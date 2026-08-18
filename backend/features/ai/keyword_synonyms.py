"""Bounded, hand-curated domain-synonym expansion for job-description
keywords, applied on top of `ranking.extract_keywords`.

`extract_keywords` is pure literal tokenization -- no stemming, no synonyms.
That's fine for the item side (a profile item's own words are what they
are), but it produces false negatives on the job-description side whenever
the JD and a profile item describe the same thing in different words (e.g.
a JD says "computer vision" while a project's own text only ever says
"OpenCV"). This module only enriches what counts as "the JD is asking for
this" -- it never rewrites or scores an item's own text, keeping the rules-
based, no-model-call design of `ranking.py` intact.
"""

_DOMAIN_SYNONYMS: dict[str, frozenset[str]] = {
    "vision": frozenset(
        {
            "computer",
            "vision",
            "opencv",
            "cv2",
            "yolo",
            "detection",
            "segmentation",
            "imagery",
            "image",
        }
    ),
    "ml": frozenset(
        {
            "machine",
            "learning",
            "ml",
            "ai",
            "model",
            "models",
            "tensorflow",
            "pytorch",
            "keras",
            "sklearn",
            "scikit",
            "deep",
            "neural",
            "nlp",
        }
    ),
    "data": frozenset(
        {"data", "pandas", "numpy", "etl", "pipeline", "warehouse", "analytics", "spark", "airflow"}
    ),
    "backend": frozenset(
        {"backend", "api", "apis", "server", "microservice", "microservices", "rest", "graphql"}
    ),
    "frontend": frozenset(
        {
            "frontend",
            "ui",
            "ux",
            "react",
            "vue",
            "angular",
            "css",
            "html",
            "javascript",
            "typescript",
        }
    ),
    "mobile": frozenset({"mobile", "android", "ios", "flutter", "swift", "kotlin", "react-native"}),
    "cloud": frozenset(
        {
            "cloud",
            "aws",
            "azure",
            "gcp",
            "devops",
            "docker",
            "kubernetes",
            "k8s",
            "terraform",
            "ci",
            "cd",
        }
    ),
    "database": frozenset(
        {
            "database",
            "databases",
            "sql",
            "postgres",
            "postgresql",
            "mysql",
            "mongodb",
            "nosql",
            "redis",
        }
    ),
    "security": frozenset(
        {
            "security",
            "cybersecurity",
            "penetration",
            "pentest",
            "vulnerability",
            "encryption",
            "auth",
        }
    ),
    "embedded": frozenset(
        {"embedded", "firmware", "iot", "arduino", "raspberry", "microcontroller", "rtos"}
    ),
    "web": frozenset({"web", "website", "webapp", "fullstack", "full-stack"}),
    "gamedev": frozenset({"game", "gamedev", "unity", "unreal", "gameplay"}),
    "robotics": frozenset({"robotics", "robot", "ros", "autonomous", "drone", "drones", "gps"}),
    "blockchain": frozenset({"blockchain", "web3", "smart", "contract", "solidity", "crypto"}),
}


def expand_keywords(keywords: set[str]) -> set[str]:
    """Unions in every domain's full synonym set whenever any one of that
    domain's own terms already appears in `keywords` -- one domain touched
    is enough to pull in its siblings, since a JD mentioning "OpenCV" is
    just as clearly computer-vision-flavored as one mentioning "vision"."""
    expanded = set(keywords)
    for synonyms in _DOMAIN_SYNONYMS.values():
        if synonyms & keywords:
            expanded |= synonyms
    return expanded
