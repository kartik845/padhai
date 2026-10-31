"""
PadhAI - AI Notes Q&A Bot
Padho Smart, Pucho Kuch Bhi

Flow: PDF upload -> pypdf se text -> text + sawal Gemini ko -> Hinglish jawab + source
"""

import html
import io
import re

import streamlit as st
from google import genai
from pypdf import PdfReader

# ---------------------------------------------------------------
# Settings (yahan se aasani se badal sakte ho)
# ---------------------------------------------------------------
MODEL = "gemini-2.5-flash"            # Model badalna ho to sirf yahan
FALLBACK_MODELS = ["gemini-2.0-flash"]  # Upar wala na mile to ye try hoga
MAX_CHARS = 400_000                   # Notes ki max length prompt mein
HISTORY_MESSAGES = 6                  # Pichle kitne messages yaad rakhne hain

st.set_page_config(page_title="PadhAI", page_icon="📚", layout="wide")

# ---------------------------------------------------------------
# Design (CSS)
# ---------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap');

html, body, [class*="css"], .stMarkdown, .stChatInput textarea {
  font-family: 'Poppins', sans-serif;
}

/* Background: deep navy + 3 soft glows */
.stApp {
  background:
    radial-gradient(circle at 12% 8%, rgba(139,92,246,.28) 0, transparent 38%),
    radial-gradient(circle at 88% 20%, rgba(56,189,248,.20) 0, transparent 36%),
    radial-gradient(circle at 50% 100%, rgba(52,211,153,.16) 0, transparent 40%),
    #0b1020;
}

/* Streamlit chrome hatao (header transparent, taaki sidebar button dikhe) */
#MainMenu, footer, [data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }

.block-container { padding-top: 2rem; max-width: 900px; }

/* Brand */
.brand {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  font-size: clamp(2.4rem, 6vw, 3.6rem);
  line-height: 1.05;
  margin: 0;
  background: linear-gradient(90deg, #a78bfa, #38bdf8 55%, #34d399);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.tagline { color: #9aa3c7; margin: .35rem 0 1.4rem; font-size: 1.02rem; }

/* Glass card */
.glass {
  background: rgba(255,255,255,.05);
  border: 1px solid rgba(255,255,255,.09);
  border-radius: 18px;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  padding: 22px 24px;
}

/* Welcome (empty state) */
.welcome h3 {
  font-family: 'Space Grotesk', sans-serif;
  margin: 0 0 14px; color: #e6e9f5; font-size: 1.35rem;
}
.step { display: flex; gap: 14px; align-items: center; padding: 10px 0; color: #cfd5ee; }
.step .n {
  flex: 0 0 34px; height: 34px; border-radius: 50%;
  display: grid; place-items: center; font-weight: 600; color: #fff;
  background: linear-gradient(135deg, #8b5cf6, #38bdf8);
}
.dropzone {
  margin-top: 16px; padding: 18px; text-align: center; color: #b9a8ff;
  border: 2px dashed rgba(139,92,246,.6); border-radius: 14px;
  box-shadow: 0 0 28px rgba(139,92,246,.22), inset 0 0 22px rgba(139,92,246,.10);
}

/* Sidebar */
[data-testid="stSidebar"] {
  background: rgba(255,255,255,.035);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-right: 1px solid rgba(255,255,255,.08);
}
.sb-title { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.15rem; color: #e6e9f5; }
.filechip {
  display: flex; align-items: center; gap: 8px; margin: 6px 0; padding: 8px 12px;
  background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.08);
  border-radius: 10px; color: #dfe4f7; font-size: .85rem; word-break: break-all;
}
.filechip small { color: #8e97bd; margin-left: auto; white-space: nowrap; }

/* Chat bubbles */
[data-testid="stChatMessage"] {
  background: rgba(255,255,255,.05);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 18px;
  padding: 14px 16px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background: linear-gradient(135deg, rgba(139,92,246,.55), rgba(56,189,248,.45));
  border-color: rgba(255,255,255,.18);
}

/* Naya message aaye to halka fade-in (sirf yahi ek animation) */
@keyframes pop { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
[data-testid="stChatMessage"]:last-of-type { animation: pop .35s ease-out; }

/* Source chips */
.chips { margin-top: 10px; display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  font-size: .75rem; padding: 3px 10px; border-radius: 999px;
  color: #7ff0cd; background: rgba(52,211,153,.12);
  border: 1px solid rgba(52,211,153,.35);
}

/* Buttons */
.stButton > button, .stDownloadButton > button {
  background: linear-gradient(135deg, #8b5cf6, #38bdf8);
  color: #fff; border: 0; border-radius: 12px; padding: .55rem 1rem;
  font-weight: 500; transition: transform .2s, box-shadow .2s;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 26px rgba(139,92,246,.5);
  color: #fff;
}
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible {
  outline: 2px solid #34d399; outline-offset: 2px;
}

/* Upload box */
[data-testid="stFileUploaderDropzone"] {
  background: rgba(139,92,246,.07);
  border: 2px dashed rgba(139,92,246,.55);
  border-radius: 14px;
}
[data-testid="stFileUploaderDropzone"]:hover { box-shadow: 0 0 24px rgba(139,92,246,.35); }

/* Chat input */
[data-testid="stChatInput"] { border-radius: 16px; }

/* Mobile */
@media (max-width: 640px) {
  .block-container { padding: 1rem .8rem 5rem; }
  .glass { padding: 16px; }
}
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------
# Gemini client
# ---------------------------------------------------------------
@st.cache_resource
def get_client():
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


try:
    client = get_client()
except Exception:
    st.error(
        "Gemini API key nahi mili. `.streamlit/secrets.toml` (local) ya "
        "Streamlit Cloud ke Secrets mein `GEMINI_API_KEY = \"...\"` daalo."
    )
    st.stop()


# ---------------------------------------------------------------
# PDF reading (cache hota hai, har sawal pe dobara nahi padhta)
# ---------------------------------------------------------------
@st.cache_data(show_spinner=False)
def read_pdf(file_bytes: bytes, name: str):
    """PDF ke har page ka text nikalta hai aur [File | Page N] tag lagata hai."""
    reader = PdfReader(io.BytesIO(file_bytes))
    parts, pages_with_text = [], 0
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages_with_text += 1
            parts.append(f"[File: {name} | Page {i}]\n{text}")
    return "\n\n".join(parts), len(reader.pages), pages_with_text


# ---------------------------------------------------------------
# Gemini call + friendly errors
# ---------------------------------------------------------------
def ask_gemini(prompt: str) -> str:
    last_err = None
    for model in [MODEL] + FALLBACK_MODELS:
        try:
            res = client.models.generate_content(model=model, contents=prompt)
            return res.text or "Jawab khali aaya, dobara try karo."
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
            # Model na mile to agla model try karo, warna ruk jao
            if "404" in last_err or "not found" in last_err.lower():
                continue
            break
    low = (last_err or "").lower()
    if "429" in low or "quota" in low or "resource_exhausted" in low:
        return "⏳ Free limit abhi khatam ho gayi. 1 minute ruk ke dobara try karo."
    if "api key" in low or "api_key" in low or "permission" in low or "403" in low:
        return "🔑 API key galat ya band hai. AI Studio se nayi key banao aur Secrets mein daalo."
    if "404" in low or "not found" in low:
        return "🤖 Model nahi mila. app.py mein MODEL ka naam current Gemini Flash model se badlo."
    return f"⚠️ Kuch gadbad hui: {last_err}"


def build_prompt(notes: str, history: list, question: str, exam_mode: bool) -> str:
    hist = "\n".join(
        f"{'Student' if role == 'user' else 'Tutor'}: {msg}"
        for role, msg in history[-HISTORY_MESSAGES:]
    )
    style = (
        "EXAM MODE ON: Jawab sirf short, crisp, exam-ready bullet points mein do (max 6 points). "
        "Definitions aur keywords bold karo."
        if exam_mode
        else "Jawab simple Hinglish mein samjhake do, zaroorat ho to bullet points use karo."
    )
    return f"""Tum PadhAI ho, ek friendly college tutor.

RULES:
1. Sirf neeche diye NOTES ke basis pe jawab do. Bahar se kuch mat jodo.
2. Jawab ke end mein source likho is format mein: (Source: filename, Page 3). Agar kai pages hon: (Source: filename, Page 3, 5)
3. Agar answer notes mein nahi hai to bolo: "Ye notes mein nahi mila".
4. {style}

NOTES:
{notes[:MAX_CHARS]}

PEHLE KI BAATCHEET:
{hist or '(koi nahi)'}

STUDENT KA SAWAL: {question}"""


# ---------------------------------------------------------------
# Answer render (source ko chip bana ke dikhata hai)
# ---------------------------------------------------------------
SRC_RE = re.compile(r"\(Source:\s*([^)]+)\)", re.IGNORECASE)


def render_answer(text: str):
    sources = [s.strip() for s in SRC_RE.findall(text)]
    clean = SRC_RE.sub("", text).strip()
    st.markdown(clean)
    if sources:
        chips = "".join(f'<span class="chip">📌 {html.escape(s)}</span>' for s in sources)
        st.markdown(f'<div class="chips">{chips}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------
# Session state
# ---------------------------------------------------------------
if "chat" not in st.session_state:
    st.session_state.chat = []

# ---------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------
notes_text = ""
quick_q = None

with st.sidebar:
    st.markdown('<div class="sb-title">📂 Tumhare Notes</div>', unsafe_allow_html=True)
    files = st.file_uploader(
        "PDF upload karo", type="pdf", accept_multiple_files=True, label_visibility="collapsed"
    )

    scanned_only = False
    if files:
        for f in files:
            text, total, with_text = read_pdf(f.getvalue(), f.name)
            if text:
                notes_text += text + "\n\n"
            else:
                scanned_only = True
            st.markdown(
                f'<div class="filechip">📄 {html.escape(f.name)}<small>{total} pages</small></div>',
                unsafe_allow_html=True,
            )
        if not notes_text.strip():
            st.error("Text nahi mila. Ye scanned (image wali) PDF lagti hai. Text wali PDF use karo.")
        elif scanned_only:
            st.warning("Kuch file scanned lag rahi hai, uska text skip hua.")

    st.divider()
    st.markdown('<div class="sb-title">⚡ Quick Actions</div>', unsafe_allow_html=True)
    if st.button("📝 Summary banao", use_container_width=True):
        quick_q = "In notes ki short summary bullet points mein banao."
    if st.button("❓ 10 Important Questions", use_container_width=True):
        quick_q = "In notes se exam ke liye 10 most important questions banao."
    if st.button("🎯 5 MCQ Quiz", use_container_width=True):
        quick_q = "In notes se 5 MCQ banao, har ek ke 4 options ke saath, aur end mein sab ke answers do."

    st.divider()
    exam_mode = st.toggle("🎓 Exam Mode", help="ON karoge to jawab short aur crisp aayenge")
    if st.button("🗑️ Chat clear karo", use_container_width=True):
        st.session_state.chat = []
        st.rerun()

# ---------------------------------------------------------------
# Header + empty state
# ---------------------------------------------------------------
st.markdown('<h1 class="brand">PadhAI</h1>', unsafe_allow_html=True)
st.markdown('<div class="tagline">Padho Smart, Pucho Kuch Bhi</div>', unsafe_allow_html=True)

if not notes_text.strip() and not st.session_state.chat:
    st.markdown(
        """
<div class="glass welcome">
  <h3>Shuru kaise karein?</h3>
  <div class="step"><span class="n">1</span><span>Sidebar se apni notes ki <b>PDF upload</b> karo</span></div>
  <div class="step"><span class="n">2</span><span>Chat mein koi bhi <b>sawal pucho</b>, ya Quick Action dabao</span></div>
  <div class="step"><span class="n">3</span><span>Source ke saath jawab lo aur <b>exam mein top karo</b></span></div>
  <div class="dropzone">⬅️ Sidebar mein PDF drop karo (mobile pe upar left ka arrow dabao)</div>
</div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------
# Purani chat dikhao
# ---------------------------------------------------------------
for role, msg in st.session_state.chat:
    with st.chat_message(role, avatar="🧑‍🎓" if role == "user" else "📚"):
        if role == "user":
            st.markdown(msg)
        else:
            render_answer(msg)

# ---------------------------------------------------------------
# Naya sawal
# ---------------------------------------------------------------
typed = st.chat_input("Apna sawal likho...")
question = quick_q or typed

if question:
    if not notes_text.strip():
        st.warning("Pehle sidebar se text wali PDF upload karo 📂")
    else:
        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(question)

        with st.chat_message("assistant", avatar="📚"):
            with st.spinner("Notes padh raha hu..."):
                answer = ask_gemini(
                    build_prompt(notes_text, st.session_state.chat, question, exam_mode)
                )
            render_answer(answer)

        st.session_state.chat.append(("user", question))
        st.session_state.chat.append(("assistant", answer))

# ---------------------------------------------------------------
# Download button (last jawab)
# ---------------------------------------------------------------
last_answers = [m for r, m in st.session_state.chat if r == "assistant"]
if last_answers:
    with st.sidebar:
        st.download_button(
            "⬇️ Last jawab download (.txt)",
            data=SRC_RE.sub(lambda m: f"[Source: {m.group(1).strip()}]", last_answers[-1]),
            file_name="padhai_answer.txt",
            mime="text/plain",
            use_container_width=True,
        )
