from datetime import datetime
from pathlib import Path

from fpdf import FPDF

from app.config import get_settings
from app.schemas import PanelStory

# The built-in PDF font only supports basic Latin characters.
# Gemini often returns curly quotes and long dashes, so we convert them.
_REPLACEMENTS = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2013": "-",
    "\u2014": "-",
    "\u2026": "...",
}


def _safe_text(text: str) -> str:
    for old, new in _REPLACEMENTS.items():
        text = text.replace(old, new)

    return text.encode("latin-1", "replace").decode("latin-1")


def export_comic_pdf(
    panels: list[PanelStory],
) -> str:
    settings = get_settings()

    export_dir = settings.output_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    pdf_name = f"comic_{timestamp}.pdf"
    pdf_path = export_dir / pdf_name

    pdf = FPDF()
    pdf.set_auto_page_break(
        auto=True,
        margin=15,
    )

    for panel in panels:
        pdf.add_page()

        pdf.set_font(
            "Helvetica",
            "B",
            18,
        )

        pdf.cell(
            0,
            12,
            _safe_text(f"Panel {panel.panel_number}: {panel.title}"),
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.ln(5)

        pdf.set_font(
            "Helvetica",
            "",
            12,
        )

        image_path = _image_path_from_url(
            panel.image_url
            if hasattr(panel, "image_url")
            else ""
        )

        if image_path and image_path.exists():
            pdf.image(
                str(image_path),
                x=15,
                w=180,
            )

            pdf.ln(8)

        pdf.multi_cell(
            0,
            8,
            _safe_text(panel.caption),
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.ln(4)

        pdf.multi_cell(
            0,
            8,
            _safe_text(panel.narration),
            new_x="LMARGIN",
            new_y="NEXT",
        )

    pdf.output(str(pdf_path))

    return f"/static/exports/{pdf_name}"


def _image_path_from_url(
    image_url: str,
) -> Path | None:

    if not image_url:
        return None

    if image_url.startswith("/static/"):
        relative_path = image_url.removeprefix(
            "/static/"
        )

        return get_settings().output_dir / relative_path

    return None