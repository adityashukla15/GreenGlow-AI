import { useEffect, useState } from "react";
import { AlertCircle, Flame, Leaf, RefreshCw, Trophy } from "lucide-react";
import { ApiError, request } from "../services/api.js";
import { endpoints } from "../services/endpoints.js";
import { useUser } from "../context/UserContext.jsx";

function LoadingState({ label }) {
  return (
    <div className="dashboard-state" role="status">
      <span className="dashboard-spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

function RetryButton({ onRetry }) {
  return (
    <button className="button button-quiet dashboard-retry" onClick={onRetry}>
      <RefreshCw size={15} aria-hidden="true" />
      Try again
    </button>
  );
}

function DashboardError({ message, onRetry }) {
  return (
    <div className="dashboard-state dashboard-state-error" role="alert">
      <AlertCircle size={19} aria-hidden="true" />
      <p>{message}</p>
      <RetryButton onRetry={onRetry} />
    </div>
  );
}

export function DashboardPage() {
  const { email } = useUser();
  const [retryCount, setRetryCount] = useState(0);
  const [scoreState, setScoreState] = useState({ status: "loading" });
  const [leaderboardState, setLeaderboardState] = useState({
    status: "loading",
  });

  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    setScoreState({ status: "loading" });
    setLeaderboardState({ status: "loading" });

    request(endpoints.greenScore(email), { signal: controller.signal })
      .then((data) => {
        if (active) {
          setScoreState({ status: "success", data });
        }
      })
      .catch((error) => {
        if (!active || error.name === "AbortError") {
          return;
        }

        setScoreState({ status: "error", error });
      });

    request(`${endpoints.leaderboard}?limit=10`, {
      signal: controller.signal,
    })
      .then((data) => {
        if (active) {
          setLeaderboardState({ status: "success", data });
        }
      })
      .catch((error) => {
        if (!active || error.name === "AbortError") {
          return;
        }

        setLeaderboardState({ status: "error", error });
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [email, retryCount]);

  function retry() {
    setRetryCount((count) => count + 1);
  }

  const scoreErrorMessage =
    scoreState.status === "error" && scoreState.error instanceof ApiError
      ? scoreState.error.status === 404
        ? "There isn't a GreenGlow profile for this email yet. Selecting an email does not create a backend account. Participate in an experience first, then try again."
        : scoreState.error.message
      : "Green Score could not be loaded. Please try again.";
  const leaderboardErrorMessage =
    leaderboardState.status === "error" &&
    leaderboardState.error instanceof ApiError
      ? leaderboardState.error.status === 404
        ? "The leaderboard is not available right now. Please try again."
        : leaderboardState.error.message
      : "The leaderboard could not be loaded. Please try again.";

  return (
    <main className="dashboard-page">
      <header className="dashboard-heading">
        <p className="eyebrow">Your GreenGlow profile</p>
        <h1>My Green Score</h1>
        <p>
          Scores reflect activities linked to <strong>{email}</strong>. Your
          email is an identifier, not authentication.
        </p>
      </header>

      <div className="dashboard-grid">
        <section
          className="dashboard-card score-card"
          aria-labelledby="score-title"
        >
          <div className="dashboard-card-heading">
            <span className="dashboard-icon dashboard-icon-green">
              <Leaf size={19} aria-hidden="true" />
            </span>
            <div>
              <p className="eyebrow">Your progress</p>
              <h2 id="score-title">Green Score</h2>
            </div>
          </div>

          {scoreState.status === "loading" && (
            <LoadingState label="Loading your score…" />
          )}

          {scoreState.status === "error" &&
            (scoreState.error instanceof ApiError &&
            scoreState.error.status === 404 ? (
              <div className="dashboard-empty" role="status">
                <p>{scoreErrorMessage}</p>
                <RetryButton onRetry={retry} />
              </div>
            ) : (
              <DashboardError message={scoreErrorMessage} onRetry={retry} />
            ))}

          {scoreState.status === "success" && (
            <>
              <div className="score-total">
                <span>{scoreState.data.total_points.toLocaleString()}</span>
                <span>points</span>
              </div>
              <div className="score-breakdown">
                <p className="eyebrow">Score breakdown</p>
                <dl>
                  <div>
                    <dt>Quiz</dt>
                    <dd>
                      {scoreState.data.score_breakdown.quiz_points.toLocaleString()}
                    </dd>
                  </div>
                  <div>
                    <dt>Challenges</dt>
                    <dd>
                      {scoreState.data.score_breakdown.challenge_points.toLocaleString()}
                    </dd>
                  </div>
                  <div>
                    <dt>Eco Sort</dt>
                    <dd>
                      {scoreState.data.score_breakdown.eco_sort_points.toLocaleString()}
                    </dd>
                  </div>
                  {scoreState.data.score_breakdown.reconciliation_difference !==
                    0 && (
                    <div>
                      <dt>Score reconciliation difference</dt>
                      <dd>
                        {scoreState.data.score_breakdown.reconciliation_difference.toLocaleString()}
                      </dd>
                    </div>
                  )}
                </dl>
              </div>
            </>
          )}
        </section>

        <section
          className="dashboard-card leaderboard-card"
          aria-labelledby="leaderboard-title"
        >
          <div className="dashboard-card-heading">
            <span className="dashboard-icon dashboard-icon-gold">
              <Trophy size={19} aria-hidden="true" />
            </span>
            <div>
              <p className="eyebrow">Community</p>
              <h2 id="leaderboard-title">Leaderboard</h2>
            </div>
          </div>

          {leaderboardState.status === "loading" && (
            <LoadingState label="Loading leaderboard…" />
          )}

          {leaderboardState.status === "error" && (
            <DashboardError
              message={leaderboardErrorMessage}
              onRetry={retry}
            />
          )}

          {leaderboardState.status === "success" &&
            (leaderboardState.data.length === 0 ? (
              <div className="dashboard-empty" role="status">
                <Flame size={20} aria-hidden="true" />
                <p>The leaderboard is empty so far.</p>
              </div>
            ) : (
              <ol className="leaderboard-list">
                {leaderboardState.data.map((entry) => (
                  <li key={`${entry.rank}-${entry.username}`}>
                    <span className="leaderboard-rank">{entry.rank}</span>
                    <span className="leaderboard-name">{entry.username}</span>
                    <span className="leaderboard-score">
                      {entry.score.toLocaleString()}
                      <small> pts</small>
                    </span>
                  </li>
                ))}
              </ol>
            ))}
        </section>
      </div>
    </main>
  );
}
