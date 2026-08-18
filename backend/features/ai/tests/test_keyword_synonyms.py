from datetime import date
from types import SimpleNamespace

from app.core.enums import SectionType
from features.ai.keyword_synonyms import expand_keywords
from features.ai.ranking import extract_keywords, rank_and_select


def test_expand_keywords_pulls_in_domain_synonyms() -> None:
    keywords = extract_keywords("We need a Computer Vision Engineer.")
    expanded = expand_keywords(keywords)

    assert "opencv" in expanded
    assert "yolo" in expanded
    assert "detection" in expanded
    # Original literal keywords are still present, never dropped.
    assert keywords <= expanded


def test_expand_keywords_is_a_noop_for_unrelated_domains() -> None:
    keywords = extract_keywords("We are hiring a barista with excellent customer service skills.")
    expanded = expand_keywords(keywords)

    assert "opencv" not in expanded
    assert "kubernetes" not in expanded


def test_rank_and_select_no_longer_excludes_opencv_project_for_computer_vision_jd() -> None:
    """Reproduces the reported case: a drone project whose only relevant
    text is "OpenCV"/"EasyOCR" was excluded from a "Computer Vision
    Engineer" job description by the literal-token hard gate, because
    "computer"/"vision" never appear verbatim in the project's own text."""
    keywords = expand_keywords(
        extract_keywords(
            "We are hiring a Computer Vision Engineer to build real-time "
            "perception systems for autonomous platforms."
        )
    )

    items_by_type = {
        SectionType.PROJECTS: [
            SimpleNamespace(
                id="drone-vision",
                title="RTSP-Vision",
                role="Lead Engineer",
                description=(
                    "Built a real-time drone flight-path monitor that reads live GPS "
                    "coordinates from a drone's on-screen display via an RTSP video "
                    "stream. Backend in Python with OpenCV and EasyOCR for coordinate "
                    "extraction; FastAPI and WebSocket stream live coordinates to a "
                    "Leaflet.js map frontend."
                ),
                start_date=date(2025, 1, 1),
                end_date=date(2025, 6, 1),
                is_pinned=False,
                skills=[],
            ),
            SimpleNamespace(
                id="recipe-blog",
                title="Personal Recipe Blog",
                role="Author",
                description="A static site listing family recipes and cooking tips.",
                start_date=date(2022, 1, 1),
                end_date=date(2022, 3, 1),
                is_pinned=False,
                skills=[],
            ),
        ],
    }

    ranked = rank_and_select(items_by_type, keywords)

    project_ids = {r.item.id for r in ranked[SectionType.PROJECTS]}
    assert "drone-vision" in project_ids
    assert "recipe-blog" not in project_ids
