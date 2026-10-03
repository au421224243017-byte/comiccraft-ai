from app.schemas import ComicLayout, PanelStory


def build_layout(
    panels: list[PanelStory],
) -> ComicLayout:
    """
    Build the final comic layout from generated panel stories.
    """

    ordered_panels = sorted(
        panels,
        key=lambda panel: panel.panel_number,
    )

    return ComicLayout(
        panels=ordered_panels,
        pdf_path=None,
    )