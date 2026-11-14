# Deployment quick reference

## Streamlit Community Cloud
1. Push source to GitHub (exclude `.env`, `.venv`, secrets and databases).
2. Create app from repository; main file `streamlit_app.py`.
3. Add in App Settings → Secrets:

```toml
GROQ_API_KEY = "gsk_..."
GROQ_MODEL = "openai/gpt-oss-20b"
```

4. Redeploy/reboot. The key is optional because deterministic classification and ranking operate without Groq.

## Render / Docker
`Dockerfile` listens on `$PORT` (default 8501). `render.yaml` creates one Streamlit web service. Configure `GROQ_API_KEY` as a secret in the service environment. For persistent reviewer feedback, attach a persistent disk and set `FEEDBACK_DB_PATH` to a path on that disk.
