import { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Check,
  Leaf,
  RefreshCw,
  Trophy,
  X,
} from "lucide-react";
import { Link } from "react-router-dom";
import { ApiError, request } from "../services/api.js";
import { endpoints } from "../services/endpoints.js";
import { useUser } from "../context/UserContext.jsx";

function getSubmissionError(error) {
  if (!(error instanceof ApiError)) {
    return "Your answers could not be submitted. Check your connection and try again.";
  }

  if (error.status === 403) {
    return "This quiz session is not associated with the selected email. Start a new quiz using the same email.";
  }
  if (error.status === 404) {
    return "This quiz session could not be found. Start a new quiz to continue.";
  }
  if (error.status === 409) {
    return "This session may already have been submitted, or that display name is already in use. Try another name, or start a new quiz.";
  }
  if (error.status === 422) {
    return "The answers were not accepted. Check that every question has an answer, then try again.";
  }

  return error.message;
}

function LoadingPanel({ message }) {
  return (
    <div className="quiz-state" role="status">
      <span className="dashboard-spinner" aria-hidden="true" />
      <p>{message}</p>
    </div>
  );
}

function QuizError({ message, onRestart }) {
  return (
    <section className="quiz-state quiz-error-panel" role="alert">
      <AlertCircle size={23} aria-hidden="true" />
      <h2>We couldn’t prepare your quiz</h2>
      <p>{message}</p>
      <div className="quiz-actions">
        <button className="button button-primary" onClick={onRestart}>
          <RefreshCw size={16} aria-hidden="true" />
          Try again
        </button>
        <Link className="button button-quiet" to="/dashboard">
          <ArrowLeft size={16} aria-hidden="true" />
          Back to dashboard
        </Link>
      </div>
    </section>
  );
}

export function QuizPage() {
  const { email } = useUser();
  const [quizState, setQuizState] = useState({ status: "loading" });
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [username, setUsername] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [retryCount, setRetryCount] = useState(0);
  const submitLock = useRef(false);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    async function prepareQuiz() {
      setQuizState({ status: "loading" });
      setCurrentIndex(0);
      setAnswers({});
      setSubmitError("");
      submitLock.current = false;

      try {
        const availableQuestions = await request(endpoints.quizQuestions, {
          signal: controller.signal,
        });
        if (!Array.isArray(availableQuestions)) {
          throw new Error("The quiz questions response was invalid.");
        }

        if (!active) {
          return;
        }
        setQuizState({ status: "starting" });

        const session = await request(endpoints.quizSessionStart, {
          method: "POST",
          body: { email },
          signal: controller.signal,
        });

        if (!active) {
          return;
        }
        if (
          typeof session?.session_token !== "string" ||
          !Array.isArray(session.questions)
        ) {
          throw new Error("The quiz session response was invalid.");
        }

        if (session.questions.length === 0) {
          setQuizState({ status: "empty" });
          return;
        }

        setQuizState({
          status: "active",
          sessionToken: session.session_token,
          questions: session.questions,
        });
      } catch (error) {
        if (!active || error.name === "AbortError") {
          return;
        }

        const message =
          error instanceof ApiError
            ? error.status === 503
              ? "Ten fresh questions aren’t available right now. Please try again later."
              : error.message
            : "The quiz response was incomplete. Please try again.";
        setQuizState({ status: "error", message });
      }
    }

    prepareQuiz();
    return () => {
      active = false;
      controller.abort();
    };
  }, [email, retryCount]);

  function restartQuiz() {
    setRetryCount((count) => count + 1);
  }

  function selectAnswer(questionId, optionIndex) {
    setAnswers((currentAnswers) => ({
      ...currentAnswers,
      [questionId]: optionIndex,
    }));
    setSubmitError("");
  }

  async function submitQuiz(event) {
    event.preventDefault();
    if (
      quizState.status !== "active" ||
      submitLock.current ||
      username.trim().length < 3 ||
      username.trim().length > 50
    ) {
      return;
    }

    const completeAnswers = quizState.questions.every(
      (question) => Number.isInteger(answers[question.id]),
    );
    if (!completeAnswers) {
      setSubmitError("Please select an answer for every question.");
      return;
    }

    submitLock.current = true;
    setSubmitError("");
    setQuizState((current) => ({ ...current, status: "submitting" }));

    try {
      const result = await request(endpoints.quizSessionSubmit, {
        method: "POST",
        body: {
          session_token: quizState.sessionToken,
          username: username.trim(),
          email,
          answers: quizState.questions.map((question) => ({
            question_id: question.id,
            selected_option: answers[question.id],
          })),
        },
      });

      setQuizState({ status: "result", questions: quizState.questions, result });
    } catch (error) {
      submitLock.current = false;
      if (error instanceof ApiError && [403, 404].includes(error.status)) {
        setQuizState({
          status: "error",
          message: getSubmissionError(error),
        });
        return;
      }

      setQuizState((current) => ({ ...current, status: "active" }));
      setSubmitError(getSubmissionError(error));
    }
  }

  return (
    <main className="quiz-page">
      <header className="quiz-heading">
        <p className="eyebrow">
          <Leaf size={14} aria-hidden="true" />
          Green Quiz
        </p>
        <h1>Small choices, greener celebrations.</h1>
        <p>
          Explore practical ideas for a more thoughtful Diwali. Your email
          identifies your profile; it does not authenticate you.
        </p>
      </header>

      {quizState.status === "loading" && (
        <LoadingPanel message="Loading available questions…" />
      )}
      {quizState.status === "starting" && (
        <LoadingPanel message="Preparing your 10-question quiz…" />
      )}
      {quizState.status === "submitting" && (
        <LoadingPanel message="Submitting your answers…" />
      )}
      {quizState.status === "error" && (
        <QuizError message={quizState.message} onRestart={restartQuiz} />
      )}
      {quizState.status === "empty" && (
        <section className="quiz-state">
          <AlertCircle size={23} aria-hidden="true" />
          <h2>No questions are available</h2>
          <p>Please try again later.</p>
          <button className="button button-primary" onClick={restartQuiz}>
            <RefreshCw size={16} aria-hidden="true" />
            Try again
          </button>
        </section>
      )}

      {quizState.status === "active" && (
        <form className="quiz-card" onSubmit={submitQuiz}>
          <div className="quiz-progress-heading">
            <span>
              Question {currentIndex + 1} of {quizState.questions.length}
            </span>
            <span>{quizState.questions[currentIndex].category}</span>
          </div>
          <div
            className="quiz-progress-track"
            role="progressbar"
            aria-label="Quiz progress"
            aria-valuemin={1}
            aria-valuemax={quizState.questions.length}
            aria-valuenow={currentIndex + 1}
          >
            <span
              style={{
                width: `${((currentIndex + 1) / quizState.questions.length) * 100}%`,
              }}
            />
          </div>

          <fieldset className="quiz-question">
            <legend>{quizState.questions[currentIndex].question}</legend>
            <div className="quiz-options">
              {quizState.questions[currentIndex].options.map(
                (option, optionIndex) => {
                  const questionId = quizState.questions[currentIndex].id;
                  const selected = answers[questionId] === optionIndex;
                  return (
                    <label
                      className={`quiz-option${selected ? " quiz-option-selected" : ""}`}
                      key={`${questionId}-${optionIndex}`}
                    >
                      <input
                        type="radio"
                        name={`question-${questionId}`}
                        value={optionIndex}
                        checked={selected}
                        onChange={() => selectAnswer(questionId, optionIndex)}
                      />
                      <span className="quiz-option-marker" aria-hidden="true" />
                      <span>{option}</span>
                    </label>
                  );
                },
              )}
            </div>
          </fieldset>

          <div className="quiz-navigation">
            <button
              className="button button-quiet"
              type="button"
              disabled={currentIndex === 0}
              onClick={() => setCurrentIndex((index) => index - 1)}
            >
              <ArrowLeft size={16} aria-hidden="true" />
              Previous
            </button>
            {currentIndex < quizState.questions.length - 1 ? (
              <button
                className="button button-primary"
                type="button"
                onClick={() => setCurrentIndex((index) => index + 1)}
              >
                Next <ArrowRight size={16} aria-hidden="true" />
              </button>
            ) : (
              <span className="quiz-submit-hint">
                Review your answers, then submit below.
              </span>
            )}
          </div>

          {currentIndex === quizState.questions.length - 1 && (
            <div className="quiz-submit-section">
              <label htmlFor="quiz-username">Display name</label>
              <input
                id="quiz-username"
                className="quiz-name-input"
                type="text"
                autoComplete="nickname"
                minLength={3}
                maxLength={50}
                value={username}
                onChange={(event) => {
                  setUsername(event.target.value);
                  setSubmitError("");
                }}
                placeholder="How should we show your name?"
                aria-describedby="quiz-name-note"
              />
              <p id="quiz-name-note" className="quiz-name-note">
                This name appears on the leaderboard. Choose 3–50 characters;
                names must be unique.
              </p>
              {submitError && (
                <p className="quiz-submit-error" role="alert">
                  {submitError}
                </p>
              )}
              <button
                className="button button-primary quiz-submit-button"
                type="submit"
                disabled={
                  username.trim().length < 3 || username.trim().length > 50
                }
              >
                Submit quiz <Check size={16} aria-hidden="true" />
              </button>
            </div>
          )}
        </form>
      )}

      {quizState.status === "result" && (
        <section className="quiz-result" aria-live="polite">
          <div className="quiz-result-score">
            <span className="dashboard-icon dashboard-icon-gold">
              <Trophy size={21} aria-hidden="true" />
            </span>
            <p className="eyebrow">Quiz complete</p>
            <h2>
              {quizState.result.score} <span>points</span>
            </h2>
            <p>
              {quizState.result.correct_answers} of{" "}
              {quizState.result.total_questions} correct
            </p>
          </div>
          <div className="quiz-result-list">
            <h3>Your answers</h3>
            {quizState.result.results.map((answer, index) => {
              const question = quizState.questions.find(
                (item) => item.id === answer.question_id,
              );
              return (
                <article
                  className={`quiz-answer-review${answer.is_correct ? " is-correct" : " is-incorrect"}`}
                  key={answer.question_id}
                >
                  <div className="quiz-review-heading">
                    <span>
                      {answer.is_correct ? (
                        <Check size={16} aria-hidden="true" />
                      ) : (
                        <X size={16} aria-hidden="true" />
                      )}
                    </span>
                    <h4>
                      {index + 1}. {question?.question}
                    </h4>
                  </div>
                  <p>
                    Your answer:{" "}
                    {question?.options[answer.selected_option] ?? "—"}
                  </p>
                  {!answer.is_correct && (
                    <p>
                      Correct answer:{" "}
                      {question?.options[answer.correct_option] ?? "—"}
                    </p>
                  )}
                  <p className="quiz-explanation">{answer.explanation}</p>
                </article>
              );
            })}
          </div>
          <div className="quiz-actions">
            <button className="button button-primary" onClick={restartQuiz}>
              <RefreshCw size={16} aria-hidden="true" />
              Play another quiz
            </button>
            <Link className="button button-quiet" to="/dashboard">
              View my score
            </Link>
          </div>
        </section>
      )}
    </main>
  );
}
