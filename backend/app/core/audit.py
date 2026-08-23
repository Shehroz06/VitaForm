"""Automatic audit-log writer.

A SQLAlchemy `before_flush` listener that records every create/update/
(soft-)delete of a profile-owned resource -- registered once, at import
time (see app/main.py), rather than instrumented into each feature's
service. This is deliberate: CLAUDE.md's LOGGING section calls for audit
logs across the whole profile ("Everything has CRUD"), and instrumenting
that by hand into every one of the ~20 resource services would be the
same three lines copy-pasted ~20 times -- exactly the kind of duplication
this project's own rules forbid. A session-level listener gets it once,
for every current and future profile-owned model, for free.

Scope, deliberately: only models with a *direct* `profile_id` column are
audited. A child row that's only reachable via a parent (e.g. ResumeVersion,
which hangs off Resume) is not -- walking relationships to find an
ancestor's profile_id inside a flush-time listener would be expensive and,
for something like autosave, extremely noisy (an audit entry every few
seconds while a user edits a resume). Auditing the owning parent's own
create/update/delete already captures the meaningful lifecycle event.
"""

import uuid
from typing import Any

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from features.audit_log.models import AuditAction, AuditLog


def _resource_type_for(instance: Any) -> str | None:
    table_name = getattr(instance, "__tablename__", None)
    return table_name if isinstance(table_name, str) else None


def _deleted_at_was_just_set(instance: Any) -> bool:
    if not hasattr(instance, "deleted_at"):
        return False
    history = inspect(instance).attrs.deleted_at.history
    return bool(history.added) and history.added[0] is not None


@event.listens_for(Session, "before_flush")
def _write_audit_logs(session: Session, flush_context: Any, instances: Any) -> None:
    for instance in session.new:
        if isinstance(instance, AuditLog):
            continue
        profile_id = getattr(instance, "profile_id", None)
        resource_type = _resource_type_for(instance)
        if profile_id is None or resource_type is None:
            continue
        # UUIDPrimaryKeyMixin's `id` gets its default (uuid.uuid4) applied
        # by SQLAlchemy while building the INSERT, which happens after
        # before_flush runs -- so a brand-new instance's `id` is still None
        # here unless we assign it ourselves first.
        if instance.id is None:
            instance.id = uuid.uuid4()
        session.add(
            AuditLog(
                profile_id=profile_id,
                action=AuditAction.CREATED,
                resource_type=resource_type,
                resource_id=instance.id,
            )
        )

    for instance in session.dirty:
        if isinstance(instance, AuditLog) or not session.is_modified(instance):
            continue
        profile_id = getattr(instance, "profile_id", None)
        resource_type = _resource_type_for(instance)
        if profile_id is None or resource_type is None:
            continue
        action = AuditAction.DELETED if _deleted_at_was_just_set(instance) else AuditAction.UPDATED
        session.add(
            AuditLog(
                profile_id=profile_id,
                action=action,
                resource_type=resource_type,
                resource_id=instance.id,
            )
        )
