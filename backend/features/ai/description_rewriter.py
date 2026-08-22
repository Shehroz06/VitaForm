"""Optional, best-effort polish pass on top of description_condenser.py's
extractive selection: an actual AI rewrite for phrasing/concision, guarded
by an automated, deterministic fact-check rather than trusted on the
model's word alone.

Why this exists as a separate, narrower step instead of folding rewriting
into the main resume-generation prompt: it can fail (provider down, bad
JSON, a rewrite that doesn't pass the fact-check) without taking the whole
generation down with it -- every failure mode here falls back to the
already-computed extractive text (reorder-only, description_condenser.py),
never to nothing and never to an unverified AI rewrite.

The fact-check is intentionally *not* another AI call ("did the AI's
rewrite invent anything?" asked to a second AI is exactly the kind of
unreliable AI-verifying-AI check CLAUDE.md's "AI never invents" principle
exists to avoid). It's two deterministic comparisons instead:
- every number that appears in the rewrite must already appear in the
  original (catches inflated/invented metrics).
- every skill/technology the taxonomy recognizes in the rewrite must
  already be recognized in the original (catches invented tech stacks).
Neither is a complete semantic fact-check, but both are precise about the
two most damaging, highest-frequency categories of resume fabrication, and
neither can be fooled by the model just asserting it followed the rules.
"""

import json
import re
import uuid

from pydantic import BaseModel, Field, ValidationError

from app.config.settings import Settings
from features.ai.provider_runner import run_with_fallback
from features.ai.repository import PromptHistoryRepository
from features.jobs.skills_taxonomy import match_skills

REWRITE_PURPOSE = "description_rewrite"
REWRITE_VERSION = 1
_REWRITE_TEMPERATURE = 0.3
_MAX_OUTPUT_TOKENS = 2000

REWRITE_SYSTEM_PROMPT = """\
You are a resume-editing assistant inside a Career Operating System.

You will be given several resume item descriptions, each already written by
the user. Your only job is to rephrase each one to be more concise and more
impactful for the given job description -- never to add information.

Rules, no exceptions:
- Do not add any technology, tool, skill, metric, number, or achievement
  that is not already stated in that item's own original text. Rephrasing
  is allowed; inventing is not.
- Do not invent context from the job description into an item that didn't
  already have it -- you may reorder/emphasize what's already there, never
  graft on something the item never mentioned.
- Keep each rewrite roughly the same length or shorter than the original,
  never meaningfully longer.
- If an item's original text is already tight and well-phrased, or you
  cannot improve it without adding information, return it unchanged.
- Preserve the original's format: if the original is bullet points (lines
  starting with "-"), the rewrite must be bullet points too, same count or
  fewer. If it's a paragraph, the rewrite is a paragraph.
- Respond with ONLY a single valid JSON object, no markdown, no code
  fences, no commentary. Exact shape:

{"items": [{"id": "uuid", "text": "rewritten text"}, ...]}

One entry per id you were given, in any order.
"""


class _RewriteItem(BaseModel):
    id: uuid.UUID
    text: str = Field(min_length=1)


class _RewriteResponse(BaseModel):
    items: list[_RewriteItem] = Field(default_factory=list)


class RewriteResponseValidationError(Exception):
    """Malformed enough to warrant a retry (bad JSON, wrong schema) --
    distinct from a single item failing the fact-check, which is handled
    silently by dropping just that item."""


_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?%?")


def _numbers_in(text: str) -> set[str]:
    return set(_NUMBER_RE.findall(text))


def passes_fact_check(original: str, rewritten: str) -> bool:
    """True only if the rewrite introduces no number and no
    taxonomy-recognized skill that wasn't already in the original text."""
    if _numbers_in(rewritten) - _numbers_in(original):
        return False
    if match_skills(rewritten) - match_skills(original):
        return False
    return True


def build_rewrite_prompt(
    items: list[tuple[uuid.UUID, str]],
    *,
    job_description: str,
    target_role: str | None,
) -> str:
    lines = [
        f"Job description:\n{job_description}\n",
        f"Target role: {target_role or 'not specified'}",
        "\nItems to rewrite:",
    ]
    lines.extend(f"- id={item_id}\n  text: {text}" for item_id, text in items)
    return "\n".join(lines)


def _parse_response(raw_text: str, valid_item_ids: set[uuid.UUID]) -> dict[uuid.UUID, str]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```\s*$", "", raw_text.strip(), flags=re.MULTILINE)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RewriteResponseValidationError(f"Rewrite response was not valid JSON: {exc}") from exc
    try:
        parsed = _RewriteResponse.model_validate(data)
    except ValidationError as exc:
        raise RewriteResponseValidationError(
            f"Rewrite response did not match the expected schema: {exc}"
        ) from exc

    # Same defense-in-depth as validator.py: drop anything for an id we
    # didn't ask about rather than failing the whole batch.
    return {item.id: item.text.strip() for item in parsed.items if item.id in valid_item_ids}


async def rewrite_descriptions(
    settings: Settings,
    prompt_history_repository: PromptHistoryRepository,
    descriptions_by_item_id: dict[uuid.UUID, str],
    *,
    job_description: str,
    target_role: str | None,
) -> dict[uuid.UUID, str]:
    """Best-effort: returns only the items whose rewrite both came back
    from the provider and passed passes_fact_check. Every other item
    (provider failure, malformed response, a rewrite that fails the fact
    check) is simply absent from the result -- callers already have an
    extractive fallback (description_condenser.py) for exactly this case,
    so this never needs to raise on partial or total failure."""
    if not descriptions_by_item_id:
        return {}

    items = list(descriptions_by_item_id.items())
    user_prompt = build_rewrite_prompt(
        items, job_description=job_description, target_role=target_role
    )
    await prompt_history_repository.get_or_create(
        REWRITE_PURPOSE, REWRITE_VERSION, REWRITE_SYSTEM_PROMPT
    )

    valid_ids = set(descriptions_by_item_id.keys())
    run_result = await run_with_fallback(
        settings,
        REWRITE_SYSTEM_PROMPT,
        user_prompt,
        temperature=_REWRITE_TEMPERATURE,
        max_tokens=_MAX_OUTPUT_TOKENS,
        validate=lambda text: _parse_response(text, valid_ids),
    )
    if run_result.value is None:
        return {}

    return {
        item_id: rewritten
        for item_id, rewritten in run_result.value.items()
        if passes_fact_check(descriptions_by_item_id[item_id], rewritten)
    }
