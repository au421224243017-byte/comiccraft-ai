from typing import List

from pydantic import BaseModel, Field, field_validator


class PromptRequest(BaseModel):
    story_prompt: str = Field(..., min_length=3, max_length=2000)
    character_name: str = Field(..., min_length=1, max_length=80)
    setting: str = Field(..., min_length=1, max_length=120)
    tone: str = Field(..., min_length=1, max_length=60)
    art_style: str = Field(..., min_length=1, max_length=80)
    # New: defaults to "female" so existing routes and tests keep working.
    character_gender: str = Field(default="female", max_length=20)

    @field_validator("*")
    @classmethod
    def strip_values(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Values cannot be empty.")

        return value

    @property
    def is_male(self) -> bool:
        return self.character_gender.strip().lower() in ("male", "boy", "man", "he")

    @property
    def pronoun_subject(self) -> str:
        return "he" if self.is_male else "she"

    @property
    def pronoun_possessive(self) -> str:
        return "his" if self.is_male else "her"

    @property
    def character_description(self) -> str:
        """Example: 'Princy is a young girl'"""
        noun = "boy" if self.is_male else "girl"
        return f"{self.character_name} is a young {noun}"


class PanelOutline(BaseModel):
    panel_number: int
    title: str
    scene_description: str
    image_prompt: str


class PanelStory(BaseModel):
    panel_number: int
    title: str
    scene_description: str
    image_prompt: str
    caption: str
    narration: str
    image_url: str = ""


class ComicLayout(BaseModel):
    panels: List[PanelStory]
    pdf_path: str | None = None


class GenerationResponse(BaseModel):
    success: bool
    panels: List[PanelStory]
    pdf_url: str