"""Named rate-limit dependency instances, applied via `dependencies=[...]`
on the routes that need them. Kept as module-level singletons (rather than
constructed inline at each call site) so the test suite can override each
one by identity in a single place -- see conftest.py's `client` fixture."""

from app.dependencies.rate_limit import IpRateLimit, UserRateLimit

# Auth endpoints: no account exists yet to scope by, so these are per-IP.
# Credential-guessing and account-enumeration are the threats here, not
# volume, so limits are tight relative to genuine human usage.
login_rate_limit = IpRateLimit("auth:login", max_requests=10, window_seconds=300)
register_rate_limit = IpRateLimit("auth:register", max_requests=5, window_seconds=3600)
forgot_password_rate_limit = IpRateLimit(
    "auth:forgot-password", max_requests=5, window_seconds=3600
)

# AI generation endpoints: each call is a real, paid provider request (and
# provider_runner.py's fallback chain can multiply one call into several),
# so these are scoped per-user to cap real-money abuse per account.
resume_generate_rate_limit = UserRateLimit(
    "ai:resume-generate", max_requests=20, window_seconds=3600
)
rewrite_text_rate_limit = UserRateLimit("ai:rewrite-text", max_requests=30, window_seconds=3600)
cover_letter_rate_limit = UserRateLimit("ai:cover-letter", max_requests=20, window_seconds=3600)
linkedin_rate_limit = UserRateLimit("ai:linkedin", max_requests=20, window_seconds=3600)
cv_import_rate_limit = UserRateLimit("ai:cv-import", max_requests=10, window_seconds=3600)

# Rendering endpoints: each triggers a real pdflatex/WeasyPrint compile.
# Not AI-costly, but still CPU-expensive, so a per-user cap sized to the
# call pattern rather than a single flat number.
#
# export/autofit are explicit one-off clicks -- 60/hour is already far
# past any real session. preview is different: the builder refetches it
# after every debounced autosave (~1 render per editing pause) *and* a
# multi-page resume fetches one request per page, so an active editing
# session legitimately generates hundreds of these. Its cap is set high
# enough that a normal session never hits it, while still bounding a
# runaway client.
resume_export_rate_limit = UserRateLimit(
    "render:resume-export", max_requests=60, window_seconds=3600
)
resume_autofit_rate_limit = UserRateLimit(
    "render:resume-autofit", max_requests=60, window_seconds=3600
)
resume_preview_rate_limit = UserRateLimit(
    "render:resume-preview", max_requests=900, window_seconds=3600
)
template_preview_rate_limit = UserRateLimit(
    "render:template-preview", max_requests=600, window_seconds=3600
)
