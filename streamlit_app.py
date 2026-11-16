import os
import sqlite3
from pathlib import Path

import streamlit as st
from openai import OpenAI
from werkzeug.security import generate_password_hash, check_password_hash

APP_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DATABASE_PATH", str(APP_DIR / "contentgen.db")))
MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")

st.set_page_config(page_title="Contentgen – AI Content Generator", page_icon="✍️", layout="centered")

st.markdown("""
<style>
    /* Premium dark charcoal + purple theme */
    .stApp {
        background: radial-gradient(circle at 15% 10%, rgba(112,72,184,.24), transparent 34%),
                    radial-gradient(circle at 90% 85%, rgba(92,45,155,.20), transparent 32%),
                    linear-gradient(135deg, #090812 0%, #12101f 52%, #19122b 100%);
        color: #f4f0ff;
    }
    [data-testid="stHeader"] { background: rgba(9,8,18,.72); }
    [data-testid="stAppViewContainer"] > .main { background: transparent; }
    .block-container { max-width: 900px; padding-top: 2rem; padding-bottom: 3rem; }
    h1, h2, h3, p, label, .stMarkdown, [data-testid="stCaptionContainer"] { color: #f4f0ff !important; }
    h1 { letter-spacing: -1px; }
    .subtitle { color: #c4b6e8 !important; font-size: 1.05rem; }
    [data-testid="stTabs"] button { color: #d9cafa !important; }
    [data-testid="stTabs"] button[aria-selected="true"] { color: #ffffff !important; border-bottom-color: #a78bfa !important; }
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background: #211b32 !important; color: #ffffff !important;
        border: 1px solid #59427d !important; border-radius: 10px !important;
    }
    [data-testid="stTextInput"] input::placeholder, [data-testid="stTextArea"] textarea::placeholder { color: #b8accd !important; }
    div.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] button {
        background: linear-gradient(90deg, #7048b8, #965be8) !important;
        color: #ffffff !important; border: 0 !important; border-radius: 10px !important;
        font-weight: 600; min-height: 2.7rem;
    }
    div.stButton > button:not([kind="primary"]), [data-testid="stDownloadButton"] button {
        background: #2a2140 !important; color: #f4f0ff !important;
        border: 1px solid #684c91 !important; border-radius: 10px !important;
    }
    [data-testid="stAlert"] { background: #211b32; color: #f4f0ff; border: 1px solid #59427d; }
    hr { border-color: #443456 !important; }
    [data-testid="stForm"] { background: rgba(29,23,44,.72); padding: 1.2rem; border: 1px solid #443456; border-radius: 14px; }
</style>
""", unsafe_allow_html=True)


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")


init_db()

if "user" not in st.session_state:
    st.session_state.user = None
if "generated_content" not in st.session_state:
    st.session_state.generated_content = ""


def register_user(name, email, password):
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name.strip(), email.strip().lower(), generate_password_hash(password)),
            )
        return True, "Account created. You are now logged in."
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists. Please log in."


def login_user(email, password):
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    if user and check_password_hash(user["password_hash"], password):
        return {"id": user["id"], "name": user["name"], "email": user["email"]}
    return None


def get_api_key():
    try:
        return st.secrets.get("OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY", ""))
    except Exception:
        return os.getenv("OPENROUTER_API_KEY", "")


def generate_content(topic, content_type, tone):
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("OpenRouter API key is missing. Add OPENROUTER_API_KEY in Streamlit app Secrets.")
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    prompt = f"""Generate {content_type} content on the following topic:
Topic: {topic}
Tone: {tone}

Write clear, useful and well-structured content. Return only the generated content."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful AI content writing assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content or ""


st.title("✍️ Contentgen")
st.markdown("<p class='subtitle'>AI Content Generator — create useful content in seconds.</p>", unsafe_allow_html=True)
st.divider()

if not st.session_state.user:
    login_tab, signup_tab = st.tabs(["Login", "Create account"])
    with login_tab:
        st.subheader("Welcome back")
        with st.form("login_form"):
            login_email = st.text_input("Email address", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")
            login_submit = st.form_submit_button("Log in", type="primary", use_container_width=True)
        if login_submit:
            user = login_user(login_email, login_password)
            if user:
                st.session_state.user = user
                st.success("Logged in successfully.")
                st.rerun()
            else:
                st.error("Invalid email or password.")
    with signup_tab:
        st.subheader("Create your account")
        with st.form("signup_form"):
            signup_name = st.text_input("Full name", max_chars=80)
            signup_email = st.text_input("Email address", key="signup_email")
            signup_password = st.text_input("Password (minimum 8 characters)", type="password", key="signup_password")
            signup_confirm = st.text_input("Confirm password", type="password")
            signup_submit = st.form_submit_button("Create account", type="primary", use_container_width=True)
        if signup_submit:
            if not signup_name.strip() or not signup_email.strip() or not signup_password:
                st.error("Please fill in all fields.")
            elif "@" not in signup_email or "." not in signup_email.rsplit("@", 1)[-1]:
                st.error("Please enter a valid email address.")
            elif len(signup_password) < 8:
                st.error("Password must be at least 8 characters.")
            elif signup_password != signup_confirm:
                st.error("Passwords do not match.")
            else:
                ok, message = register_user(signup_name, signup_email, signup_password)
                if ok:
                    st.session_state.user = login_user(signup_email, signup_password)
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    st.info("Create an account or log in to access the AI content generator.")
else:
    top_left, top_right = st.columns([4, 1])
    with top_left:
        st.subheader(f"Hello, {st.session_state.user['name']}! 👋")
    with top_right:
        if st.button("Log out"):
            st.session_state.user = None
            st.session_state.generated_content = ""
            st.rerun()

    st.subheader("Generate Content")
    topic = st.text_area("Topic / Prompt", placeholder="Enter your topic or prompt...", height=130)
    col1, col2 = st.columns(2)
    with col1:
        content_type = st.selectbox("Content Type", ["Blog", "Article", "Social Media Post", "Email", "Essay", "Product Description"])
    with col2:
        tone = st.selectbox("Tone", ["Professional", "Friendly", "Creative", "Casual", "Informative"])

    if st.button("✨ Generate Content", type="primary", use_container_width=True):
        if not topic.strip():
            st.warning("Please enter a topic or prompt.")
        else:
            with st.spinner("Generating your content..."):
                try:
                    st.session_state.generated_content = generate_content(topic.strip(), content_type, tone)
                except Exception as exc:
                    st.error(f"Could not generate content: {exc}")

    if st.session_state.generated_content:
        st.subheader("Generated Content")
        st.text_area("Your result", value=st.session_state.generated_content, height=300)
        st.download_button(
            "⬇️ Download content (.txt)",
            data=st.session_state.generated_content,
            file_name="contentgen-output.txt",
            mime="text/plain",
            use_container_width=True,
        )
        st.caption("Select the text in the result box to copy it, or use the download button.")

st.divider()
st.markdown("**Features:** Login & Signup • Password hashing • AI content generation • Multiple content formats • Tone selection • Download generated content")
st.caption("Contentgen – AI Content Generator")

