"""Datenmodelle der Mini-SIEM-Anwendung."""

from .analysis import (
    AnalysisResult,
    DetectionFinding,
    EntitySummary,
    MarkedLogLine,
    RiskBreakdown,
    SSHEvent,
)

__all__ = [
    "AnalysisResult",
    "DetectionFinding",
    "EntitySummary",
    "MarkedLogLine",
    "RiskBreakdown",
    "SSHEvent",
]
