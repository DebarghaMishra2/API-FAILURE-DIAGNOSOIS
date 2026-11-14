# Automated test results

Validation run for the packaged project:

- Python compilation: passed (`python -m compileall -q app scripts tests streamlit_app.py`).
- Unit tests: **22 passed, 0 failed** (`python -m unittest discover -s tests -v`).
- Synthetic scenario evaluation: **8 scenarios**; 100% deterministic classification accuracy and expected diagnosis in top 1 across this included synthetic set; 87.5% metric correlation because the intentionally incomplete case has no metrics.
- Synthetic documents parsed: 6 documents across PDF, HTML, Markdown and TXT; 13 section chunks on this local validation run.
- No live Groq API request was made during package validation. Groq narrative generation is optional and must be tested with the user's own key.
- Streamlit UI was syntax-compiled but not launched inside the packaging environment because Streamlit was not installed in that environment. Install `requirements.txt` and launch locally to verify the UI in your environment.

These checks establish internal functional smoke coverage only, not production reliability or accuracy on real HCLTech data.
