from pathlib import Path

from app.services.hybrid_analysis import HybridAnalysisService


SAMPLE_DATA = Path("sample_data")


def test_hybrid_analysis_counts_high_risk_attribution_renewals() -> None:
    service = HybridAnalysisService()

    result = service.count_high_risk_attribution_renewals(
        path=SAMPLE_DATA / "renewals.xlsx",
        question="How many high-risk renewals mention attribution issues?",
    )

    assert result.route == "hybrid"
    assert result.result == 3
    assert "deterministic pandas" in result.explanation
