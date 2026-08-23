from sqlalchemy.orm import InstrumentedAttribute

from app.exceptions.base import ValidationException


def resolve_sort(
    sort: str | None,
    allowed_columns: dict[str, InstrumentedAttribute],
    *,
    default: InstrumentedAttribute,
    default_desc: bool = False,
) -> tuple[InstrumentedAttribute, bool]:
    """Parses a `?sort=field` / `?sort=-field` query value against an
    allowlist of {name: column}, so a client can only ever sort by a
    column the endpoint explicitly exposes -- never an arbitrary/internal
    one. Returns (column, desc) ready for list_owned's sort_column/sort_desc.
    Falls back to `default`/`default_desc` when `sort` is absent."""
    if not sort:
        return default, default_desc

    desc = sort.startswith("-")
    field = sort[1:] if desc else sort
    column = allowed_columns.get(field)
    if column is None:
        allowed = ", ".join(sorted(allowed_columns))
        raise ValidationException(f"Cannot sort by '{field}'. Allowed fields: {allowed}.")
    return column, desc
