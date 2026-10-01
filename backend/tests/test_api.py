from fastapi.testclient import TestClient

from th_trainer.api import create_app


def test_sessions_persist_and_inputs_are_validated(tmp_path):
    database = tmp_path / "trainer.sqlite3"

    with TestClient(create_app(database)) as client:
        assert client.get("/api/health").json() == {"status": "ok"}
        invalid = client.post(
            "/api/sessions",
            json={"seats": 7, "assistance_mode": "assisted"},
        )
        assert invalid.status_code == 422

        created = client.post(
            "/api/sessions",
            json={"seats": 2, "assistance_mode": "unassisted"},
        )
        assert created.status_code == 201
        session = created.json()
        assert session["seats"] == 2
        assert client.get(f"/api/sessions/{session['id']}").json() == session

    with TestClient(create_app(database)) as client:
        assert client.get("/api/sessions").json() == [session]
        assert client.get("/api/sessions/unknown").status_code == 404


def test_hands_persist_hide_private_state_and_reject_duplicate_actions(tmp_path):
    database = tmp_path / "trainer.sqlite3"
    with TestClient(create_app(database)) as client:
        assert client.post("/api/hands", json={"dealer": 2}).status_code == 422
        response = client.post("/api/hands", json={})
        assert response.status_code == 201
        hand = response.json()
        assert hand.pop("playback")[0]["kind"] == "setup"
        assert hand["players"][1]["cards"] == [None, None]
        assert "deck" not in hand and "burned" not in hand
        hand_id = hand["id"]
        action_url = f"/api/hands/{hand_id}/actions"
        assert client.post(action_url, json={"action": "check", "revision": 0}).status_code == 422
        assert client.get(f"/api/hands/{hand_id}").json() == hand
        response = client.post(action_url, json={"action": "call", "revision": 0})
        hand = response.json()
        frames = hand.pop("playback")
        assert [frame["kind"] for frame in frames] == ["call", "check", "deal", "check"]
        assert [frame["hand"]["street"] for frame in frames] == ["preflop", "preflop", "flop", "flop"]
        assert frames[0]["hand"]["pot"] == 4
        assert frames[1]["hand"]["board"] == []
        assert all(frame["hand"]["players"][1]["cards"] == [None, None] for frame in frames)
        assert hand["street"] == "flop" and hand["actor"] == 0
        assert client.post(action_url, json={"action": "call", "revision": 0}).status_code == 409
    with TestClient(create_app(database)) as client:
        assert client.get(f"/api/hands/{hand_id}").json() == hand
        result = client.post(action_url, json={"action": "raise", "raise_to": 198, "revision": 1}).json()
        assert result["result"]["reason"] == "showdown"
        assert all(card is not None for card in result["players"][1]["cards"])
        assert sum(p["stack"] for p in result["players"]) == 400


def test_migration_preserves_old_configuration(tmp_path):
    import sqlite3

    database = tmp_path / "v1.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.executescript("""
            CREATE TABLE sessions (id TEXT PRIMARY KEY, created_at TEXT, seats INTEGER, assistance_mode TEXT);
            INSERT INTO sessions VALUES ('old', '2026-01-01', 2, 'unassisted');
            PRAGMA user_version = 1;
        """)
    with TestClient(create_app(database)) as client:
        assert client.get('/api/sessions/old').json()['seats'] == 2
        assert client.post('/api/hands', json={}).status_code == 201


def test_playback_preserves_bot_turns_and_all_in_runout(tmp_path):
    with TestClient(create_app(tmp_path / "trainer.sqlite3")) as client:
        initial = client.post('/api/hands', json={"dealer": 1}).json()
        frames = initial["playback"]
        assert [frame["kind"] for frame in frames] == ["setup", "call"]
        assert frames[0]["hand"]["actor"] == 1
        assert frames[0]["hand"]["pot"] == 3
        assert frames[0]["hand"]["history"][-1]["action"] == "BB"
        assert initial["actor"] == 0
        result = client.post(f'/api/hands/{initial["id"]}/actions', json={
            "action": "raise", "raise_to": 200, "revision": 0,
        }).json()
        frames = result["playback"]
        assert [frame["kind"] for frame in frames] == ["raise", "call", "deal", "deal", "deal", "award"]
        assert [len(frame["hand"]["board"]) for frame in frames] == [0, 0, 3, 4, 5, 5]
        assert all(frame["hand"]["players"][1]["cards"] == [None, None] for frame in frames[:-1])
        assert all(card is not None for card in frames[-1]["hand"]["players"][1]["cards"])
        assert frames[-1]["hand"]["result"] == result["result"]
