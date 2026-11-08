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

const CATEGORIES = ["wet", "dry", "recyclable"];

function categoryLabel(category) {
  return category.charAt(0).toUpperCase() + category.slice(1);
}

function getStartError(error) {
  if (error instanceof ApiError && error.status === 404) {
    return "There is no GreenGlow profile for this email yet. Selecting an email does not create an account. Complete the Green Quiz first, then return to Eco Sort.";
  }
  if (error instanceof ApiError && error.status === 503) {
    return "Eco Sort could not start right now. Please try again shortly.";
  }
  if (error instanceof ApiError) {
    return error.message;
  }
  return "The Eco Sort response was incomplete. Please try again.";
}

function getSubmitError(error) {
  if (!(error instanceof ApiError)) {
    return "Your sorting choices could not be submitted. Check your connection and try again.";
  }
  if (error.status === 403 || error.status === 404 || error.status === 409) {
    return "This game session is expired, unavailable, or already submitted. Start a new game to continue.";
  }
  if (error.status === 422) {
    return "The answers were not accepted. Check every item and try again.";
  }
  return error.message;
}

function LoadingPanel({ message }) {
  return (
    <div className="ecosort-state" role="status">
      <span className="dashboard-spinner" aria-hidden="true" />
      <p>{message}</p>
    </div>
  );
}

function ErrorPanel({ message, onRestart, terminal = false }) {
  return (
    <section className="ecosort-state ecosort-error" role="alert">
      <AlertCircle size={23} aria-hidden="true" />
      <h2>{terminal ? "Game session unavailable" : "Eco Sort couldn’t load"}</h2>
      <p>{message}</p>
      <div className="quiz-actions">
        <button className="button button-primary" onClick={onRestart}>
          <RefreshCw size={16} aria-hidden="true" />
          Start a new game
        </button>
        <Link className="button button-quiet" to="/dashboard">
          <ArrowLeft size={16} aria-hidden="true" />
          Back to dashboard
        </Link>
      </div>
    </section>
  );
}

export function EcoSortPage() {
  const { email } = useUser();
  const [gameState, setGameState] = useState({ status: "loading" });
  const [answers, setAnswers] = useState({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [submitError, setSubmitError] = useState("");
  const [retryCount, setRetryCount] = useState(0);
  const submitLock = useRef(false);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    async function prepareGame() {
      setGameState({ status: "loading" });
      setAnswers({});
      setCurrentIndex(0);
      setSubmitError("");
      submitLock.current = false;

      try {
        const availableItems = await request(endpoints.ecoSortItems, {
          signal: controller.signal,
        });
        if (!Array.isArray(availableItems)) {
          throw new Error("The Eco Sort items response was invalid.");
        }
        if (!active) {
          return;
        }
        if (availableItems.length === 0) {
          setGameState({ status: "empty" });
          return;
        }

        setGameState({ status: "starting" });
        const session = await request(endpoints.ecoSortStart, {
          method: "POST",
          body: { email },
          signal: controller.signal,
        });

        if (!active) {
          return;
        }
        if (
          typeof session?.session_token !== "string" ||
          !Array.isArray(session.items) ||
          session.items.length !== 10 ||
          !session.items.every(
            (item) =>
              Number.isInteger(item.id) &&
              typeof item.name === "string" &&
              typeof item.description === "string",
          )
        ) {
          throw new Error("The Eco Sort session response was invalid.");
        }

        setGameState({
          status: "active",
          sessionToken: session.session_token,
          items: session.items,
        });
      } catch (error) {
        if (!active || error.name === "AbortError") {
          return;
        }
        setGameState({ status: "error", message: getStartError(error) });
      }
    }

    prepareGame();
    return () => {
      active = false;
      controller.abort();
    };
  }, [email, retryCount]);

  function restartGame() {
    setRetryCount((count) => count + 1);
  }

  function selectCategory(itemId, category) {
    setAnswers((currentAnswers) => ({
      ...currentAnswers,
      [itemId]: category,
    }));
    setSubmitError("");
  }

  async function submitGame(event) {
    event.preventDefault();
    if (gameState.status !== "active" || submitLock.current) {
      return;
    }

    const fullyAnswered = gameState.items.every(
      (item) => typeof answers[item.id] === "string",
    );
    if (!fullyAnswered) {
      setSubmitError("Choose a category for every item before submitting.");
      return;
    }

    submitLock.current = true;
    setSubmitError("");
    setGameState((current) => ({ ...current, status: "submitting" }));

    try {
      const result = await request(endpoints.ecoSortSubmit, {
        method: "POST",
        body: {
          email,
          session_token: gameState.sessionToken,
          answers: gameState.items.map((item) => ({
            item_id: item.id,
            selected_category: answers[item.id],
          })),
        },
      });

      setGameState({
        status: "result",
        items: gameState.items,
        result,
      });
    } catch (error) {
      submitLock.current = false;
      if (error instanceof ApiError && [403, 404, 409].includes(error.status)) {
        setGameState({
          status: "terminal-error",
          message: getSubmitError(error),
        });
        return;
      }
      setGameState((current) => ({ ...current, status: "active" }));
      setSubmitError(getSubmitError(error));
    }
  }

  const activeItem =
    gameState.status === "active" ? gameState.items[currentIndex] : null;

  return (
    <main className="ecosort-page">
      <header className="ecosort-heading">
        <p className="eyebrow">
          <Leaf size={14} aria-hidden="true" />
          Eco Sort Game
        </p>
        <h1>Give every item the right place.</h1>
        <p>
          Sort each item using the categories below. Your choices are checked by
          GreenGlow; local collection rules can vary. Your email identifies
          your profile, it does not authenticate you.
        </p>
      </header>

      {gameState.status === "loading" && (
        <LoadingPanel message="Loading sorting items…" />
      )}
      {gameState.status === "starting" && (
        <LoadingPanel message="Starting your Eco Sort game…" />
      )}
      {gameState.status === "submitting" && (
        <LoadingPanel message="Checking your sorting choices…" />
      )}
      {gameState.status === "error" && (
        <ErrorPanel message={gameState.message} onRestart={restartGame} />
      )}
      {gameState.status === "terminal-error" && (
        <ErrorPanel
          message={gameState.message}
          onRestart={restartGame}
          terminal
        />
      )}
      {gameState.status === "empty" && (
        <section className="ecosort-state">
          <AlertCircle size={23} aria-hidden="true" />
          <h2>No sorting items are available</h2>
          <p>Please try again later.</p>
          <button className="button button-primary" onClick={restartGame}>
            <RefreshCw size={16} aria-hidden="true" />
            Try again
          </button>
        </section>
      )}

      {gameState.status === "active" && activeItem && (
        <form className="ecosort-card" onSubmit={submitGame}>
          <div className="ecosort-progress-heading">
            <span>
              Item {currentIndex + 1} of {gameState.items.length}
            </span>
            <span>
              {Object.keys(answers).length} sorted
            </span>
          </div>
          <div
            className="quiz-progress-track"
            role="progressbar"
            aria-label="Eco Sort progress"
            aria-valuemin={1}
            aria-valuemax={gameState.items.length}
            aria-valuenow={currentIndex + 1}
          >
            <span
              style={{
                width: `${((currentIndex + 1) / gameState.items.length) * 100}%`,
              }}
            />
          </div>

          <article className="ecosort-item">
            <span className="ecosort-item-visual" aria-hidden="true">
              <Leaf size={27} />
            </span>
            <p className="eyebrow">Sorting item</p>
            <h2>{activeItem.name}</h2>
            <p>{activeItem.description}</p>
          </article>

          <fieldset className="ecosort-categories">
            <legend>Which category does this belong in?</legend>
            <div className="ecosort-category-options">
              {CATEGORIES.map((category) => (
                <label
                  className={`ecosort-category-option${answers[activeItem.id] === category ? " is-selected" : ""}`}
                  key={category}
                >
                  <input
                    type="radio"
                    name={`item-${activeItem.id}`}
                    value={category}
                    checked={answers[activeItem.id] === category}
                    onChange={() => selectCategory(activeItem.id, category)}
                  />
                  <span className="ecosort-category-marker" aria-hidden="true" />
                  <span>{categoryLabel(category)}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <div className="ecosort-navigation">
            <button
              className="button button-quiet"
              type="button"
              disabled={currentIndex === 0}
              onClick={() => setCurrentIndex((index) => index - 1)}
            >
              <ArrowLeft size={16} aria-hidden="true" />
              Previous
            </button>
            {currentIndex < gameState.items.length - 1 ? (
              <button
                className="button button-primary"
                type="button"
                onClick={() => setCurrentIndex((index) => index + 1)}
              >
                Next <ArrowRight size={16} aria-hidden="true" />
              </button>
            ) : (
              <span className="ecosort-submit-hint">
                Review your choices, then check them.
              </span>
            )}
          </div>

          {currentIndex === gameState.items.length - 1 && (
            <div className="ecosort-submit-section">
              {submitError && (
                <p className="quiz-submit-error" role="alert">
                  {submitError}
                </p>
              )}
              <button
                className="button button-primary ecosort-submit-button"
                type="submit"
                disabled={
                  gameState.items.some(
                    (item) => typeof answers[item.id] !== "string",
                  )
                }
              >
                Check my sorting <Check size={16} aria-hidden="true" />
              </button>
            </div>
          )}
        </form>
      )}

      {gameState.status === "result" && (
        <section className="ecosort-result" aria-live="polite">
          <div className="ecosort-result-score">
            <span className="dashboard-icon dashboard-icon-green">
              <Trophy size={21} aria-hidden="true" />
            </span>
            <p className="eyebrow">Sorting complete</p>
            <h2>
              {gameState.result.score_awarded} <span>points</span>
            </h2>
            <p>
              {gameState.result.correct_answers} of{" "}
              {gameState.result.total_items} sorted correctly
            </p>
            <p>
              Total Green Score: {gameState.result.total_score.toLocaleString()}
            </p>
          </div>

          <div className="ecosort-result-list">
            <h3>Sorting review</h3>
            {gameState.result.results.map((result) => {
              const item = gameState.items.find(
                (entry) => entry.id === result.item_id,
              );
              return (
                <article
                  className={`ecosort-review${result.is_correct ? " is-correct" : " is-incorrect"}`}
                  key={result.item_id}
                >
                  <div className="ecosort-review-heading">
                    <span>
                      {result.is_correct ? (
                        <Check size={16} aria-hidden="true" />
                      ) : (
                        <X size={16} aria-hidden="true" />
                      )}
                    </span>
                    <h4>{item?.name ?? "Sorting item"}</h4>
                  </div>
                  <p>
                    Your choice: {categoryLabel(result.selected_category)}
                  </p>
                  {!result.is_correct && (
                    <p>
                      Correct category: {categoryLabel(result.correct_category)}
                    </p>
                  )}
                  <p className="ecosort-explanation">{result.explanation}</p>
                </article>
              );
            })}
          </div>

          <div className="quiz-actions">
            <button className="button button-primary" onClick={restartGame}>
              <RefreshCw size={16} aria-hidden="true" />
              Play another game
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
