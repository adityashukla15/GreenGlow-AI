from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


WasteCategory = Literal["wet", "dry", "recyclable"]


class EcoSortEmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=5, max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Invalid email address")

        return value


class EcoSortWasteItem(BaseModel):
    id: int
    name: str
    description: str


class EcoSortGameStartResponse(BaseModel):
    session_token: str
    items: list[EcoSortWasteItem]


class EcoSortAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: int = Field(gt=0)
    selected_category: WasteCategory


class EcoSortSubmitRequest(EcoSortEmailRequest):
    session_token: str = Field(min_length=20, max_length=64)
    answers: list[EcoSortAnswer] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def validate_unique_item_ids(self):
        item_ids = [answer.item_id for answer in self.answers]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("Duplicate item IDs are not allowed")

        return self


class EcoSortAnswerResult(BaseModel):
    item_id: int
    selected_category: WasteCategory
    correct_category: WasteCategory
    is_correct: bool
    explanation: str


class EcoSortGameSubmitResponse(BaseModel):
    correct_answers: int
    total_items: int
    score_awarded: int
    total_score: int
    results: list[EcoSortAnswerResult]
