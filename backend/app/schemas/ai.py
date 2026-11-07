from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssistantPreferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    budget: str | None = Field(default=None, max_length=80)
    interests: list[str] | None = Field(default=None, max_length=10)
    decoration_interests: list[str] | None = Field(default=None, max_length=10)
    celebration_style: str | None = Field(default=None, max_length=120)

    @field_validator("budget", "celebration_style")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        if not value:
            raise ValueError("Text cannot be empty")

        return value

    @field_validator("interests", "decoration_interests")
    @classmethod
    def validate_optional_lists(
        cls,
        values: list[str] | None,
    ) -> list[str] | None:
        if values is None:
            return None

        cleaned = [value.strip() for value in values]
        if any(not value or len(value) > 100 for value in cleaned):
            raise ValueError("Each item must contain 1 to 100 characters")

        return cleaned


class AssistantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=2000)
    preferences: AssistantPreferences | None = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be empty")

        return value


class AssistantResponse(BaseModel):
    reply: str
    provider: str = "groq"


class GeneratedQuizQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=10, max_length=500)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_answer: int = Field(ge=0, le=3)
    explanation: str = Field(min_length=10, max_length=1000)
    category: str = Field(min_length=2, max_length=100)

    @field_validator("question", "explanation", "category")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Text cannot be empty")

        return value

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: list[str]) -> list[str]:
        cleaned = [option.strip() for option in value]

        if any(not option for option in cleaned):
            raise ValueError("Options cannot be empty")

        if len({option.casefold() for option in cleaned}) != 4:
            raise ValueError("All four options must be unique")

        return cleaned


class GeneratedQuizContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questions: list[GeneratedQuizQuestion] = Field(
        min_length=10,
        max_length=10
    )


class GeneratedChallenge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=5, max_length=150)
    description: str = Field(min_length=10, max_length=1000)

    @field_validator("title", "description")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Text cannot be empty")

        return value


class GeneratedChallengeContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    challenges: list[GeneratedChallenge] = Field(
        min_length=3,
        max_length=5
    )