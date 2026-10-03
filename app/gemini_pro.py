import json
import re

from app.config import get_settings
from app.schemas import PanelOutline, PanelStory, PromptRequest


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


def _validate_story(items: list[PanelStory]) -> list[PanelStory]:
    if len(items) != 5:
        raise ValueError(
            f"Gemini returned {len(items)} story panels instead of 5. Please try again."
        )

    items = sorted(items, key=lambda panel: panel.panel_number)

    for number, panel in enumerate(items, start=1):
        panel.panel_number = number

    return items


def generate_story(
    request: PromptRequest,
    outline: list[PanelOutline],
) -> list[PanelStory]:

    settings = get_settings()

    if settings.use_mock_ai:
        return _mock_story(request, outline)

    from google import genai

    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is missing.")

    client = genai.Client(
        api_key=settings.gemini_api_key
    )

    outline_json = json.dumps(
        [item.model_dump() for item in outline],
        indent=2,
    )

    name = request.character_name
    she = request.pronoun_subject
    her = request.pronoun_possessive
    kid = "boy" if request.is_male else "girl"

    prompt = f"""
You are an award-winning comic book writer.
Turn this comic outline into a polished five-panel comic story.

MAIN CHARACTER:
{request.character_description}. Use the pronouns "{she}/{her}" for {name}.
Always call the character "{name}". Never write "the hero" or "the protagonist".

SETTING: {request.setting}
TONE: {request.tone}
ART STYLE: {request.art_style}

OUTLINE:
{outline_json}

RULES:
- Keep the same five panels, the same panel_number values and the same story events.
- The five panels must read as ONE connected story: each panel follows from the one before.
- caption: one short comic caption (max 12 words) specific to THIS panel.
- narration: 2 or 3 vivid sentences specific to THIS panel. Mention what {name} does, sees
  or feels in this exact scene, and use "{she}" and "{her}" correctly.
- Never reuse the same sentence in two panels and never write generic filler such as
  "the story continues".
- Keep scene_description as it is, or improve it slightly.
- Keep image_prompt as it is, but make sure it still describes {name} as a young
  {kid} with the same look in every panel.

Return ONLY valid JSON, no markdown.
Return exactly five objects. Each object must contain:
- panel_number
- title
- scene_description
- image_prompt
- caption
- narration
"""

    response = client.models.generate_content(
        model=settings.gemini_story_model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
        },
    )

    data = _extract_json(response.text)

    return _validate_story([PanelStory(**item) for item in data])


def _mock_story(
    request: PromptRequest,
    outline: list[PanelOutline],
) -> list[PanelStory]:

    name = request.character_name
    setting = request.setting
    she = request.pronoun_subject
    her = request.pronoun_possessive
    She = she.capitalize()
    idea = request.story_prompt.rstrip(".!? ")

    captions = [
        "The adventure begins.",
        f"{name} spots something strange.",
        "Trouble appears!",
        f"{name} has a plan.",
        "A happy ending.",
    ]

    narrations = [
        (
            f"{name} takes a deep breath at the edge of the {setting}. "
            f"{She} has waited for this moment, and {she} is ready to follow "
            f"{her} idea: {idea}."
        ),
        (
            f"Something unusual catches {name}'s eye. {She} moves closer, curious "
            f"and a little nervous, and realises this could change everything."
        ),
        (
            f"Suddenly things go wrong and the way forward is blocked. "
            f"{name} feels worried, but {she} refuses to give up."
        ),
        (
            f"{name} stops and thinks hard. {She} remembers what {she} noticed "
            f"earlier and turns it into a clever answer."
        ),
        (
            f"The trouble is gone and the {setting} is calm again. "
            f"{name} smiles proudly, knowing {she} did it with {her} own courage."
        ),
    ]

    result = []

    for item in outline:
        index = min(max(item.panel_number, 1), 5) - 1

        result.append(
            PanelStory(
                panel_number=item.panel_number,
                title=item.title,
                scene_description=item.scene_description,
                image_prompt=item.image_prompt,
                caption=captions[index],
                narration=narrations[index],
            )
        )

    return result