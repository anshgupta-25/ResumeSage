<div align="center">

# 📄 ResumeSage AI

**Turn a messy resume into validated JSON — then score it honestly against any job description.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?logo=langchain&logoColor=white)](https://langchain.com)
[![Mistral](https://img.shields.io/badge/Mistral-small--2603-FF7000?logo=mistralai&logoColor=white)](https://mistral.ai)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)

<sub>Built by <a href="https://github.com/anshgupta-25">Ansh Gupta</a></sub>

</div>

---

## What it does

Resumes arrive as unstructured prose. Hiring systems need structured data.
ResumeSage sits in that gap.

**Parse** — paste or upload a resume and get back a validated object: contact
details, split technical/soft skills, a work-history timeline, education,
projects, an estimated seniority level, and an honest read on strengths and gaps.

**Job Fit** — add a job description and get a 0–100 match score, a per-skill
evidence trail showing *where* in the resume each requirement was actually met,
the skills that are genuinely missing, concrete resume edits that would raise
the score, and the interview questions a recruiter would use to probe the gaps.

The model never returns loose text. Every response is validated against a
Pydantic schema, so a hallucinated field or a wrong type fails loudly instead
of quietly reaching the UI.

---

## 🚀 Quick start

```bash
# 1. Isolated environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Dependencies
pip install -r requirements.txt

# 3. API key
cp .env.example .env               # then open .env and paste your Mistral key
```

> **macOS note:** Homebrew's Python is "externally managed" (PEP 668), so a bare
> `pip install` is refused. The virtual environment above is required, not optional.

Get a free key at [console.mistral.ai/api-keys](https://console.mistral.ai/api-keys).
Mistral is the **only** key this project needs.

---

## 🎮 Running it

### Streamlit app

```bash
streamlit run ResumeSageBot/app.py
```

Two tabs: **Parse Resume** and **Job Fit Score**. Paste text directly or upload
a `.txt`, `.md`, or `.pdf`.

### Command line

```bash
# Parse a resume to JSON on stdout
python -m ResumeSageBot.core -f samples/sample_resume.txt

# Parse *and* score against a job description
python -m ResumeSageBot.core -f samples/sample_resume.txt -j samples/sample_job.txt

# Write the result to a file
python -m ResumeSageBot.core -f samples/sample_resume.txt -o out.json

# Or pipe it in
cat samples/sample_resume.txt | python -m ResumeSageBot.core
```

Try the bundled samples first — `sample_resume.txt` is a 3-year backend
developer, `sample_job.txt` asks for 5+ years plus Kubernetes and Kafka. The
score should land in the middle, with the missing skills named precisely.

---

## 🧱 How it is built

| File | Responsibility |
|---|---|
| **[`schema.py`](ResumeSageBot/schema.py)** | Pydantic models — the contract the LLM must satisfy |
| **[`core.py`](ResumeSageBot/core.py)** | Prompts, model calls, parsing, and the CLI |
| **[`app.py`](ResumeSageBot/app.py)** | Streamlit UI — presentation only, no prompts |

### The pipeline

```
resume text
    │
    ├─▶ ChatPromptTemplate ──▶ ChatMistralAI ──▶ raw text
    │                                               │
    │                                       strip code fences
    │                                               │
    └──────────────────────────▶ PydanticOutputParser ──▶ Resume / JobFit
                                                                │
                                                          Streamlit UI
```

### Design decisions worth noting

**Nested schemas, not flat ones.** `Experience`, `Education`, `Project`, and
`SkillMatch` are their own models. A job is an object with a company, a role,
a duration, and highlights — not four parallel lists that have to be zipped
back together downstream.

**Prompts live in exactly one place.** `app.py` imports from `core.py` rather
than keeping its own copy of the system prompt. There is no way for the UI and
the CLI to drift apart.

**`temperature=0.1`.** Extraction should be boring and repeatable. The same
resume should parse the same way twice.

**Everything is `Optional`, and missing means `null`.** The prompt is explicit
that absent information returns null and that names, dates, and employers must
never be invented. A resume with no phone number should produce `null`, not a
plausible-looking fabrication.

**Evidence, not just a verdict.** The job-fit scorer has to quote where in the
resume each matched skill appeared. A score you cannot audit is not worth much,
and requiring evidence makes the model far less willing to award credit for a
skill that is not really there.

---

## 🔒 A note on privacy

Resumes are personal data. `.gitignore` excludes a `resumes/` directory, so
that is the safe place to keep real ones while you work. The files in
`samples/` are fictional. Nothing is written to disk unless you pass `-o`, but
resume text is sent to Mistral's API for processing — do not paste anyone's
resume you do not have permission to.

---

## 📋 Requirements

Python 3.11 or newer, and a Mistral API key. Full dependency list in
[`requirements.txt`](requirements.txt).
