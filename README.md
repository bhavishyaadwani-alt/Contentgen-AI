# Contentgen – Streamlit Edition

This is the Streamlit version of the Contentgen AI Content Generator. It includes account registration/login, password hashing, content generation through OpenRouter, and downloading generated text.

## Run locally (Windows PowerShell)

1. Open this folder in VS Code.
2. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
3. Set your OpenRouter key in the current terminal (do not share or commit it):
   ```powershell
   $env:OPENROUTER_API_KEY="YOUR_OPENROUTER_API_KEY"
   ```
4. Start Streamlit:
   ```powershell
   python -m streamlit run streamlit_app.py
   ```
5. Open the local URL shown by Streamlit, usually `http://localhost:8501`.

## Deploy so it works on other laptops

Deploy on Streamlit Community Cloud:

1. Create a GitHub repository and upload `streamlit_app.py`, `requirements.txt`, and `README.md` (and `.streamlit/config.toml` if desired).
2. Go to https://share.streamlit.io/ and sign in with GitHub.
3. Choose **Create app**, select your repository and branch, and set the main file path to `streamlit_app.py`.
4. In the app's **Advanced settings / Secrets**, add:
   ```toml
   OPENROUTER_API_KEY = "YOUR_OPENROUTER_API_KEY"
   ```
5. Deploy. Streamlit will provide a public `https://...streamlit.app` URL that can be opened from other laptops without keeping your own laptop running.

Never upload your API key, database file, or private secrets to GitHub.

## Database note

This demo uses SQLite (`contentgen.db`) for user accounts. On Streamlit Community Cloud, the local filesystem is not guaranteed to be permanent across app rebuilds/restarts. For a long-running production app where accounts must persist reliably, connect a hosted database such as Supabase/PostgreSQL and store its credentials in Streamlit Secrets.
