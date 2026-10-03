import base64
from datetime import datetime
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from app.config import get_settings


def generate_image(
    image_prompt: str,
    panel_number: int,
) -> str:

    settings = get_settings()

    panel_dir = settings.output_dir / "panels"
    panel_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d%H%M%S%f"
    )

    filename = (
        f"panel-{panel_number}-{timestamp}.png"
    )

    output_path = panel_dir / filename

    provider = _choose_provider(settings)

    if provider == "cloudflare":
        try:
            _generate_cloudflare_image(
                output_path,
                image_prompt,
                settings,
            )
        except Exception as exc:
            # Keep the app working: show a placeholder and explain in the terminal.
            print(
                f"[ComicCraft] Cloudflare image failed for panel "
                f"{panel_number}: {exc}. Using a placeholder image.",
                flush=True,
            )

            _create_placeholder(
                output_path,
                image_prompt,
                panel_number,
                settings.image_width,
                settings.image_height,
            )

    elif provider == "huggingface":
        _generate_huggingface_image(
            output_path,
            image_prompt,
            settings,
        )

    else:
        _create_placeholder(
            output_path,
            image_prompt,
            panel_number,
            settings.image_width,
            settings.image_height,
        )

    return f"/static/panels/{filename}"


def _choose_provider(settings) -> str:
    provider = settings.image_provider.strip().lower()

    if provider in ("mock", "cloudflare", "huggingface"):
        return provider

    # IMAGE_PROVIDER not set: behave exactly like before.
    return "mock" if settings.use_mock_ai else "huggingface"


def _create_placeholder(
    output_path: Path,
    prompt: str,
    panel_number: int,
    width: int,
    height: int,
) -> None:

    image = Image.new(
        "RGB",
        (width, height),
        "white",
    )

    draw = ImageDraw.Draw(image)

    draw.rectangle(
        [20, 20, width - 20, height - 20],
        outline="black",
        width=4,
    )

    text = (
        f"ComicCraft Panel {panel_number}\n\n"
        f"{prompt[:500]}"
    )

    draw.multiline_text(
        (50, 50),
        text,
        fill="black",
        spacing=10,
    )

    image.save(output_path)


def _generate_cloudflare_image(
    output_path: Path,
    prompt: str,
    settings,
) -> None:
    """Cloudflare Workers AI (FLUX.1 schnell). Needs account id + API token."""

    if not settings.cloudflare_account_id or not settings.cloudflare_api_token:
        raise RuntimeError(
            "CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN is missing in .env."
        )

    import httpx

    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        f"{settings.cloudflare_account_id}/ai/run/"
        f"{settings.cloudflare_image_model}"
    )

    headers = {
        "Authorization": f"Bearer {settings.cloudflare_api_token}",
    }

    payload = {
        # The model accepts a prompt of 1 to 2048 characters.
        "prompt": prompt[:2048],
        "steps": settings.cloudflare_image_steps,
    }

    response = httpx.post(
        url,
        headers=headers,
        json=payload,
        timeout=120,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"HTTP {response.status_code}: {response.text[:300]}"
        )

    content_type = response.headers.get("content-type", "")

    if "application/json" in content_type:
        data = response.json()

        image_b64 = (data.get("result") or {}).get("image")

        if not image_b64:
            raise RuntimeError(
                f"No image in response: {str(data)[:300]}"
            )

        image_bytes = base64.b64decode(image_b64)
    else:
        image_bytes = response.content

    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image.save(output_path)


def _generate_huggingface_image(
    output_path: Path,
    prompt: str,
    settings,
) -> None:

    if not settings.hf_api_key:
        raise RuntimeError(
            "HF_API_KEY is missing."
        )

    import httpx

    url = (
        "https://api-inference.huggingface.co/models/"
        f"{settings.hf_image_model}"
    )

    headers = {
        "Authorization": (
            f"Bearer {settings.hf_api_key}"
        ),
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "width": settings.image_width,
            "height": settings.image_height,
        },
    }

    response = httpx.post(
        url,
        headers=headers,
        json=payload,
        timeout=180,
    )

    response.raise_for_status()

    output_path.write_bytes(
        response.content
    )