from pydantic import BaseModel, Field, field_validator


class ChallengeCompleteRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()

        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Invalid email address")

        return value


class ChallengeResponse(BaseModel):
    id: int
    title: str
    description: str
    points: int


class ChallengeCompleteResponse(BaseModel):
    message: str
    challenge_title: str
    points_awarded: int
    total_score: int


class ChallengeCompletionStatusResponse(BaseModel):
    profile_exists: bool
    completed_challenge_ids: list[int]
