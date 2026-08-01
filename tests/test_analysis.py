from pathlib import Path

from service import analyze_log


SAMPLE_FILE = Path(__file__).parents[1] / "examples" / "sample_auth.log"


def test_sample_log_triggers_expected_rules() -> None:
    result = analyze_log(SAMPLE_FILE.read_text(encoding="utf-8"), SAMPLE_FILE.name)
    rule_ids = {finding.rule_id for finding in result.findings}

    assert result.total_lines == 19
    assert result.parsed_events == 18
    assert result.failed_logins == 15
    assert result.successful_logins == 3
    assert result.risk_score == 100
    assert result.risk_level == "KRITISCH"
    assert result.alert is True
    assert {
        "FAILED_LOGINS_BY_IP",
        "HIGH_IP_VOLUME",
        "TARGETED_USER",
        "SUCCESS_AFTER_FAILURES",
    } <= rule_ids
    assert {item.value for item in result.suspicious_ips} == {
        "203.0.113.45",
        "198.51.100.77",
    }
    assert len(result.marked_lines) == 16


def test_benign_log_has_low_risk() -> None:
    content = "Jul 31 10:00:00 host sshd[1]: Accepted publickey for deploy from 10.0.0.10 port 50000 ssh2"

    result = analyze_log(content, "benign.log")

    assert result.risk_score == 0
    assert result.risk_level == "NIEDRIG"
    assert result.alert is False
    assert result.suspicious_ips == []
    assert result.marked_lines == []
