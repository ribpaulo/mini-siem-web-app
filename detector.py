"""Regelbasierte Erkennung verdächtiger SSH-Anmeldemuster."""

from collections import defaultdict

from models.analysis import DetectionFinding, EventType, SSHEvent


# Zentrale Schwellenwerte machen die Demo-Regeln transparent und anpassbar.
FAILED_IP_THRESHOLD = 5
IP_ATTEMPT_THRESHOLD = 10
USER_ATTEMPT_THRESHOLD = 6
FAILURES_BEFORE_SUCCESS_THRESHOLD = 3


def _capped_points(base: int, count: int, threshold: int, factor: int, cap: int) -> int:
    """Berechnet Basispunkte plus begrenzte Zusatzpunkte über dem Schwellenwert."""

    return min(base + max(0, count - threshold) * factor, cap)


def detect_threats(events: list[SSHEvent]) -> list[DetectionFinding]:
    """Wendet alle Demo-Erkennungsregeln auf die Ereignisse an."""

    findings: list[DetectionFinding] = []
    by_ip: dict[str, list[SSHEvent]] = defaultdict(list)
    by_user: dict[str, list[SSHEvent]] = defaultdict(list)

    for event in events:
        by_ip[event.ip_address].append(event)
        if event.username:
            by_user[event.username].append(event)

    for ip_address, ip_events in sorted(by_ip.items()):
        failures = [event for event in ip_events if event.event_type == EventType.FAILED_LOGIN]
        """Regel 1: Merfache Fehlversuche"""
        if len(failures) >= FAILED_IP_THRESHOLD:
            findings.append(
                DetectionFinding(
                    rule_id="FAILED_LOGINS_BY_IP",
                    title="Mehrfache fehlgeschlagene Logins",
                    description=(
                        f"{len(failures)} fehlgeschlagene Anmeldungen von {ip_address} "
                        f"(Schwelle: {FAILED_IP_THRESHOLD})."
                    ),
                    severity="hoch",
                    points=_capped_points(25, len(failures), FAILED_IP_THRESHOLD, 2, 40),
                    line_numbers=[event.line_number for event in failures],
                    ip_address=ip_address,
                )
            )

        """Regel 2: Viele Events derselben IP"""
        if len(ip_events) >= IP_ATTEMPT_THRESHOLD:
            findings.append(
                DetectionFinding(
                    rule_id="HIGH_IP_VOLUME",
                    title="Viele Versuche von derselben IP",
                    description=(
                        f"{len(ip_events)} Anmeldeereignisse von {ip_address} "
                        f"(Schwelle: {IP_ATTEMPT_THRESHOLD})."
                    ),
                    severity="mittel",
                    points=_capped_points(15, len(ip_events), IP_ATTEMPT_THRESHOLD, 1, 25),
                    line_numbers=[event.line_number for event in ip_events],
                    ip_address=ip_address,
                )
            )

        """RegeL 3: Erfolg nach Fehlversuchen"""
        previous_failures: list[SSHEvent] = []
        for event in ip_events:
            if event.event_type == EventType.FAILED_LOGIN:
                previous_failures.append(event)
                continue
            if len(previous_failures) >= FAILURES_BEFORE_SUCCESS_THRESHOLD:
                related = [*previous_failures, event]
                findings.append(
                    DetectionFinding(
                        rule_id="SUCCESS_AFTER_FAILURES",
                        title="Erfolgreicher Login nach Fehlversuchen",
                        description=(
                            f"Erfolgreiche Anmeldung von {ip_address} nach "
                            f"{len(previous_failures)} vorherigen Fehlversuchen."
                        ),
                        severity="kritisch",
                        points=30,
                        line_numbers=[item.line_number for item in related],
                        ip_address=ip_address,
                        username=event.username,
                    )
                )
                # Eine neue Sequenz beginnt nach einem erfolgreichen Login.
                previous_failures = []

    for username, user_events in sorted(by_user.items()):
        """Regel 4: Viele Versuche für einen Benutzer"""
        if len(user_events) < USER_ATTEMPT_THRESHOLD:
            continue
        failures = [event for event in user_events if event.event_type == EventType.FAILED_LOGIN]
        findings.append(
            DetectionFinding(
                rule_id="TARGETED_USER",
                title="Viele Versuche für denselben Benutzer",
                description=(
                    f"{len(user_events)} Anmeldeversuche für Benutzer {username} "
                    f"(davon {len(failures)} fehlgeschlagen; Schwelle: {USER_ATTEMPT_THRESHOLD})."
                ),
                severity="mittel",
                points=_capped_points(15, len(user_events), USER_ATTEMPT_THRESHOLD, 2, 25),
                line_numbers=[event.line_number for event in user_events],
                username=username,
            )
        )

    return findings
