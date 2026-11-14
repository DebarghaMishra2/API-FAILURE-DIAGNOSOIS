"""Hybrid API-document retrieval using in-project BM25 plus TF-IDF similarity."""
from __future__ import annotations
import math, re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def tokenize(text): return re.findall(r"[a-z0-9_./-]+",str(text).lower())

class BM25Index:
    """Small-corpus BM25 implementation (Okapi BM25) without an external index service."""
    def __init__(self, documents, k1=1.5, b=0.75):
        self.docs=[tokenize(x) for x in documents]
        self.k1=k1; self.b=b
        self.lengths=[len(x) for x in self.docs]
        self.avgdl=(sum(self.lengths)/len(self.lengths)) if self.lengths else 0.0
        self.term_freq=[Counter(x) for x in self.docs]
        df=Counter()
        for doc in self.docs: df.update(set(doc))
        n=len(self.docs)
        self.idf={term:math.log(1+(n-freq+0.5)/(freq+0.5)) for term,freq in df.items()}
    def get_scores(self, query_tokens):
        scores=[]
        for tf,dl in zip(self.term_freq,self.lengths):
            score=0.0
            for term in query_tokens:
                freq=tf.get(term,0)
                if not freq: continue
                denom=freq+self.k1*(1-self.b+self.b*(dl/(self.avgdl or 1)))
                score+=self.idf.get(term,0.0)*(freq*(self.k1+1)/denom)
            scores.append(score)
        return scores

class DocumentationRetriever:
    def __init__(self, chunks=None):
        self.chunks=list(chunks or []); self.bm25=None; self.vectorizer=None; self.matrix=None
        self.build(self.chunks)
    def build(self,chunks):
        self.chunks=list(chunks or [])
        corpus=[str(x.get("text", "")) for x in self.chunks]
        if corpus:
            self.bm25=BM25Index(corpus)
            self.vectorizer=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,lowercase=True,strip_accents="unicode")
            try: self.matrix=self.vectorizer.fit_transform(corpus)
            except ValueError: self.matrix=None
        else: self.bm25=self.vectorizer=self.matrix=None
    def search(self,query,top_k=5):
        if not self.chunks: return []
        tokens=tokenize(query)
        bm=self.bm25.get_scores(tokens) if self.bm25 else [0.0]*len(self.chunks)
        if self.matrix is not None:
            q=self.vectorizer.transform([query]); tf=cosine_similarity(q,self.matrix).ravel()
        else: tf=[0.0]*len(self.chunks)
        def norm(values):
            hi=max(values) if len(values) else 0; lo=min(values) if len(values) else 0
            if hi==lo: return [0.0 for _ in values]
            return [(x-lo)/(hi-lo) for x in values]
        bn,tn=norm(list(bm)),norm(list(tf))
        ranked=[]
        for i,chunk in enumerate(self.chunks):
            score=0.45*bn[i]+0.55*tn[i]
            ranked.append({**chunk,"retrieval_score":round(float(score),4),"bm25_score":round(float(bm[i]),4),"tfidf_score":round(float(tf[i]),4)})
        ranked.sort(key=lambda x:x["retrieval_score"],reverse=True)
        return ranked[:max(1,int(top_k))]
