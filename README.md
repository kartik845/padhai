# 📚 PadhAI — Padho Smart, Pucho Kuch Bhi

Ek AI Notes Q&A Bot. Apni notes ki PDF upload karo, fir chat mein kuch bhi pucho.
AI sirf tumhari notes ke basis pe Hinglish mein jawab deta hai, source (file + page) ke saath.

## Features
- Multiple PDF upload, har page ka tag (file + page number)
- Chat with memory (follow-up sawal chalte hain)
- Quick actions: Summary, 10 Important Questions, 5 MCQ Quiz
- Exam Mode: short, crisp, exam-ready jawab
- Jawab .txt mein download
- Notes mein na ho to "Ye notes mein nahi mila" (hallucination control)
- Dark glassmorphism UI

## Tech Stack
Python, Streamlit, pypdf, Google Gemini API (google-genai), Streamlit Community Cloud

## Local run
```
python -m venv venv
venv\Scripts\activate          # Windows  (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
```
`.streamlit/secrets.toml.example` ko copy karke `.streamlit/secrets.toml` banao aur apni key daalo (aistudio.google.com se free).
```
streamlit run app.py
```

## Deploy (free)
1. Code GitHub pe daalo (secrets.toml nahi)
2. share.streamlit.io -> New app -> repo + app.py select karo
3. Advanced settings -> Secrets mein `GEMINI_API_KEY = "..."` paste karo -> Deploy

## Limitations / Future scope
- Scanned (image) PDF ke liye OCR chahiye
- Bahut bade notes (1000+ pages) ke liye RAG + vector DB
- Voice input/output, user login, quiz score tracking
