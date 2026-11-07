from pydantic import BaseModel, Field, field_validator, model_validator


class QuizQuestionResponse(BaseModel):
    id: int
    question: str
    options: list[str]
    category: str


class QuizAnswer(BaseModel):
    question_id: int = Field(gt=0)
    selected_option: int = Field(ge=0)


class QuizSubmitRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=255)
    answers: list[QuizAnswer] = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()

        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Invalid email address")

        return value

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Username cannot be empty")

        return value

    @model_validator(mode="after")
    def validate_unique_questions(self):
        question_ids = [
            answer.question_id for answer in self.answers
        ]

        if len(question_ids) != len(set(question_ids)):
            raise ValueError("Duplicate question IDs are not allowed")

        return self


class AnswerResult(BaseModel):
    question_id: int
    selected_option: int
    correct_option: int
    is_correct: bool
    explanation: str


class QuizSubmitResponse(BaseModel):
    username: str
    total_questions: int
    correct_answers: int
    incorrect_answers: int
    score: int
    results: list[AnswerResult]

class QuizSessionStartResponse(BaseModel):
    session_token: str
    questions: list[QuizQuestionResponse]


class QuizSessionSubmitRequest(QuizSubmitRequest):
    session_token: str = Field(min_length=36, max_length=36)

class QuizSessionStartRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()

        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Invalid email address")

        return value