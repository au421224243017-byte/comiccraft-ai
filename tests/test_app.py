from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_homepage():
    response = client.get("/")

    assert response.status_code == 200
    assert "ComicCraft AI" in response.text


def test_generate_comic():
    response = client.post(
        "/generate",
        data={
            "story_prompt": "A young hero discovers a secret machine.",
            "character_name": "Arjun",
            "setting": "Chennai",
            "tone": "Funny and adventurous",
            "art_style": "Colorful comic book",
        },
    )

    assert response.status_code == 200
    assert "Your Comic Is Ready" in response.text