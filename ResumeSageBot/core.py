"""
ResumeSage AI — the engine.

    1. Take a raw, messy resume (pasted text or a .txt/.pdf file).
    2. Extract structured, validated information from it.
    3. Optionally score it against a job description.
    4. Return real Python objects, never raw model text.

Both the CLI below and the Streamlit UI import from this module, so the
prompts live in exactly one place.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_mistralai import ChatMistralAI

try:  # works both as `python -m ResumeSageBot.core` and as a plain script
    from .schema import JobFit, Resume
except ImportError:  # pragma: no cover
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from ResumeSageBot.schema import JobFit, Resume

load_dotenv()

MODEL_NAME = "mistral-small-2603"


# ── Model ──────────────────────────────────────────────────────────────────────

def get_model(temperature: float = 0.1) -> ChatMistralAI:
    """A low-temperature model — extraction should be boring and repeatable."""
    return ChatMistralAI(model=MODEL_NAME, temperature=temperature)


# ── Parsers ────────────────────────────────────────────────────────────────────

resume_parser = PydanticOutputParser(pydantic_object=Resume)
fit_parser = PydanticOutputParser(pydantic_object=JobFit)


# ── Prompts ────────────────────────────────────────────────────────────────────

EXTRACT_SYSTEM = """
You are ResumeSage AI, an expert technical recruiter and resume parser.

Your responsibilities:

1. Read the entire resume carefully, including badly formatted or run-on text.
2. Extract every piece of candidate information you can find.
3. Write a fresh 2-3 sentence summary of the candidate in your own words.
4. Separate technical skills from soft skills.
5. Group work history, education, and projects into their own structured lists.
6. Estimate total years of experience and a seniority level from the dates given.
7. Name genuine strengths and the gaps a recruiter would actually flag.
8. Extract facts ONLY from the provided text.
9. If a field is not present in the resume, return null. Never guess a name,
   an email, a company, or a date that is not written there.
10. Never invent skills, employers, degrees, or achievements.
11. Return ONLY valid JSON. No markdown, no code fences, no commentary.

Follow this schema exactly:
{format_instructions}
"""

extract_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", EXTRACT_SYSTEM),
        (
            "human",
            "Parse the following resume and extract all relevant information.\n\n"
            "Resume:\n{resume_text}",
        ),
    ]
)

FIT_SYSTEM = """
You are ResumeSage AI, an expert technical recruiter scoring a candidate
against one specific job opening.

Your responsibilities:

1. Read the job description and identify what it genuinely requires.
2. Check each requirement against real evidence in the resume.
3. For every required skill, say whether it is present and quote where it
   appeared. If it is absent, mark it absent — do not be generous.
4. List the missing skills honestly, and separately list transferable skills
   that only partially cover a gap.
5. Judge whether the candidate's experience level clears the bar.
6. Give an overall match_score from 0 to 100 that a hiring manager would agree
   with. Be strict: 90+ means they could be hired today.
7. Suggest concrete resume edits that would raise the score.
8. Write interview questions that probe the weakest areas.
9. Base every judgement on the two texts provided. Never invent experience.
10. Return ONLY valid JSON. No markdown, no code fences, no commentary.

Follow this schema exactly:
{format_instructions}
"""

fit_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", FIT_SYSTEM),
        (
            "human",
            "Score this candidate against the job opening.\n\n"
            "=== JOB DESCRIPTION ===\n{job_description}\n\n"
            "=== RESUME ===\n{resume_text}",
        ),
    ]
)


# ── Helpers ────────────────────────────────────────────────────────────────────

_FENCE_OPEN = re.compile(r"^```(?:json)?\s*")
_FENCE_CLOSE = re.compile(r"\s*```$")


def strip_fences(text: str) -> str:
    """Models wrap JSON in ``` fences even when told not to. Undo that."""
    cleaned = _FENCE_OPEN.sub("", text.strip())
    return _FENCE_CLOSE.sub("", cleaned).strip()


def read_resume_file(path: str) -> str:
    """Read a resume from a .txt/.md file, or a .pdf if pypdf is installed."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No such file: {p}")

    if p.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(p))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    return p.read_text(encoding="utf-8", errors="ignore")


# ── Public API ─────────────────────────────────────────────────────────────────

def extract_resume(resume_text: str, model: ChatMistralAI | None = None) -> Resume:
    """Messy resume text in, validated `Resume` object out."""
    if not resume_text.strip():
        raise ValueError("Resume text is empty.")

    model = model or get_model()
    final_prompt = extract_prompt.invoke(
        {
            "resume_text": resume_text,
            "format_instructions": resume_parser.get_format_instructions(),
        }
    )
    response = model.invoke(final_prompt)
    return resume_parser.parse(strip_fences(response.content))


def score_fit(
    resume_text: str,
    job_description: str,
    model: ChatMistralAI | None = None,
) -> JobFit:
    """Score one resume against one job description."""
    if not resume_text.strip():
        raise ValueError("Resume text is empty.")
    if not job_description.strip():
        raise ValueError("Job description is empty.")

    model = model or get_model()
    final_prompt = fit_prompt.invoke(
        {
            "resume_text": resume_text,
            "job_description": job_description,
            "format_instructions": fit_parser.get_format_instructions(),
        }
    )
    response = model.invoke(final_prompt)
    return fit_parser.parse(strip_fences(response.content))


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        prog="resumesage",
        description="Turn a messy resume into validated JSON, and optionally "
        "score it against a job description.",
    )
    ap.add_argument("-f", "--file", help="Path to a resume (.txt, .md, or .pdf)")
    ap.add_argument("-j", "--job", help="Path to a job description text file")
    ap.add_argument("-o", "--out", help="Write the JSON here instead of stdout")
    args = ap.parse_args()

    if args.file:
        resume_text = read_resume_file(args.file)
    elif not sys.stdin.isatty():
        resume_text = sys.stdin.read()
    else:
        print("Paste the resume, then press Ctrl-D:\n", file=sys.stderr)
        resume_text = sys.stdin.read()

    resume = extract_resume(resume_text)
    payload = {"resume": resume.model_dump()}

    if args.job:
        job_text = read_resume_file(args.job)
        payload["job_fit"] = score_fit(resume_text, job_text).model_dump()

    rendered = json.dumps(payload, indent=2, ensure_ascii=False)

    if args.out:
        Path(args.out).write_text(rendered, encoding="utf-8")
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        print(rendered)


if __name__ == "__main__":
    main()

# Resume -> AI -> validated JSON -> Backend -> API -> Frontend
