"""Tests for RevisitPredictionService risk score calculation."""

import pytest

from app.services.revisit_prediction_service import RevisitPredictionService


class TestRiskScoreCalculation:
    """Test the static _calculate_risk_score method."""

    def test_high_risk_overdue_single_visit_no_intent(self):
        """Customer way overdue, single visit, said won't return → max risk."""
        score = RevisitPredictionService._calculate_risk_score(
            days_since_last_visit=200,
            expected_revisit_days=90,
            visit_count=1,
            revisit_intention="no",
            total_payments=100000,
        )
        # overdue_ratio = 200/90 ≈ 2.2 → 40pts
        # visit_count = 1 → 20pts
        # revisit_intention = "no" → 25pts
        # recency = 200 > 180 → 10pts (15 requires 365+)
        assert score >= 90
        assert score <= 100

    def test_low_risk_loyal_customer(self):
        """Frequent visitor, recently visited, says will return → low risk."""
        score = RevisitPredictionService._calculate_risk_score(
            days_since_last_visit=15,
            expected_revisit_days=90,
            visit_count=10,
            revisit_intention="yes",
            total_payments=5000000,
        )
        # overdue_ratio = 15/90 ≈ 0.17 → 0pts
        # visit_count = 10 → 0pts
        # revisit_intention = "yes" → 0pts
        # recency = 15 → 0pts
        assert score == 0

    def test_medium_risk_approaching_due(self):
        """Approaching revisit deadline, moderate visit count."""
        score = RevisitPredictionService._calculate_risk_score(
            days_since_last_visit=80,
            expected_revisit_days=90,
            visit_count=2,
            revisit_intention="maybe",
            total_payments=300000,
        )
        # overdue_ratio = 80/90 ≈ 0.89 → 10pts
        # visit_count = 2 → 12pts
        # revisit_intention = "maybe" → 12pts
        # recency = 80 → 0pts
        assert score == 34

    def test_no_interval_data_uses_default(self):
        """No procedure interval → uses 90-day default."""
        score = RevisitPredictionService._calculate_risk_score(
            days_since_last_visit=100,
            expected_revisit_days=None,
            visit_count=3,
            revisit_intention=None,
            total_payments=200000,
        )
        # default 90-day: 100 > 90 → 20pts
        # visit_count = 3 → 5pts
        # revisit_intention = None → 8pts
        # recency = 100 > 90 → 5pts
        assert score == 38

    def test_unknown_revisit_intention_some_risk(self):
        """Unknown intention = 8 points of risk."""
        score = RevisitPredictionService._calculate_risk_score(
            days_since_last_visit=10,
            expected_revisit_days=90,
            visit_count=5,
            revisit_intention=None,
            total_payments=100000,
        )
        # overdue: 0, visit: 0 (5+), revisit: 8, recency: 0
        assert score == 8

    def test_score_capped_at_100(self):
        """Score should never exceed 100."""
        score = RevisitPredictionService._calculate_risk_score(
            days_since_last_visit=400,
            expected_revisit_days=30,
            visit_count=1,
            revisit_intention="no",
            total_payments=50000,
        )
        assert score <= 100


class TestRiskLevel:
    def test_critical(self):
        assert RevisitPredictionService._risk_level(75) == "critical"
        assert RevisitPredictionService._risk_level(100) == "critical"

    def test_high(self):
        assert RevisitPredictionService._risk_level(50) == "high"
        assert RevisitPredictionService._risk_level(74) == "high"

    def test_medium(self):
        assert RevisitPredictionService._risk_level(30) == "medium"
        assert RevisitPredictionService._risk_level(49) == "medium"

    def test_low(self):
        assert RevisitPredictionService._risk_level(0) == "low"
        assert RevisitPredictionService._risk_level(29) == "low"
