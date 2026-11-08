import { useEffect, useState } from "react";
import { AlertCircle, RefreshCw, Trophy } from "lucide-react";
import { ApiError, request } from "../services/api.js";
import { endpoints } from "../services/endpoints.js";

function getErrorMessage(error) {
  if (error instanceof ApiError) {
    return error.message;
  }
  return "The leaderboard response could not be loaded. Please try again.";
}

export function LeaderboardPage() {
  const [retryCount, setRetryCount] = useState(0);
  const [state, setState] = useState({ status: "loading" });

  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    async function loadLeaderboard() {
      setState({ status: "loading" });
      try {
        const entries = await request(`${endpoints.leaderboard}?limit=100`, {
          signal: controller.signal,
        });
        if (
          !Array.isArray(entries) ||
          !entries.every(
            (entry) =>
              Number.isInteger(entry.rank) &&
              typeof entry.username === "string" &&
              Number.isFinite(entry.score),
          )
        ) {
          throw new Error("The leaderboard response was invalid.");
        }
        if (active) {
          setState({ status: "success", entries });
        }
      } catch (error) {
        if (!active || error.name === "AbortError") {
          return;
        }
        setState({ status: "error", message: getErrorMessage(error) });
      }
    }

    loadLeaderboard();
    return () => {
      active = false;
      controller.abort();
    };
  }, [retryCount]);

  return (
    <main className="leaderboard-page">
      <header className="leaderboard-heading">
        <p className="eyebrow">
          <Trophy size={14} aria-hidden="true" />
          Community
        </p>
        <h1>GreenGlow Leaderboard</h1>
        <p>See scores ranked by the GreenGlow community.</p>
      </header>

      {state.status === "loading" && (
        <div className="leaderboard-state" role="status">
          <span className="dashboard-spinner" aria-hidden="true" />
          <p>Loading leaderboard…</p>
        </div>
      )}

      {state.status === "error" && (
        <section className="leaderboard-state leaderboard-error" role="alert">
          <AlertCircle size={22} aria-hidden="true" />
          <h2>Leaderboard unavailable</h2>
          <p>{state.message}</p>
          <button
            className="button button-quiet"
            type="button"
            onClick={() => setRetryCount((count) => count + 1)}
          >
            <RefreshCw size={15} aria-hidden="true" />
            Try again
          </button>
        </section>
      )}

      {state.status === "success" &&
        (state.entries.length === 0 ? (
          <section className="leaderboard-state">
            <Trophy size={22} aria-hidden="true" />
            <h2>No scores yet</h2>
            <p>The leaderboard will appear when community scores are available.</p>
          </section>
        ) : (
          <ol className="leaderboard-full-list" aria-label="Ranked scores">
            {state.entries.map((entry) => (
              <li key={`${entry.rank}-${entry.username}`}>
                <span className="leaderboard-full-rank">{entry.rank}</span>
                <span className="leaderboard-full-name">{entry.username}</span>
                <span className="leaderboard-full-score">
                  {entry.score.toLocaleString()} <small>pts</small>
                </span>
              </li>
            ))}
          </ol>
        ))}
    </main>
  );
}
