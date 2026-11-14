"""Evidence ingestion for request/response logs, metrics, error text and API docs."""
from __future__ import annotations
import csv, io, json, re
from pathlib import Path
from typing import Any, Iterable
from bs4 import BeautifulSoup
from pypdf import PdfReader
import pdfplumber
from .redaction import redact_structure, redact_text
from .normalization import normalize_endpoint, parse_datetime

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_LOG_EXT = {".json", ".jsonl", ".ndjson", ".csv"}
ALLOWED_DOC_EXT = {".pdf", ".html", ".htm", ".md", ".markdown", ".txt"}

def _decode(raw: bytes) -> str:
    return raw.decode("utf-8-sig", errors="replace")

def parse_structured_file(filename: str, raw: bytes) -> list[dict]:
    ext=Path(filename).suffix.lower()
    if len(raw)>MAX_UPLOAD_BYTES:
        raise ValueError(f"{filename} exceeds the 20 MB upload limit")
    if ext==".csv":
        return [redact_structure(dict(row)) for row in csv.DictReader(io.StringIO(_decode(raw))) if any((v or "").strip() for v in row.values())]
    if ext in {".jsonl", ".ndjson"}:
        rows=[]
        for line_no,line in enumerate(_decode(raw).splitlines(),1):
            if not line.strip(): continue
            try: item=json.loads(line)
            except json.JSONDecodeError as exc: raise ValueError(f"Invalid JSONL at line {line_no}: {exc}") from exc
            rows.extend(_records_from_json(item))
        return [redact_structure(x) for x in rows]
    if ext==".json":
        try: data=json.loads(_decode(raw))
        except json.JSONDecodeError as exc: raise ValueError(f"Invalid JSON: {exc}") from exc
        return [redact_structure(x) for x in _records_from_json(data)]
    raise ValueError(f"Unsupported structured evidence type: {ext}")

def _records_from_json(data: Any) -> list[dict]:
    if isinstance(data,list): return [x for x in data if isinstance(x,dict)]
    if not isinstance(data,dict): return []
    for key in ("records","logs","requests","responses","metrics","events"):
        value=data.get(key)
        if isinstance(value,list):
            return [x for x in value if isinstance(x,dict)]
    return [data]

def _canonical_log(row: dict) -> dict:
    row=dict(row)
    request=row.get("request") if isinstance(row.get("request"),dict) else {}
    response=row.get("response") if isinstance(row.get("response"),dict) else {}
    # Merge only metadata; keep body objects for field-name/size analysis, then redact.
    merged={**row, **request, **response}
    aliases={
        "http_method":"method", "verb":"method", "url":"endpoint", "path":"endpoint",
        "uri":"endpoint", "route":"endpoint", "status":"status_code", "http_status":"status_code",
        "response_status":"status_code", "duration_ms":"latency_ms", "response_time_ms":"latency_ms",
        "elapsed_ms":"latency_ms", "request_id":"correlation_id", "trace_id":"correlation_id",
        "error":"error_message", "message":"error_message", "time":"timestamp", "ts":"timestamp",
    }
    for old,new in aliases.items():
        if new not in merged and old in merged: merged[new]=merged[old]
    event_type=str(row.get("event_type") or row.get("type") or "").lower()
    generic_headers=row.get("headers") or {}
    request_header_value=merged.get("request_headers") or request.get("headers") or (generic_headers if event_type!="response" else {}) or {}
    response_header_value=merged.get("response_headers") or response.get("headers") or (generic_headers if event_type=="response" else {}) or {}
    merged["request_headers"] = request_header_value
    merged["response_headers"] = response_header_value
    merged["request_payload"] = merged.get("request_payload", request.get("body", row.get("request_body")))
    merged["response_payload"] = merged.get("response_payload", response.get("body", row.get("response_body")))
    merged["endpoint"] = normalize_endpoint(str(merged.get("endpoint") or "/"))
    return redact_structure(merged)

def parse_log_uploads(files: Iterable[tuple[str,bytes]]) -> list[dict]:
    rows=[]
    for name,raw in files:
        for row in parse_structured_file(name,raw):
            row.setdefault("source_file", name)
            rows.append(_canonical_log(row))
    # Join request-only and response-only events by correlation identifier when feasible.
    grouped={}; standalone=[]
    for row in rows:
        cid=str(row.get("correlation_id") or row.get("request_id") or "")
        if cid and (str(row.get("event_type") or row.get("type") or "").lower() in {"request","response"} or (not row.get("status_code") and row.get("method"))):
            bucket=grouped.setdefault(cid,{})
            is_response=str(row.get("event_type") or row.get("type") or "").lower()=="response"
            if is_response:
                for key,value in row.items():
                    if key!="request_headers": bucket[key]=value
                if row.get("response_headers"): bucket["response_headers"]=row["response_headers"]
            else:
                bucket.update(row)
        else: standalone.append(row)
    standalone.extend(_canonical_log(v) for v in grouped.values())
    return [r for r in standalone if r.get("method") or r.get("status_code") or r.get("error_message")]

def parse_metric_uploads(files: Iterable[tuple[str,bytes]]) -> list[dict]:
    rows=[]
    for name,raw in files:
        for row in parse_structured_file(name,raw):
            row.setdefault("source_file", name)
            rows.append(row)
    out=[]
    for r in rows:
        item=dict(r)
        aliases={"path":"endpoint","url":"endpoint","time":"timestamp","p95":"p95_latency_ms","latency_p95_ms":"p95_latency_ms","error_rate":"error_rate_pct","rps":"request_rate_rps","dependency_errors":"dependency_error_rate_pct"}
        for old,new in aliases.items():
            if new not in item and old in item: item[new]=item[old]
        item["endpoint"]=normalize_endpoint(str(item.get("endpoint") or "/"))
        item.setdefault("source_file", "uploaded metrics")
        out.append(redact_structure(item))
    return out

def parse_error_uploads(files: Iterable[tuple[str,bytes]]) -> str:
    texts=[]
    for name,raw in files:
        if len(raw)>MAX_UPLOAD_BYTES: raise ValueError(f"{name} exceeds the 20 MB upload limit")
        ext=Path(name).suffix.lower()
        if ext in {".json", ".jsonl", ".ndjson", ".csv"}:
            try: content=json.dumps(parse_structured_file(name,raw), ensure_ascii=False)
            except Exception: content=_decode(raw)
        else: content=_decode(raw)
        texts.append(f"[{name}]\n{redact_text(content)}")
    return "\n\n".join(texts)

def _metadata_from_text(text: str, filename: str) -> dict:
    patterns={
        "version":r"(?im)^\s*(?:api\s+)?version\s*[:#]\s*([^\r\n]+)",
        "effective_date":r"(?im)^\s*effective\s+date\s*[:#]\s*([^\r\n]+)",
        "document_owner":r"(?im)^\s*(?:document\s+)?owner\s*[:#]\s*([^\r\n]+)",
        "status":r"(?im)^\s*(?:status|approval\s+status)\s*[:#]\s*([^\r\n]+)",
        "supersedes":r"(?im)^\s*supersedes\s*[:#]\s*([^\r\n]+)",
        "product":r"(?im)^\s*product\s*[:#]\s*([^\r\n]+)",
        "environment":r"(?im)^\s*environment\s*[:#]\s*([^\r\n]+)",
    }
    result={"source":filename,"title":Path(filename).stem.replace("_"," ").replace("-"," ").title()}
    for key,pattern in patterns.items():
        m=re.search(pattern,text)
        if m: result[key]=m.group(1).strip()[:200]
    first=re.search(r"(?m)^#\s+(.+)$",text)
    if first: result["title"]=first.group(1).strip()
    return result

def _sections(text: str) -> list[tuple[str,str]]:
    lines=text.splitlines(); sections=[]; title="Overview"; buff=[]
    for line in lines:
        m=re.match(r"^\s*(#{1,6})\s+(.+?)\s*$",line)
        if m:
            if "\n".join(buff).strip(): sections.append((title,"\n".join(buff).strip()))
            title=m.group(2).strip(); buff=[]
        else: buff.append(line)
    if "\n".join(buff).strip(): sections.append((title,"\n".join(buff).strip()))
    if not sections and text.strip(): sections=[("Overview",text.strip())]
    return sections

def _extract_pdf(raw: bytes) -> list[tuple[int,str]]:
    pages=[]
    try:
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            for i,page in enumerate(pdf.pages,1):
                text=page.extract_text() or ""
                table_text=[]
                for table in page.extract_tables() or []:
                    for row in table:
                        cells=[str(c or "").strip() for c in row]
                        if any(cells): table_text.append(" | ".join(cells))
                combined=text + (("\n\nExtracted table:\n"+"\n".join(table_text)) if table_text else "")
                if combined.strip(): pages.append((i,combined))
    except Exception:
        reader=PdfReader(io.BytesIO(raw))
        for i,page in enumerate(reader.pages,1):
            text=page.extract_text() or ""
            if text.strip(): pages.append((i,text))
    return pages

def parse_document_upload(filename: str, raw: bytes) -> dict:
    if len(raw)>MAX_UPLOAD_BYTES: raise ValueError(f"{filename} exceeds the 20 MB upload limit")
    ext=Path(filename).suffix.lower(); pages=[]
    if ext==".pdf": pages=_extract_pdf(raw)
    elif ext in {".html",".htm"}:
        soup=BeautifulSoup(_decode(raw),"html.parser")
        for tag in soup(["script","style","noscript"]): tag.decompose()
        # Preserve HTML tables in row-oriented form, including headers.
        table_lines=[]
        for table in soup.find_all("table"):
            for tr in table.find_all("tr"):
                cells=[c.get_text(" ",strip=True) for c in tr.find_all(["th","td"])]
                if cells: table_lines.append(" | ".join(cells))
        text=soup.get_text("\n",strip=True)
        if table_lines: text += "\n\nExtracted tables:\n"+"\n".join(table_lines)
        pages=[(None,text)]
    elif ext in {".md",".markdown",".txt"}:
        pages=[(None,_decode(raw))]
    else: raise ValueError(f"Unsupported document type: {ext}")
    full="\n\n".join(text for _,text in pages)
    metadata=_metadata_from_text(full,filename)
    chunks=[]
    for page_no,page_text in pages:
        for section,body in _sections(page_text):
            # Paragraph-preserving chunks with an upper character bound.
            paras=[p.strip() for p in re.split(r"\n\s*\n",body) if p.strip()]
            current=""
            for para in paras:
                if len(current)+len(para)>1800 and current:
                    chunks.append({"text":redact_text(current),"source":filename,"title":metadata["title"],"section":section,"page":page_no,"metadata":metadata})
                    current=para
                else: current=(current+"\n\n"+para).strip()
            if current.strip(): chunks.append({"text":redact_text(current),"source":filename,"title":metadata["title"],"section":section,"page":page_no,"metadata":metadata})
    return {"metadata":metadata,"chunks":chunks,"pages":len(pages),"text_length":len(full)}

def parse_document_uploads(files: Iterable[tuple[str,bytes]]) -> list[dict]:
    documents=[]
    for name,raw in files: documents.append(parse_document_upload(name,raw))
    return documents

def load_local_documents(directory: str | Path) -> list[dict]:
    docs=[]; directory=Path(directory)
    if not directory.exists(): return docs
    for path in sorted(directory.iterdir()):
        if path.is_file() and path.suffix.lower() in ALLOWED_DOC_EXT:
            docs.append(parse_document_upload(path.name,path.read_bytes()))
    return docs
