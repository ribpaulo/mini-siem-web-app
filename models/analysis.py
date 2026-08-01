"""Pydantic-Modelle für Parser-, Detektor- und API-Ergebnisse."""

from enum import Enum

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Unterstützte Arten von SSH-Authentifizierungsereignissen."""

    FAILED_LOGIN = "failed_login"
    SUCCESSFUL_LOGIN = "successful_login"


class SSHEvent(BaseModel):
    """Ein aus einer Logzeile extrahiertes SSH-Ereignis."""

    line_number: int
    raw_line: str
    timestamp: str | None = None
    hostname: str | None = None
    event_type: EventType
    ip_address: str
    username: str | None = None
    authentication_method: str | None = None


class DetectionFinding(BaseModel):
    """Ein einzelner, durch eine Regel ausgelöster Fund."""

    rule_id: str
    title: str
    description: str
    severity: str
    points: int = Field(ge=0)
    line_numbers: list[int] = Field(default_factory=list)
    ip_address: str | None = None
    username: str | None = None


class EntitySummary(BaseModel):
    """Zusammenfassung der Aktivität einer IP-Adresse oder eines Benutzers."""

    value: str
    attempts: int
    failed_attempts: int
    successful_attempts: int
    reasons: list[str] = Field(default_factory=list)


class MarkedLogLine(BaseModel):
    """Originalzeile mit den Gründen für ihre Markierung."""

    line_number: int
    content: str
    reasons: list[str]


class RiskBreakdown(BaseModel):
    """Punkteanteil pro ausgelöster Erkennungsregel."""

    rule_id: str
    label: str
    points: int


class AnalysisResult(BaseModel):
    """Vollständiges Resultat einer Logdatei-Analyse."""

    filename: str
    total_lines: int
    parsed_events: int
    failed_logins: int
    successful_logins: int
    risk_score: int = Field(ge=0, le=100)
    risk_level: str
    alert: bool
    suspicious_ips: list[EntitySummary] = Field(default_factory=list)
    suspicious_users: list[EntitySummary] = Field(default_factory=list)
    findings: list[DetectionFinding] = Field(default_factory=list)
    score_breakdown: list[RiskBreakdown] = Field(default_factory=list)
    marked_lines: list[MarkedLogLine] = Field(default_factory=list)
