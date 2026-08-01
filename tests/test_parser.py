from models.analysis import EventType
from parser import parse_line, parse_ssh_log


def test_parses_failed_and_successful_logins() -> None:
    content = "\n".join(
        [
            "Jul 31 09:12:10 host sshd[1]: Failed password for invalid user admin from 203.0.113.45 port 41101 ssh2",
            "Jul 31 09:12:20 host sshd[2]: Accepted publickey for deploy from 2001:db8::10 port 41102 ssh2",
            "Jul 31 09:12:30 host CRON[3]: unrelated message",
        ]
    )

    events = parse_ssh_log(content)

    assert len(events) == 2
    assert events[0].event_type == EventType.FAILED_LOGIN
    assert events[0].username == "admin"
    assert events[0].ip_address == "203.0.113.45"
    assert events[1].event_type == EventType.SUCCESSFUL_LOGIN
    assert events[1].authentication_method == "publickey"
    assert events[1].ip_address == "2001:db8::10"


def test_parses_iso_timestamp_and_rejects_invalid_ip() -> None:
    iso_line = (
        "2026-07-31T09:12:10+02:00 host sshd[1]: "
        "Invalid user guest from 198.51.100.10 port 40000"
    )
    bad_line = "Jul 31 09:12:10 host sshd[2]: Failed password for root from not-an-ip port 22 ssh2"

    assert parse_line(iso_line, 1) is not None
    assert parse_line(bad_line, 2) is None
