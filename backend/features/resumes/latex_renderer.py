import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from features.resumes.latex_utils import (
    format_description,
    format_inline_description,
    format_paragraph,
    latex_escape,
    latex_inline,
    latex_safe_url,
)
from features.resumes.schemas import ResumeStyle

logger = logging.getLogger("app.resumes.latex")

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "resumes"
_COMPILE_TIMEOUT_SECONDS = 15

# No HTML autoescaping here (unlike renderer.py's _jinja_env): escaping HTML
# entities into a .tex source file would corrupt it. Every user-controlled
# value is instead run through the latex_escape/format_description filters
# explicitly, in the template itself -- see latex_utils.py's module
# docstring for why that's the correctness layer and -no-shell-escape below
# is the hard backstop.
#
# Jinja2's default {{ }}/{% %}/{# #} delimiters collide with real LaTeX
# syntax -- a macro call like \textbf{#1} contains the literal two
# characters `{#`, which Jinja's default lexer reads as the start of a
# comment tag with no matching close, breaking the parse. Standard fix
# (used by every Jinja-for-LaTeX writeup): swap to delimiters that don't
# appear in LaTeX source.
_latex_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    block_start_string=r"\BLOCK{",
    block_end_string="}",
    variable_start_string=r"\VAR{",
    variable_end_string="}",
    comment_start_string=r"\#{",
    comment_end_string="}",
    trim_blocks=True,
    lstrip_blocks=True,
)
_latex_jinja_env.filters["latex_escape"] = latex_escape
_latex_jinja_env.filters["latex_inline"] = latex_inline
_latex_jinja_env.filters["format_description"] = format_description
_latex_jinja_env.filters["format_inline_description"] = format_inline_description
_latex_jinja_env.filters["format_paragraph"] = format_paragraph
_latex_jinja_env.filters["latex_safe_url"] = latex_safe_url

# Jake's-Resume-convention base values at spacing="cozy", content_density=1.0.
_BASE_MARGIN_IN = 0.65
_BASE_BODY_PT = 10.5
_BASE_NAME_PT = 22.0
_SPACING_MARGIN_IN: dict[str, float] = {
    "relaxed": 0.85,
    "cozy": 0.65,
    "compact": 0.5,
    "extreme": 0.4,
}
_SPACING_SECTION_GAP_PT: dict[str, float] = {
    "relaxed": 10.0,
    "cozy": 7.0,
    "compact": 4.0,
    "extreme": 3.0,
}
_SPACING_ITEM_SEP_PT: dict[str, float] = {
    "relaxed": 4.0,
    "cozy": 2.0,
    "compact": 0.0,
    "extreme": 0.0,
}
# Font size only nudges down modestly at the density floor -- legibility
# matters more here than in the HTML/CSS path, since a PDF can't be zoomed
# in-browser the way a web page can.
_DENSITY_FONT_FLOOR_PT = 9.5


class LatexRenderError(Exception):
    """pdflatex exited non-zero or produced no PDF. Carries the tail of the
    compile log so a failure is diagnosable instead of a bare exit code."""


_SECTION_GAP_FLOOR_PT = 3.0
# The gap between the rule under a section heading and the content below it
# (\titlespacing's "after" value) is its own, more generous floor -- it was
# previously derived as half of section_gap_pt, which read as cramped even
# at non-extreme density/spacing (half of an already-modest "before" gap
# is a small number). Rule-to-content spacing matters more for readability
# than the ratio between "before" and "after" gaps stays consistent.
_SECTION_AFTER_GAP_FLOOR_PT = 5.0
_SECTION_AFTER_GAP_RATIO = 0.8


def _layout_metrics(style: ResumeStyle) -> dict[str, float]:
    density = style.content_density
    margin_in = _SPACING_MARGIN_IN[style.spacing] * (0.7 + 0.3 * density)
    # Floored, not just scaled: the .tex template's \titlerule sits between
    # the section title and this gap (see its comment on why the vspace
    # around \titlerule is bounded) -- letting this shrink arbitrarily at
    # low density/compact spacing would let the rule collide with the
    # following line even with that fix, since there'd be no gap left at all.
    section_gap_pt = max(_SECTION_GAP_FLOOR_PT, _SPACING_SECTION_GAP_PT[style.spacing] * density)
    section_after_gap_pt = max(
        _SECTION_AFTER_GAP_FLOOR_PT, section_gap_pt * _SECTION_AFTER_GAP_RATIO
    )
    item_sep_pt = _SPACING_ITEM_SEP_PT[style.spacing]
    body_pt = max(_DENSITY_FONT_FLOOR_PT, _BASE_BODY_PT * density)
    name_pt = max(_DENSITY_FONT_FLOOR_PT * 1.8, _BASE_NAME_PT * density)
    return {
        "margin_in": round(margin_in, 3),
        "section_gap_pt": round(section_gap_pt, 2),
        "section_after_gap_pt": round(section_after_gap_pt, 2),
        "item_sep_pt": round(item_sep_pt, 2),
        "body_pt": round(body_pt, 2),
        "name_pt": round(name_pt, 2),
    }


class LatexRenderer:
    """Jinja2(.tex) -> pdflatex -> PDF bytes. A separate pipeline from
    ResumeRenderer's WeasyPrint path (see renderer.py's dispatch), used only
    by templates whose render_engine is RenderEngine.LATEX."""

    async def render(self, template_slug: str, **context: object) -> bytes:
        # pdflatex is a slow (up to _COMPILE_TIMEOUT_SECONDS), blocking
        # subprocess call -- running it directly here would stall the whole
        # asyncio event loop, freezing every other in-flight request for as
        # long as this one compile takes. Offloaded to a worker thread so
        # only this request waits on it.
        return await asyncio.to_thread(self._render_sync, template_slug, **context)

    def render_source(self, template_slug: str, **context: object) -> str:
        """Just the Jinja(.tex) render step, no pdflatex compile -- a plain
        Jinja render is cheap (unlike the subprocess compile), so this runs
        synchronously rather than via asyncio.to_thread. Shared by render()
        (which compiles this) and the raw .tex-source download endpoint
        (features/resumes/router.py's export_resume_tex), so both always
        produce byte-identical source for the same content."""
        style: ResumeStyle = context["style"]  # type: ignore[assignment]
        return _latex_jinja_env.get_template(f"{template_slug}/resume.tex.jinja2").render(
            **context, **_layout_metrics(style)
        )

    def _render_sync(self, template_slug: str, **context: object) -> bytes:
        tex_source = self.render_source(template_slug, **context)

        with tempfile.TemporaryDirectory(prefix="resume-latex-") as tmp_dir:
            tmp_path = Path(tmp_dir)
            tex_path = tmp_path / "resume.tex"
            tex_path.write_text(tex_source, encoding="utf-8")

            try:
                result = subprocess.run(
                    [
                        "pdflatex",
                        "-interaction=nonstopmode",
                        "-halt-on-error",
                        "-no-shell-escape",
                        f"-output-directory={tmp_dir}",
                        str(tex_path),
                    ],
                    cwd=tmp_dir,
                    capture_output=True,
                    timeout=_COMPILE_TIMEOUT_SECONDS,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise LatexRenderError(
                    f"pdflatex did not finish within {_COMPILE_TIMEOUT_SECONDS}s."
                ) from exc

            pdf_path = tmp_path / "resume.pdf"
            if result.returncode != 0 or not pdf_path.exists():
                log_tail = _read_log_tail(tmp_path / "resume.log")
                logger.error(
                    "pdflatex compile failed (exit %s) for template %s:\n%s",
                    result.returncode,
                    template_slug,
                    log_tail,
                )
                raise LatexRenderError(
                    f"pdflatex exited {result.returncode}. Log tail:\n{log_tail}"
                )

            return pdf_path.read_bytes()


def _read_log_tail(log_path: Path, *, max_lines: int = 40) -> str:
    if not log_path.exists():
        return "(no log produced)"
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-max_lines:])
