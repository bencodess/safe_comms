from fastapi.testclient import TestClient

import main
from app.moderation import BAD_TERMS, BASE_TERMS_COUNT, OBFUSCATED_TERMS_COUNT


def setup_test_app():
    return TestClient(main.app)


def test_index_served():
    client = setup_test_app()
    resp = client.get("/")
    assert resp.status_code == 200
    assert "SafeComms Moderation API" in resp.text


def test_health_ok():
    client = setup_test_app()
    resp = client.get("/health/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_health_dashboard_and_metrics():
    client = setup_test_app()

    page = client.get("/health")
    assert page.status_code == 200
    assert "Safecomms API Health" in page.text

    metrics = client.get("/health/metrics")
    assert metrics.status_code == 200
    data = metrics.json()
    assert "uptime_seconds" in data
    assert "downtime_seconds" in data
    assert "last_response_ms" in data


def test_admin_verify_flow():
    client = setup_test_app()
    main.ADMIN_PASSWORD = "test-admin-pass"

    redir = client.get("/admin", follow_redirects=False)
    assert redir.status_code == 303
    assert redir.headers["location"] == "/admin-verify"

    login = client.post(
        "/admin-verify",
        data={"password": "test-admin-pass"},
        follow_redirects=False,
    )
    assert login.status_code == 303
    assert login.headers["location"] == "/admin"


def test_admin_error_report_resolve_delete():
    client = setup_test_app()
    main.ADMIN_PASSWORD = "test-admin-pass"

    login = client.post(
        "/admin-verify",
        data={"password": "test-admin-pass"},
        follow_redirects=False,
    )
    assert login.status_code == 303

    rep = client.post(
        "/admin/api/errors/report",
        json={"path": "/manual", "message": "manual issue"},
    )
    assert rep.status_code == 200
    rep_id = rep.json()["id"]

    resolved = client.post(
        f"/admin/api/errors/{rep_id}/resolve",
        json={"resolved_by": "admin"},
    )
    assert resolved.status_code == 200

    deleted = client.delete(f"/admin/api/errors/{rep_id}")
    assert deleted.status_code == 200

    listed = client.get("/admin/api/errors?include_resolved=true")
    assert listed.status_code == 200
    assert not any(e["id"] == rep_id for e in listed.json()["errors"])


def test_text_check_flags_unsafe():
    client = setup_test_app()
    resp = client.post("/check/text", json={"text": "I will kill and bomb this."})
    assert resp.status_code == 200
    data = resp.json()
    assert data["safe"] is False
    assert "kill" in data["matched_terms"]


def test_text_check_passes_clean():
    client = setup_test_app()
    resp = client.post("/check/text", json={"text": "hello team, have a nice day"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["safe"] is True
    assert data["matched_terms"] == []


def test_audio_check_passes_clean():
    client = setup_test_app()
    audio_resp = client.post("/check/audio", json={"transcript": "podcast about gardening and weather"})
    assert audio_resp.status_code == 200
    assert audio_resp.json()["safe"] is True


def test_large_wordlist_detects_de_and_scam_terms():
    client = setup_test_app()
    resp = client.post(
        "/check/text",
        json={"text": "This message mentions a terrorist plan and a phishing-link scam."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["safe"] is False
    assert "terrorist" in data["matched_terms"]
    assert "phishing link" in data["matched_terms"]


def test_hate_slur_detected():
    client = setup_test_app()
    resp = client.post("/check/text", json={"text": "that nigga is crazy"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["safe"] is False
    assert data["category"] == "hate"
    assert "nigga" in data["matched_terms"]


def test_pussy_detected():
    client = setup_test_app()
    resp = client.post("/check/text", json={"text": "you are a pussy"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["safe"] is False
    assert "pussy" in data["matched_terms"]


def test_wordlist_is_massive():
    total_terms = sum(len(values) for values in BAD_TERMS.values())
    assert BASE_TERMS_COUNT >= 10000
    assert OBFUSCATED_TERMS_COUNT >= 10000
    assert total_terms >= 20000


def test_obfuscated_term_detected():
    client = setup_test_app()
    resp = client.post("/check/text", json={"text": "you are a p.u.s.s.y"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["safe"] is False
