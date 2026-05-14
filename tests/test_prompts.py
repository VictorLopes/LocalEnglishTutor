"""Unit tests for the SUBJECT_SYSTEM_PROMPT template."""
import pytest
from prompts import SUBJECT_SYSTEM_PROMPT


def test_prompt_contains_level():
    result = SUBJECT_SYSTEM_PROMPT.format(level="B2", subject="Technology")
    assert "B2" in result


def test_prompt_contains_subject():
    result = SUBJECT_SYSTEM_PROMPT.format(level="A1", subject="Food and Drink")
    assert "Food and Drink" in result


def test_prompt_mentions_role():
    result = SUBJECT_SYSTEM_PROMPT.format(level="C1", subject="Philosophy")
    assert "Tutor" in result or "tutor" in result


def test_prompt_contains_brevity_guideline():
    result = SUBJECT_SYSTEM_PROMPT.format(level="A2", subject="Shopping")
    # The prompt instructs to keep responses short for audio interaction
    assert "concise" in result or "sentence" in result


def test_prompt_format_all_levels():
    levels = ["A1", "A2", "B1", "B2", "C1", "C2", "Business", "Job Interview"]
    for level in levels:
        result = SUBJECT_SYSTEM_PROMPT.format(level=level, subject="Test Subject")
        assert level in result
        assert "Test Subject" in result
