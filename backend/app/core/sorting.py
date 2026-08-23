from sqlalchemy.orm import InstrumentedAttribute

from app.exceptions.base import ValidationException

SortSpec = list[tuple[InstrumentedAttribute, bool]]


def resolve_sort(
    sort: str | None,
    allowed_columns: dict[str, InstrumentedAttribute],
    *,
    default: InstrumentedAttribute,
    default_desc: bool = False,
) -> SortSpec:
    """Parses a `?sort=field` / `?sort=-field` query value -- comma-separated
    for multiple keys, e.g. `?sort=name,-created_at`, per this project's API
    standards doc -- against an allowlist of {name: column}, so a client can
    only ever sort by a column the endpoint explicitly exposes, never an
    arbitrary/internal one. Returns a list of (column, desc) pairs ready
    for list_owned's `sort_columns`. Falls back to `default`/`default_desc`
    when `sort` is absent."""
    if not sort:
        return [(default, default_desc)]

    spec: SortSpec = []
    for raw_field in sort.split(","):
        raw_field = raw_field.strip()
        if not raw_field:
            continue
        desc = raw_field.startswith("-")
        field = raw_field[1:] if desc else raw_field
        column = allowed_columns.get(field)
        if column is None:
            allowed = ", ".join(sorted(allowed_columns))
            raise ValidationException(f"Cannot sort by '{field}'. Allowed fields: {allowed}.")
        spec.append((column, desc))

    return spec or [(default, default_desc)]
