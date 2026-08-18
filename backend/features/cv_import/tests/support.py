"""Test doubles and fixtures for cv_import. build_sample_pdf() produces a
real, PyMuPDF-parseable PDF (not just magic-byte-prefixed junk) so the
extraction pipeline under test actually exercises real text/layout
extraction, matching how every other phase in this codebase insists on
exercising the real pipeline rather than a stub."""

import json
from collections.abc import AsyncIterator

import pymupdf

from app.core.ai_provider import GenerationResult


def build_sample_pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Jane Doe", fontsize=20)
    page.insert_text((72, 100), "Backend Engineer", fontsize=11)
    page.insert_text((72, 140), "EXPERIENCE", fontsize=14)
    page.insert_text((72, 165), "Senior Engineer at Acme Corp", fontsize=11)
    page.insert_text((72, 185), "Jan 2022 - Present. Built APIs with Python.", fontsize=10)
    page.insert_text((72, 220), "EDUCATION", fontsize=14)
    page.insert_text((72, 245), "BSc Computer Science, MIT", fontsize=11)
    pdf_bytes: bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


_SAMPLE_CLASSIFICATION_PAYLOAD = {
    "bio": None,
    "sections": {
        "experience": [
            {
                "company_name": "Acme Corp",
                "job_title": "Senior Engineer",
                "employment_type": "full_time",
                "start_date": "2022-01-01",
                "is_current": True,
                "description": "Built APIs with Python.",
            }
        ],
        "education": [
            {
                "institution_name": "MIT",
                "degree": "BSc Computer Science",
                "start_date": "2018-01-01",
            }
        ],
    },
}


class FakeClassifierProvider:
    def __init__(self, name: str = "gemini", *, fail_times: int = 0) -> None:
        self.name = name
        self.model = "fake-model"
        self.call_count = 0
        self._fail_times = fail_times
        self.received_images: list[list[bytes] | None] = []

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float,
        max_tokens: int,
        images: list[bytes] | None = None,
    ) -> GenerationResult:
        self.call_count += 1
        self.received_images.append(images)
        if self.call_count <= self._fail_times:
            raise RuntimeError("simulated provider failure")
        return GenerationResult(
            text=json.dumps(_SAMPLE_CLASSIFICATION_PAYLOAD),
            provider=self.name,
            model=self.model,
            latency_ms=5,
            prompt_tokens=100,
            completion_tokens=50,
        )

    def stream(
        self, system_prompt: str, user_prompt: str, *, temperature: float, max_tokens: int
    ) -> AsyncIterator[str]:
        async def _empty() -> AsyncIterator[str]:
            return
            yield ""

        return _empty()

    async def health(self) -> bool:
        return True

    def list_models(self) -> list[str]:
        return [self.model]

    def estimate_tokens(self, text: str) -> int:
        return len(text)
