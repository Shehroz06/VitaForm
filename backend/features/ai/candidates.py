import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import SectionType
from features.projects.models import Project
from features.resumes.section_registry import SECTION_MODELS


async def load_candidate_items(
    db: AsyncSession, profile_id: uuid.UUID
) -> dict[SectionType, list[Any]]:
    """Loads every non-deleted item, per section type, owned by a profile --
    the full candidate pool ranking narrows down before anything reaches a
    prompt. Shared by the resume, cover-letter, and LinkedIn generators."""
    result: dict[SectionType, list[Any]] = {}
    for section_type, model in SECTION_MODELS.items():
        stmt = select(model).where(
            model.profile_id == profile_id,  # type: ignore[attr-defined]
            model.deleted_at.is_(None),
        )
        if model is Project:
            stmt = stmt.options(selectinload(Project.skills))
        items = (await db.execute(stmt)).scalars().all()
        result[section_type] = list(items)
    return result


def flatten_descriptions_by_item_id(
    items_by_type: dict[SectionType, list[Any]],
) -> dict[uuid.UUID, str]:
    """Item objects loaded for ranking already carry their own description
    text -- this just makes it addressable by id, for page_fit.py's
    condensing step (both AI generation's and the manual builder's
    "extreme fit") and ai/service.py's _jd_tailored_overrides to look up
    without either one needing its own DB access. getattr with a default:
    not every section type has a description field (Skill, Certification),
    and that's fine -- there's simply nothing to condense or tailor for
    those."""
    descriptions: dict[uuid.UUID, str] = {}
    for items in items_by_type.values():
        for item in items:
            description = getattr(item, "description", None)
            if description:
                descriptions[item.id] = description
    return descriptions
