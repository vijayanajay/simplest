"""Tests for reporting models."""

import pytest
from unittest.mock import Mock

from meqsap.reporting.models import ComparativeAnalysisResult
from meqsap.backtest import BacktestAnalysisResult


class TestComparativeAnalysisResult:
    """Test ComparativeAnalysisResult model."""
    
    @pytest.fixture
    def mock_candidate_result(self):
        """Mock candidate backtest result."""
        result = Mock(spec=BacktestAnalysisResult)
        result.total_return = 0.15
        result.sharpe_ratio = 1.2
        result.calmar_ratio = 0.8
        result.max_drawdown = -0.10
        return result
    
    @pytest.fixture
    def mock_baseline_result(self):
        """Mock baseline backtest result."""
        result = Mock(spec=BacktestAnalysisResult)
        result.total_return = 0.10
        result.sharpe_ratio = 0.9
        result.calmar_ratio = 0.6
        result.max_drawdown = -0.15
        return result
    
    def test_comparative_result_with_baseline(self, mock_candidate_result, mock_baseline_result):
        """Test comparative result with successful baseline."""
        result = ComparativeAnalysisResult(
            candidate_result=mock_candidate_result,
            baseline_result=mock_baseline_result,
            comparative_verdict="Outperformed"
        )
        
        assert result.has_baseline is True
        assert result.is_comparative is True
        assert result.comparative_verdict == "Outperformed"
        assert result.get_comparison_basis() == "Sharpe Ratio"
    
    def test_comparative_result_baseline_failed(self, mock_candidate_result):
        """Test comparative result with failed baseline."""
        result = ComparativeAnalysisResult(
            candidate_result=mock_candidate_result,
            baseline_failed=True,
            baseline_failure_reason="Data unavailable"
        )
        
        assert result.has_baseline is False
        assert result.is_comparative is False
        assert result.baseline_failed is True
        assert result.baseline_failure_reason == "Data unavailable"
    
    def test_comparative_result_no_baseline(self, mock_candidate_result):
        """Test result without baseline."""
        result = ComparativeAnalysisResult(
            candidate_result=mock_candidate_result
        )
        
        assert result.has_baseline is False
        assert result.is_comparative is False
        assert result.comparative_verdict is None
    
    def test_validation_baseline_failed_with_result(self, mock_candidate_result, mock_baseline_result):
        """Test validation when baseline_failed=True but baseline_result is provided."""
        with pytest.raises(ValueError, match="baseline_result should be None when baseline_failed is True"):
            ComparativeAnalysisResult(
                candidate_result=mock_candidate_result,
                baseline_result=mock_baseline_result,
                baseline_failed=True
            )
    
    def test_validation_verdict_without_baseline(self, mock_candidate_result):
        """Test validation when verdict is provided without baseline."""
        with pytest.raises(ValueError, match="comparative_verdict requires successful baseline_result"):
            ComparativeAnalysisResult(
                candidate_result=mock_candidate_result,
                comparative_verdict="Outperformed"
            )
    
    def test_format_verdict(self, mock_candidate_result, mock_baseline_result):
        """Test verdict formatting."""
        result = ComparativeAnalysisResult(
            candidate_result=mock_candidate_result,
            baseline_result=mock_baseline_result,
            comparative_verdict="Outperformed"
        )
        
        formatted = result.format_verdict()
        assert "Strategy Outperformed baseline" in formatted
        assert "Sharpe Ratio" in formatted
