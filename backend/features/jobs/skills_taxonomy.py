"""Bounded, hand-curated skill taxonomy for ATS matching.

`features.ai.keyword_synonyms` clusters by broad *domain* -- one match pulls
in ~10 siblings (mentioning "vision" also credits "yolo", "segmentation",
etc.), which is deliberately loose for candidate *ranking*. ATS matching
needs the opposite: precise skill *identity*, so a job description asking
for "React" isn't satisfied by a profile that only ever says "Vue". Each
entry here is one real skill and the alternate ways people write it (case
variants, common abbreviations, punctuation variants) -- no cross-skill
bleed. Same no-model-call philosophy as the rest of this feature: fast,
free, deterministic, and extended by adding entries as gaps show up.
"""

import re
from dataclasses import dataclass

_NOT_BOUNDARY = r"[a-z0-9]"


@dataclass(frozen=True)
class SkillDefinition:
    canonical: str
    aliases: frozenset[str]


_SKILLS: tuple[SkillDefinition, ...] = (
    # --- Languages ---
    SkillDefinition("Python", frozenset({"python", "python3"})),
    SkillDefinition(
        # "js" is deliberately excluded as a bare alias -- it would false-
        # match inside "Node.js", "Vue.js", "Next.js", etc., since "." is a
        # non-word boundary character.
        "JavaScript",
        frozenset({"javascript", "es6", "ecmascript"}),
    ),
    SkillDefinition("TypeScript", frozenset({"typescript"})),
    SkillDefinition("Java", frozenset({"java"})),
    SkillDefinition("C++", frozenset({"c++", "cpp"})),
    SkillDefinition("C", frozenset({"c programming", "c language"})),
    SkillDefinition("C#", frozenset({"c#", "csharp"})),
    SkillDefinition("Go", frozenset({"golang", "go language"})),
    SkillDefinition("Rust", frozenset({"rust"})),
    SkillDefinition("Ruby", frozenset({"ruby"})),
    SkillDefinition("PHP", frozenset({"php"})),
    SkillDefinition("Swift", frozenset({"swift"})),
    SkillDefinition("Kotlin", frozenset({"kotlin"})),
    SkillDefinition("SQL", frozenset({"sql"})),
    SkillDefinition("R", frozenset({"r programming", "r language"})),
    SkillDefinition("MATLAB", frozenset({"matlab"})),
    SkillDefinition("Scala", frozenset({"scala"})),
    SkillDefinition("Bash", frozenset({"bash", "shell scripting"})),
    # --- Frontend ---
    SkillDefinition("React", frozenset({"react", "reactjs", "react.js"})),
    SkillDefinition("Vue", frozenset({"vue", "vuejs", "vue.js"})),
    SkillDefinition("Angular", frozenset({"angular", "angularjs"})),
    SkillDefinition("HTML", frozenset({"html", "html5"})),
    SkillDefinition("CSS", frozenset({"css", "css3"})),
    SkillDefinition("Next.js", frozenset({"next.js", "nextjs"})),
    SkillDefinition("Tailwind CSS", frozenset({"tailwind", "tailwindcss", "tailwind css"})),
    SkillDefinition("Redux", frozenset({"redux"})),
    SkillDefinition(
        "UI/UX Design", frozenset({"ui/ux", "ui design", "ux design", "user experience"})
    ),
    # --- Backend / frameworks ---
    SkillDefinition("Node.js", frozenset({"node", "node.js", "nodejs"})),
    SkillDefinition("Express", frozenset({"express", "expressjs", "express.js"})),
    SkillDefinition("Django", frozenset({"django"})),
    SkillDefinition("Flask", frozenset({"flask"})),
    SkillDefinition("FastAPI", frozenset({"fastapi", "fast api"})),
    SkillDefinition("Spring", frozenset({"spring", "spring boot"})),
    SkillDefinition(".NET", frozenset({".net", "dotnet", "asp.net"})),
    SkillDefinition("GraphQL", frozenset({"graphql"})),
    SkillDefinition("REST API", frozenset({"rest api", "restful", "rest apis", "api development"})),
    SkillDefinition("Microservices", frozenset({"microservice", "microservices"})),
    # --- Mobile ---
    SkillDefinition("Android", frozenset({"android"})),
    SkillDefinition("iOS", frozenset({"ios"})),
    SkillDefinition("Flutter", frozenset({"flutter"})),
    SkillDefinition("React Native", frozenset({"react native"})),
    # --- Databases ---
    SkillDefinition("PostgreSQL", frozenset({"postgresql", "postgres"})),
    SkillDefinition("MySQL", frozenset({"mysql"})),
    SkillDefinition("MongoDB", frozenset({"mongodb", "mongo"})),
    SkillDefinition("Redis", frozenset({"redis"})),
    SkillDefinition("SQLite", frozenset({"sqlite"})),
    SkillDefinition("Elasticsearch", frozenset({"elasticsearch", "elastic search"})),
    SkillDefinition("NoSQL", frozenset({"nosql"})),
    # --- Cloud / DevOps ---
    SkillDefinition("AWS", frozenset({"aws", "amazon web services"})),
    SkillDefinition("Azure", frozenset({"azure"})),
    SkillDefinition("GCP", frozenset({"gcp", "google cloud", "google cloud platform"})),
    SkillDefinition("Docker", frozenset({"docker"})),
    SkillDefinition("Kubernetes", frozenset({"kubernetes", "k8s"})),
    SkillDefinition("Terraform", frozenset({"terraform"})),
    SkillDefinition(
        "CI/CD", frozenset({"ci/cd", "continuous integration", "continuous deployment"})
    ),
    SkillDefinition("Jenkins", frozenset({"jenkins"})),
    SkillDefinition("Git", frozenset({"git", "version control"})),
    SkillDefinition("Linux", frozenset({"linux", "unix"})),
    SkillDefinition("Nginx", frozenset({"nginx"})),
    SkillDefinition("DevOps", frozenset({"devops"})),
    # --- Machine learning / AI ---
    SkillDefinition("Machine Learning", frozenset({"machine learning", "ml"})),
    SkillDefinition("Deep Learning", frozenset({"deep learning"})),
    SkillDefinition(
        "Neural Networks", frozenset({"neural network", "neural networks", "cnn", "rnn"})
    ),
    SkillDefinition(
        # "cv" itself is deliberately excluded -- too easily a false positive
        # for "curriculum vitae"/"resume" on a CV-builder platform like this.
        "Computer Vision",
        frozenset({"computer vision", "opencv", "cv2", "image processing"}),
    ),
    SkillDefinition(
        "NLP", frozenset({"nlp", "natural language processing", "text mining"})
    ),
    SkillDefinition(
        "Reinforcement Learning", frozenset({"reinforcement learning", "q-learning"})
    ),
    SkillDefinition("TensorFlow", frozenset({"tensorflow"})),
    SkillDefinition("PyTorch", frozenset({"pytorch"})),
    SkillDefinition("Keras", frozenset({"keras"})),
    SkillDefinition("Scikit-learn", frozenset({"scikit-learn", "scikit", "sklearn"})),
    SkillDefinition(
        "Hugging Face Transformers",
        frozenset({"huggingface", "hugging face", "transformers library"}),
    ),
    SkillDefinition("LangChain", frozenset({"langchain"})),
    SkillDefinition(
        "RAG",
        frozenset({"rag", "retrieval augmented generation", "retrieval-augmented generation"}),
    ),
    SkillDefinition("spaCy", frozenset({"spacy"})),
    SkillDefinition("XGBoost", frozenset({"xgboost"})),
    SkillDefinition(
        "Generative AI", frozenset({"generative ai", "genai", "gen ai", "generative models"})
    ),
    SkillDefinition(
        "LLMs", frozenset({"llm", "llms", "large language model", "large language models"})
    ),
    SkillDefinition("Transformers", frozenset({"transformer models", "attention mechanism"})),
    SkillDefinition("OCR", frozenset({"ocr", "optical character recognition"})),
    SkillDefinition("Explainable AI", frozenset({"explainable ai", "xai", "grad-cam", "shap"})),
    SkillDefinition(
        "Vision-Language Models", frozenset({"vision-language", "vision language model", "vlm"})
    ),
    # --- Data ---
    SkillDefinition("Pandas", frozenset({"pandas"})),
    SkillDefinition("NumPy", frozenset({"numpy"})),
    SkillDefinition("Data Analysis", frozenset({"data analysis", "data analytics"})),
    SkillDefinition("Data Visualization", frozenset({"data visualization", "data viz"})),
    SkillDefinition("ETL", frozenset({"etl", "data pipeline", "data pipelines"})),
    SkillDefinition("Apache Spark", frozenset({"apache spark", "spark", "pyspark"})),
    SkillDefinition("Airflow", frozenset({"airflow", "apache airflow"})),
    SkillDefinition("Data Engineering", frozenset({"data engineering"})),
    SkillDefinition("Power BI", frozenset({"power bi", "powerbi"})),
    SkillDefinition("Tableau", frozenset({"tableau"})),
    SkillDefinition("Data Warehousing", frozenset({"data warehouse", "data warehousing"})),
    # --- Testing / QA ---
    SkillDefinition("Unit Testing", frozenset({"unit testing", "unit tests"})),
    SkillDefinition("Pytest", frozenset({"pytest"})),
    SkillDefinition("Jest", frozenset({"jest"})),
    SkillDefinition("Selenium", frozenset({"selenium"})),
    SkillDefinition("QA", frozenset({"quality assurance", "qa testing"})),
    # --- Security ---
    SkillDefinition("Cybersecurity", frozenset({"cybersecurity", "cyber security", "infosec"})),
    SkillDefinition(
        "Penetration Testing", frozenset({"penetration testing", "pentest", "pentesting"})
    ),
    SkillDefinition("Encryption", frozenset({"encryption", "cryptography"})),
    # --- Other engineering domains ---
    SkillDefinition("Blockchain", frozenset({"blockchain", "web3", "solidity", "smart contracts"})),
    SkillDefinition(
        "IoT", frozenset({"iot", "internet of things", "embedded systems", "firmware"})
    ),
    SkillDefinition("Robotics", frozenset({"robotics", "ros", "autonomous systems"})),
    SkillDefinition(
        "Game Development", frozenset({"game development", "gamedev", "unity", "unreal"})
    ),
    SkillDefinition("AR/VR", frozenset({"ar/vr", "augmented reality", "virtual reality"})),
    SkillDefinition(
        "Quantum Computing", frozenset({"quantum computing", "qaoa", "qcnn", "quantum"})
    ),
    SkillDefinition("Computer Graphics", frozenset({"computer graphics"})),
    SkillDefinition("HCI", frozenset({"hci", "human-computer interaction"})),
    # --- Project / soft skills ---
    SkillDefinition("Project Management", frozenset({"project management"})),
    SkillDefinition("Agile", frozenset({"agile", "scrum", "kanban"})),
    SkillDefinition("Leadership", frozenset({"leadership", "team leadership"})),
    SkillDefinition("Communication", frozenset({"communication skills", "verbal communication"})),
    SkillDefinition("Problem Solving", frozenset({"problem solving", "problem-solving"})),
    SkillDefinition("Public Speaking", frozenset({"public speaking", "presentation skills"})),
)

_BOUNDARY_START = r"(?<!" + _NOT_BOUNDARY + r")"
_BOUNDARY_END = r"(?!" + _NOT_BOUNDARY + r")"


def _alias_pattern(alias: str) -> re.Pattern[str]:
    return re.compile(_BOUNDARY_START + re.escape(alias) + _BOUNDARY_END)


_COMPILED: tuple[tuple[SkillDefinition, tuple[re.Pattern[str], ...]], ...] = tuple(
    (skill, tuple(_alias_pattern(alias) for alias in skill.aliases)) for skill in _SKILLS
)

_ALIAS_TO_CANONICAL: dict[str, str] = {
    alias: skill.canonical for skill in _SKILLS for alias in skill.aliases
} | {skill.canonical.lower(): skill.canonical for skill in _SKILLS}


def match_skills(text: str) -> set[str]:
    """Return the canonical skill names whose alias phrases appear in
    `text`, matched as whole words/phrases (not substrings of unrelated
    words, and not split across separate tokens)."""
    lower = (text or "").lower()
    return {
        skill.canonical for skill, patterns in _COMPILED if any(p.search(lower) for p in patterns)
    }


def canonicalize(name: str) -> str:
    """Map a free-text skill name (e.g. from a profile's own Skill entries)
    to its taxonomy canonical form. Falls back to the name's own trimmed
    form when it isn't a recognized taxonomy entry, so a user's niche or
    unlisted skill still counts instead of being silently dropped."""
    return _ALIAS_TO_CANONICAL.get(name.strip().lower(), name.strip())
