"""pdflatex isn't installed on every machine this test suite runs on (it's
a several-hundred-MB system dependency) -- the actual compile is exercised
in the Docker image, which does have it (see docker/backend.Dockerfile).
Here, the pure layout-metric math always runs; the real-compile tests are
skipped wherever pdflatex isn't on PATH rather than failing the whole suite."""

import shutil
from types import SimpleNamespace

import pytest

from features.resumes.latex_renderer import LatexRenderer, _layout_metrics
from features.resumes.schemas import ContactVisibility, ResumeStyle

_HAS_PDFLATEX = shutil.which("pdflatex") is not None


def test_layout_metrics_stay_within_sane_bounds_across_spacing_and_density() -> None:
    for spacing in ("relaxed", "cozy", "compact"):
        for density in (0.8, 0.9, 1.0):
            metrics = _layout_metrics(ResumeStyle(spacing=spacing, content_density=density))
            assert 0.3 <= metrics["margin_in"] <= 1.0
            assert 9.0 <= metrics["body_pt"] <= 11.0
            assert metrics["name_pt"] > metrics["body_pt"]
            assert metrics["section_gap_pt"] >= 0
            assert metrics["item_sep_pt"] >= 0
            # >= 5.0 (its own floor), not just >= 0: this is the rule-to-
            # content gap readability regression is about -- half of an
            # already-modest section_gap_pt read as visibly cramped.
            assert metrics["section_after_gap_pt"] >= 5.0


def test_layout_metrics_compact_is_tighter_than_relaxed() -> None:
    relaxed = _layout_metrics(ResumeStyle(spacing="relaxed", content_density=1.0))
    compact = _layout_metrics(ResumeStyle(spacing="compact", content_density=1.0))
    assert compact["margin_in"] < relaxed["margin_in"]
    assert compact["section_gap_pt"] < relaxed["section_gap_pt"]


def test_layout_metrics_lower_density_shrinks_margins_and_font() -> None:
    full = _layout_metrics(ResumeStyle(spacing="compact", content_density=1.0))
    floor = _layout_metrics(ResumeStyle(spacing="compact", content_density=0.8))
    assert floor["margin_in"] < full["margin_in"]
    assert floor["body_pt"] <= full["body_pt"]


def _minimal_context(**overrides: object) -> dict[str, object]:
    context: dict[str, object] = dict(
        resume_title="AI Resume",
        full_name="Ada Lovelace",
        profile=SimpleNamespace(
            location="Islamabad, Pakistan",
            phone="+92 300 1234567",
            website_url=None,
            github_url="https://github.com/example",
            linkedin_url="https://linkedin.com/in/example",
        ),
        email="ada@example.com",
        contact_visibility=ContactVisibility(),
        sections=[],
        style=ResumeStyle(),
    )
    context.update(overrides)
    return context


@pytest.mark.skipif(not _HAS_PDFLATEX, reason="pdflatex not installed on this machine")
async def test_latex_renderer_produces_a_pdf() -> None:
    pdf_bytes = await LatexRenderer().render("ats_safe", **_minimal_context())
    assert pdf_bytes.startswith(b"%PDF")


@pytest.mark.skipif(not _HAS_PDFLATEX, reason="pdflatex not installed on this machine")
async def test_latex_renderer_escapes_special_characters_without_breaking_compile() -> None:
    # A name/summary containing every LaTeX control character must compile
    # cleanly (proving latex_escape is actually wired into the template)
    # rather than being interpolated raw and breaking the document.
    context = _minimal_context(
        full_name=r"O'Malley & Sons #1 (100% $\write18{touch pwned}$)",
        sections=[
            {
                "type": "summary",
                "title": "Summary",
                "text": "Built systems handling 50% more load & 100+ req/s, ~zero downtime.",
            }
        ],
    )
    pdf_bytes = await LatexRenderer().render("ats_safe", **context)
    assert pdf_bytes.startswith(b"%PDF")
