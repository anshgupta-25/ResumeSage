"""
ResumeSage AI — data contracts.

Everything the model is allowed to return is described here as a Pydantic
model. The parser validates the LLM's raw text against these classes, so a
hallucinated field or a wrong type fails loudly instead of silently flowing
into the UI.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Experience(BaseModel):
    """One job the candidate has held."""

    company: Optional[str] = Field(None, description="Employer name")
    role: Optional[str] = Field(None, description="Job title held there")
    duration: Optional[str] = Field(None, description="e.g. 'Jan 2022 - Present'")
    location: Optional[str] = None
    highlights: Optional[List[str]] = Field(
        None, description="Bullet points describing what they actually did"
    )


class Education(BaseModel):
    """One degree, diploma, or course."""

    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = Field(None, description="Graduation year or range")
    score: Optional[str] = Field(None, description="CGPA or percentage, as written")


class Project(BaseModel):
    """One project the candidate built."""

    name: Optional[str] = None
    description: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    link: Optional[str] = None


class Resume(BaseModel):
    """The full structured view of a resume."""

    # -- identity -------------------------------------------------------
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    links: Optional[List[str]] = Field(
        None, description="GitHub, LinkedIn, portfolio, etc."
    )

    # -- narrative ------------------------------------------------------
    headline: Optional[str] = Field(
        None, description="One-line professional identity, e.g. 'Backend Engineer'"
    )
    summary: Optional[str] = Field(
        None, description="2-3 sentence recap of the candidate, written fresh"
    )

    # -- substance ------------------------------------------------------
    technical_skills: Optional[List[str]] = None
    soft_skills: Optional[List[str]] = None
    experience: Optional[List[Experience]] = None
    education: Optional[List[Education]] = None
    projects: Optional[List[Project]] = None
    certifications: Optional[List[str]] = None
    achievements: Optional[List[str]] = None
    languages: Optional[List[str]] = Field(
        None, description="Spoken languages, not programming languages"
    )

    # -- derived judgement ----------------------------------------------
    total_experience_years: Optional[float] = Field(
        None, description="Best estimate in years; null if it cannot be inferred"
    )
    seniority_level: Optional[str] = Field(
        None, description="Intern / Junior / Mid / Senior / Lead"
    )
    strengths: Optional[List[str]] = Field(
        None, description="What genuinely stands out about this candidate"
    )
    gaps: Optional[List[str]] = Field(
        None, description="Weak spots a recruiter would notice"
    )
    suggested_roles: Optional[List[str]] = Field(
        None, description="Job titles this candidate is a realistic fit for"
    )
    keywords: Optional[List[str]] = Field(
        None, description="ATS-style keywords present in the resume"
    )


class SkillMatch(BaseModel):
    """How one required skill fared against the resume."""

    skill: Optional[str] = None
    present: Optional[bool] = Field(
        None, description="True if the resume actually evidences this skill"
    )
    evidence: Optional[str] = Field(
        None, description="Where in the resume it showed up; null if absent"
    )


class JobFit(BaseModel):
    """The result of scoring a resume against one job description."""

    job_title: Optional[str] = None
    match_score: Optional[int] = Field(
        None, description="Overall fit from 0 to 100"
    )
    verdict: Optional[str] = Field(
        None, description="Strong Match / Possible Match / Weak Match"
    )
    matched_skills: Optional[List[SkillMatch]] = None
    missing_skills: Optional[List[str]] = Field(
        None, description="Required skills with no evidence in the resume"
    )
    transferable_skills: Optional[List[str]] = Field(
        None, description="Adjacent skills that partially cover a gap"
    )
    experience_verdict: Optional[str] = Field(
        None, description="Does their experience level clear the bar?"
    )
    resume_improvements: Optional[List[str]] = Field(
        None, description="Concrete edits that would raise the score"
    )
    interview_questions: Optional[List[str]] = Field(
        None, description="Questions a recruiter should ask to probe the gaps"
    )
