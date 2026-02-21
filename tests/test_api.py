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
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


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


def test_image_and_audio_checks():
    client = setup_test_app()

    image_resp = client.post("/check/image", json={"description": "A nude scene with explicit content"})
    assert image_resp.status_code == 200
    assert image_resp.json()["safe"] is False

    audio_resp = client.post("/check/audio", json={"transcript": "podcast about gardening and weather"})
    assert audio_resp.status_code == 200
    assert audio_resp.json()["safe"] is True


def test_large_wordlist_detects_de_and_scam_terms():
    client = setup_test_app()
    resp = client.post(
        "/check/text",
        json={"text": "Das ist ein Anschlag und wir machen phishing-link betrug."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["safe"] is False
    assert "anschlag" in data["matched_terms"]
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
