import asyncio

import httpx

from main import app


async def _request(method: str, url: str, **kwargs: object) -> httpx.Response:
    """Sendet Testanfragen direkt an die ASGI-App, ohne einen Netzwerkserver."""

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.request(method, url, **kwargs)


def test_start_page_is_available() -> None:
    response = asyncio.run(_request("GET", "/"))

    assert response.status_code == 200
    assert "SSH-Logdatei hochladen" in response.text


def test_json_analysis_endpoint() -> None:
    line = "Jul 31 10:00:00 host sshd[1]: Accepted publickey for deploy from 10.0.0.10 port 50000 ssh2"

    response = asyncio.run(_request(
        "POST",
        "/api/analyze",
        files={"log_file": ("auth.log", line.encode("utf-8"), "text/plain")},
    ))

    assert response.status_code == 200
    assert response.json()["parsed_events"] == 1
    assert response.json()["risk_score"] == 0


def test_html_analysis_page_contains_result() -> None:
    line = "Jul 31 10:00:00 host sshd[1]: Accepted password for demo from 10.0.0.11 port 50001 ssh2"

    response = asyncio.run(_request(
        "POST",
        "/analyze",
        files={"log_file": ("demo.log", line.encode("utf-8"), "text/plain")},
    ))

    assert response.status_code == 200
    assert "Analyse abgeschlossen" in response.text
    assert "demo.log" in response.text


def test_rejects_wrong_file_extension() -> None:
    response = asyncio.run(_request(
        "POST",
        "/api/analyze",
        files={"log_file": ("auth.csv", b"data", "text/csv")},
    ))

    assert response.status_code == 400
