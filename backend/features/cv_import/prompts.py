"""Builds the classification prompt. The per-section field spec is generated
directly from IMPORT_TARGET_SCHEMAS (the same Pydantic models the real
create endpoints use) so the prompt can never drift out of sync with what
validator.py will actually accept."""

import enum
import types
import typing

from pydantic.fields import FieldInfo

from app.core.enums import SectionType
from features.cv_import.target_schemas import IMPORT_TARGET_SCHEMAS

CLASSIFY_PURPOSE = "cv_import_classify"
CLASSIFY_VERSION = 1
CLASSIFY_TEMPERATURE = 0.1

# projects.skill_ids can't be populated by the classifier (it doesn't know
# real skill UUIDs) -- omitting it from the prompt spec lets it default to
# [] on validation, same as an ordinary create request that leaves it out.
_HIDDEN_FIELDS = {SectionType.PROJECTS: {"skill_ids"}}

CLASSIFY_SYSTEM_PROMPT = """You are extracting structured resume/CV data from raw text taken \
from a PDF. The text has been re-derived from the PDF's real layout: lines prefixed \
with "## " are detected section headings (based on font size), everything \
else is body text in reading order. Blank lines separate visual blocks.

Rules, all mandatory:
- Only include information that is explicitly present in the source text or image. \
Never invent, infer, guess, or embellish a fact -- not a company name, not a \
date, not a skill. If a value is not stated, omit that field (or the whole \
item, if a required field is missing).
- Dates must be ISO format YYYY-MM-DD. If only a month and year are given, use \
day 01. If only a year is given, use January 1 of that year.
- Every item you output must go under the correct section key from the schema \
below -- do not invent new section keys.
- "bio" is the only field where you may write connective prose, and only by \
paraphrasing the candidate's own stated summary/objective text if one exists \
in the source. If there is no summary/objective in the source, omit "bio" \
entirely -- do not synthesize one from the rest of the resume.
- Output ONLY a single JSON object matching the schema below. No markdown code \
fences, no commentary before or after."""


def _describe_type(annotation: object) -> str:
    origin = typing.get_origin(annotation)
    if origin in (typing.Union, types.UnionType):
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        return _describe_type(args[0]) if len(args) == 1 else "string"
    if origin is list:
        (inner,) = typing.get_args(annotation)
        return f"array of {_describe_type(inner)}"
    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        values = ", ".join(f'"{member.value}"' for member in annotation)
        return f"one of [{values}]"
    if annotation is bool:
        return "boolean"
    type_name = getattr(annotation, "__name__", str(annotation))
    return {
        "date": "string, format YYYY-MM-DD",
        "EmailStr": "string, email address",
        "UUID": "string",
    }.get(type_name, "string")


def _describe_field(name: str, field: FieldInfo) -> str:
    requiredness = "required" if field.is_required() else "optional"
    return f'    "{name}": {_describe_type(field.annotation)}  # {requiredness}'


def build_schema_spec() -> str:
    sections = []
    for section_type, schema in IMPORT_TARGET_SCHEMAS.items():
        hidden = _HIDDEN_FIELDS.get(section_type, set())
        field_lines = "\n".join(
            _describe_field(name, field)
            for name, field in schema.model_fields.items()
            if name not in hidden
        )
        sections.append(f'  "{section_type.value}": [\n  {{\n{field_lines}\n  }}, ...\n  ]')
    return "{\n" + ",\n".join(sections) + "\n}"


def build_classify_user_prompt(extracted_text: str) -> str:
    schema_spec = build_schema_spec()
    return f"""Extract structured data from this CV/resume text into the following JSON shape. \
Every top-level key is optional -- omit any section with no matching content in \
the source. "bio" is a top-level string field (see the rule above), separate \
from "sections".

{{
  "bio": "string, optional",
  "sections": {schema_spec}
}}

Source text extracted from the PDF:
---
{extracted_text}
---"""
