import pytest

from app.interfaces.http.routes.auth import classify_profile


@pytest.mark.parametrize(
    ("score", "expected_profile"),
    [
        (10, "conservador"),
        (15, "conservador"),
        (16, "moderado"),
        (22, "moderado"),
        (23, "agresivo"),
        (30, "agresivo"),
    ],
)
def test_classify_profile_by_score_ranges(score: int, expected_profile: str) -> None:
    assert classify_profile(score) == expected_profile

