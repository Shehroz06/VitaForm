DEFAULT_TEMPLATES = [
    ("classic", "Classic", "A clean, single-column, ATS-friendly layout."),
]

# Seeded in a later migration (076c...); kept as a separate list so the
# original seed migration's behavior never changes on replay.
ADDITIONAL_TEMPLATES = [
    ("modern", "Modern", "Bold headings with a navy accent, built for a contemporary look."),
    ("minimal", "Minimal", "Light typography and generous whitespace for an understated resume."),
    ("compact", "Compact", "Denser spacing that fits more on the page — for longer histories."),
    ("executive", "Executive", "A centered, formal layout for senior and leadership roles."),
]

# Kept as its own list, same reasoning as ADDITIONAL_TEMPLATES above -- a
# separate seed migration per batch of templates so replaying earlier
# migrations never changes.
ATS_SAFE_TEMPLATES = [
    (
        "ats_safe",
        "LaTeX",
        "The most conservative layout, built purely for maximum parser compatibility.",
    ),
]
