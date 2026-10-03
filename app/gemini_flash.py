import json
import re

from app.config import get_settings
from app.schemas import PanelOutline, PromptRequest


def _extract_json(text: str):
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text)
        text = re.sub(r"```$", "", text)
        text = text.strip()

    match = re.search(r"\[.*\]", text, re.DOTALL)

    if match:
        text = match.group(0)

    return json.loads(text)


def _validate_outline(items: list[PanelOutline]) -> list[PanelOutline]:
    if len(items) != 5:
        raise ValueError(
            f"Gemini returned {len(items)} panels instead of 5. Please try again."
        )

    items = sorted(items, key=lambda panel: panel.panel_number)

    for number, panel in enumerate(items, start=1):
        panel.panel_number = number

    return items


def generate_outline(request: PromptRequest) -> list[PanelOutline]:
    settings = get_settings()

    if settings.use_mock_ai:
        return _mock_outline(request)

    from google import genai

    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is missing.")

    client = genai.Client(
        api_key=settings.gemini_api_key
    )

    name = request.character_name
    she = request.pronoun_subject
    her = request.pronoun_possessive

    prompt = f"""
You are a professional comic book story planner.
Plan a complete five-panel comic with a clear beginning, middle and ending.

STORY IDEA:
{request.story_prompt}

MAIN CHARACTER:
{request.character_description}. Use the pronouns "{she}/{her}" for {name}.
Always call the character "{name}". Never call {name} "the hero" or "the protagonist".

SETTING: {request.setting}
TONE: {request.tone}
ART STYLE: {request.art_style}

STORY STRUCTURE (every panel must be clearly different and must follow from the previous one):
- Panel 1 - Beginning: introduce {name} in the setting and what {she} wants.
- Panel 2 - Discovery: {name} finds something surprising connected to the story idea.
- Panel 3 - Problem: something goes wrong and blocks {her} goal.
- Panel 4 - Solution: {name} solves the problem in a clever, specific way.
- Panel 5 - Ending: the result of the solution and how {name} feels.

RULES:
- scene_description: 2 short sentences describing exactly what happens and what is visible.
- image_prompt: one detailed visual description for an image generator.
  First invent ONE fixed look for {name} (hair, clothes, one accessory) and repeat that
  exact same look in all five image_prompts so {she} looks identical in every panel.
  Include the setting, the action, the mood ({request.tone}) and the art style ({request.art_style}).
  Do not ask for text, speech bubbles or lettering in the image.
- Do not repeat the same scene or sentence in different panels.

Return ONLY valid JSON, no markdown.
Return exactly five objects. Each object must contain:
- panel_number (integer 1 to 5)
- title (short)
- scene_description
- image_prompt
"""

    response = client.models.generate_content(
        model=settings.gemini_outline_model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
        },
    )

    data = _extract_json(response.text)

    return _validate_outline([PanelOutline(**item) for item in data])


def _mock_look(request: PromptRequest) -> str:
    name = request.character_name

    if request.is_male:
        return f"{name}, a young boy with short brown hair and a blue jacket"

    return f"{name}, a young girl with long braided hair and a yellow jacket"


def _mock_outline(
    request: PromptRequest,
) -> list[PanelOutline]:

    name = request.character_name
    setting = request.setting
    she = request.pronoun_subject
    her = request.pronoun_possessive
    idea = request.story_prompt.rstrip(".!? ")
    look = _mock_look(request)
    extra = f"{request.tone} mood, {request.art_style}, comic panel, no text"

    return [
        PanelOutline(
            panel_number=1,
            title="The Beginning",
            scene_description=(
                f"{name} stands at the edge of the {setting}, ready to begin "
                f"{her} adventure: {idea}. {she.capitalize()} looks ahead with determination."
            ),
            image_prompt=(
                f"{look}, standing at the entrance of the {setting}, "
                f"looking ahead with determination, wide establishing shot, {extra}"
            ),
        ),
        PanelOutline(
            panel_number=2,
            title="A Strange Discovery",
            scene_description=(
                f"While exploring, {name} notices something unusual connected to "
                f"{her} adventure. {she.capitalize()} kneels down to look closer, "
                f"curious and a little nervous."
            ),
            image_prompt=(
                f"{look}, kneeling to examine a mysterious glowing object in the "
                f"{setting}, curious expression, close-up shot, {extra}"
            ),
        ),
        PanelOutline(
            panel_number=3,
            title="The Problem",
            scene_description=(
                f"The discovery causes trouble and blocks {her} way. "
                f"{name} realises {she} cannot go forward without a new plan."
            ),
            image_prompt=(
                f"{look}, facing a big obstacle in the {setting}, worried expression, "
                f"dramatic angle, {extra}"
            ),
        ),
        PanelOutline(
            panel_number=4,
            title="The Solution",
            scene_description=(
                f"{name} thinks carefully and uses what {she} noticed earlier. "
                f"{she.capitalize()} finds a clever way to fix the problem."
            ),
            image_prompt=(
                f"{look}, solving the problem with a clever idea in the {setting}, "
                f"confident expression, dynamic action shot, {extra}"
            ),
        ),
        PanelOutline(
            panel_number=5,
            title="The Ending",
            scene_description=(
                f"The problem is solved and the {setting} is calm again. "
                f"{name} smiles proudly at what {she} has achieved."
            ),
            image_prompt=(
                f"{look}, smiling proudly in the {setting} after succeeding, "
                f"warm light, happy ending, wide shot, {extra}"
            ),
        ),
    ]