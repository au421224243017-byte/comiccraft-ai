# ComicCraft AI

AI comic story creator. Enter a story idea, character, setting, tone and art style.
The app generates a five-panel comic outline, a story, panel images, a browser preview and a PDF.

Built with FastAPI, Gemini (text), Cloudflare Workers AI FLUX (images) and fpdf2 (PDF).

## Run locally (Windows)
1. python -m venv .venv
2. .venv\Scripts\activate
3. pip install -r requirements.txt
4. Copy .env.example to .env and add your own keys
5. python -m uvicorn app.main:app --reload
6. Open http://127.0.0.1:8000

## Test
python -m pytest