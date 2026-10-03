from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.exporters import export_comic_pdf
from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_layout
from app.schemas import GenerationResponse, PromptRequest


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


def _run_pipeline(prompt_request: PromptRequest):
    """Outline -> story -> images -> layout -> PDF. Returns (panels, pdf_url)."""
    outline = generate_outline(
        prompt_request
    )

    story = generate_story(
        prompt_request,
        outline,
    )

    panels = []

    for panel in story:
        image_url = generate_image(
            panel.image_prompt,
            panel.panel_number,
        )

        panel_data = panel.model_copy(
            update={
                "image_url": image_url,
            },
        )

        panels.append(panel_data)

    layout = build_layout(panels)

    pdf_url = export_comic_pdf(
        panels
    )

    return panels, pdf_url


def _latest_pdf_url() -> str:
    """URL of the newest exported PDF, or an empty string if none exists."""
    export_dir = get_settings().output_dir / "exports"

    pdf_files = list(export_dir.glob("comic_*.pdf"))

    if not pdf_files:
        return ""

    newest = max(pdf_files, key=lambda path: path.stat().st_mtime)

    return f"/static/exports/{newest.name}"


@router.get(
    "/",
    response_class=HTMLResponse,
)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@router.post(
    "/generate",
    response_class=HTMLResponse,
)
async def generate_comic(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...),
):
    try:
        prompt_request = PromptRequest(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
        )

        panels, pdf_url = _run_pipeline(prompt_request)

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "panels": panels,
                "pdf_url": pdf_url,
            },
        )

    except Exception as exc:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": str(exc),
            },
            status_code=500,
        )


@router.post(
    "/generate-comic/json",
    response_model=GenerationResponse,
)
async def generate_comic_json(prompt_request: PromptRequest):
    """API version of /generate. Send JSON, get JSON back."""
    try:
        panels, pdf_url = _run_pipeline(prompt_request)

        return GenerationResponse(
            success=True,
            panels=panels,
            pdf_url=pdf_url,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get("/test-image")
async def test_image(
    prompt: str = "A futuristic city at sunset, sci-fi, cinematic",
):
    """Developer route: test image generation without making a full comic."""
    try:
        image_url = generate_image(prompt, 0)

        return {
            "message": "Image generated successfully",
            "image_url": image_url,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get(
    "/export-success",
    response_class=HTMLResponse,
)
async def export_success(request: Request, pdf_url: str = ""):
    # Only accept PDFs from our own exports folder.
    if not pdf_url.startswith("/static/exports/"):
        pdf_url = _latest_pdf_url()

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "pdf_url": pdf_url,
        },
    )


@router.get(
    "/export",
    response_class=HTMLResponse,
)
async def export_page(request: Request, pdf_url: str = ""):
    # Old URL kept so nothing that already uses /export breaks.
    return await export_success(request, pdf_url)