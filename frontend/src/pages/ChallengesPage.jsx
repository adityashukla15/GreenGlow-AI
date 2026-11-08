import { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  ArrowLeft,
  Check,
  CircleCheck,
  Leaf,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { Link } from "react-router-dom";
import { ApiError, request } from "../services/api.js";
import { endpoints } from "../services/endpoints.js";
import { useUser } from "../context/UserContext.jsx";

function getListError(error) {
  if (error instanceof ApiError) {
    return error.message;
  }
  return "Challenges could not be loaded. Check your connection and try again.";
}

function getCompletionError(error) {
  if (!(error instanceof ApiError)) {
    return "We couldn’t confirm the result. Check your connection before trying again.";
  }
  if (error.status === 404) {
    return "Your profile or this challenge is not available. If this is a new profile, complete the Green Quiz first. Then reload the challenges.";
  }
  if (error.status === 409) {
    return "This challenge has already been completed for this profile.";
  }
  if (error.status === 422) {
    return "The selected profile email was not accepted. Check your onboarding email and try again.";
  }
  return error.message;
}

function LoadingState() {
  return (
    <div className="challenge-state" role="status">
      <span className="dashboard-spinner" aria-hidden="true" />
      <p>Loading your challenges…</p>
    </div>
  );
}

function ErrorState({ message, onRetry }) {
  return (
    <section className="challenge-state challenge-error" role="alert">
      <AlertCircle size={23} aria-hidden="true" />
      <h2>Challenges are unavailable</h2>
      <p>{message}</p>
      <button className="button button-primary" onClick={onRetry}>
        <RefreshCw size={16} aria-hidden="true" />
        Try again
      </button>
    </section>
  );
}

export function ChallengesPage() {
  const { email } = useUser();
  const [loadState, setLoadState] = useState({ status: "loading" });
  const [retryCount, setRetryCount] = useState(0);
  const [confirmingId, setConfirmingId] = useState(null);
  const [completionStates, setCompletionStates] = useState({});
  const inFlightCompletions = useRef(new Set());

  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    async function loadChallenges() {
      setLoadState({ status: "loading" });

      try {
        const challenges = await request(endpoints.challenges, {
          signal: controller.signal,
        });
        const completionStatus = await request(
          endpoints.challengeCompletions(email),
          { signal: controller.signal },
        );
        if (
          !Array.isArray(challenges) ||
          typeof completionStatus?.profile_exists !== "boolean" ||
          !Array.isArray(completionStatus.completed_challenge_ids) ||
          !completionStatus.completed_challenge_ids.every(Number.isInteger)
        ) {
          throw new Error("The challenges response was invalid.");
        }
        if (active) {
          setCompletionStates(
            Object.fromEntries(
              completionStatus.completed_challenge_ids.map((id) => [
                id,
                { status: "already-completed" },
              ]),
            ),
          );
          setLoadState({
            status: "success",
            challenges,
            profileExists: completionStatus.profile_exists,
          });
        }
      } catch (error) {
        if (!active || error.name === "AbortError") {
          return;
        }
        setLoadState({ status: "error", message: getListError(error) });
      }
    }

    loadChallenges();
    return () => {
      active = false;
      controller.abort();
    };
  }, [retryCount]);

  function retryLoading() {
    setRetryCount((count) => count + 1);
    setCompletionStates({});
    setConfirmingId(null);
  }

  function askToComplete(challengeId) {
    setConfirmingId(challengeId);
    setCompletionStates((current) => ({
      ...current,
      [challengeId]: { status: "confirming" },
    }));
  }

  function cancelCompletion(challengeId) {
    setConfirmingId(null);
    setCompletionStates((current) => {
      const next = { ...current };
      delete next[challengeId];
      return next;
    });
  }

  async function completeChallenge(challengeId) {
    if (
      completionStates[challengeId]?.status !== "confirming" ||
      inFlightCompletions.current.has(challengeId)
    ) {
      return;
    }

    inFlightCompletions.current.add(challengeId);
    setCompletionStates((current) => ({
      ...current,
      [challengeId]: { status: "submitting" },
    }));
    setConfirmingId(null);

    try {
      const result = await request(
        endpoints.completeChallenge(challengeId),
        {
          method: "POST",
          body: { email },
        },
      );

      if (
        typeof result?.challenge_title !== "string" ||
        typeof result.points_awarded !== "number" ||
        typeof result.total_score !== "number"
      ) {
        throw new Error("The challenge completion response was invalid.");
      }

      setCompletionStates((current) => ({
        ...current,
        [challengeId]: { status: "completed", result },
      }));
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setCompletionStates((current) => ({
          ...current,
          [challengeId]: {
            status: "already-completed",
            message: getCompletionError(error),
          },
        }));
        return;
      }
      setCompletionStates((current) => ({
        ...current,
        [challengeId]: {
          status: "error",
          message: getCompletionError(error),
        },
      }));
    } finally {
      inFlightCompletions.current.delete(challengeId);
    }
  }

  return (
    <main className="challenges-page">
      <header className="challenges-heading">
        <p className="eyebrow">
          <Leaf size={14} aria-hidden="true" />
          Daily Challenges
        </p>
        <h1>Small actions, thoughtful celebrations.</h1>
        <p>
          Choose a practical eco-friendly activity. Completing a challenge
          awards the points returned by GreenGlow. Your email identifies your
          profile; it does not authenticate you.
        </p>
      </header>

      {loadState.status === "loading" && <LoadingState />}
      {loadState.status === "error" && (
        <ErrorState message={loadState.message} onRetry={retryLoading} />
      )}
      {loadState.status === "success" && loadState.challenges.length === 0 && (
        <section className="challenge-state">
          <Sparkles size={23} aria-hidden="true" />
          <h2>No challenges available right now</h2>
          <p>Check back soon for another way to celebrate thoughtfully.</p>
          <button className="button button-quiet" onClick={retryLoading}>
            <RefreshCw size={16} aria-hidden="true" />
            Refresh
          </button>
        </section>
      )}

      {loadState.status === "success" && loadState.challenges.length > 0 && (
        <section className="challenge-grid" aria-label="Available challenges">
          {loadState.challenges.map((challenge) => {
            const completion = completionStates[challenge.id];
            const isConfirming = confirmingId === challenge.id;
            const isSubmitting = completion?.status === "submitting";
            const isCompleted = [
              "completed",
              "already-completed",
            ].includes(completion?.status);

            return (
              <article className="challenge-card" key={challenge.id}>
                <div className="challenge-card-top">
                  <span className="challenge-icon" aria-hidden="true">
                    {isCompleted ? (
                      <CircleCheck size={20} />
                    ) : (
                      <Leaf size={20} />
                    )}
                  </span>
                  <span className="challenge-points">
                    {challenge.points} points
                  </span>
                </div>
                <h2>{challenge.title}</h2>
                <p className="challenge-description">{challenge.description}</p>

                {isCompleted ? (
                  <div className="challenge-completion" role="status">
                    <p className="challenge-success">
                      <Check size={16} aria-hidden="true" />
                      {completion.result?.message ??
                        "This challenge has already been completed for this profile."}
                    </p>
                      {completion.result && (
                        <p>
                          <strong>{completion.result.points_awarded}</strong>{" "}
                          points awarded · Green Score now{" "}
                          <strong>{completion.result.total_score}</strong>
                        </p>
                      )}
                    </div>
                ) : isConfirming ? (
                  <div
                    className="challenge-confirm"
                    role="group"
                    aria-label={`Confirm completion of ${challenge.title}`}
                  >
                    <p>
                      Confirm that you completed this challenge? It can only be
                      completed once for this profile.
                    </p>
                    <div className="challenge-confirm-actions">
                      <button
                        className="button button-primary"
                        type="button"
                        onClick={() => completeChallenge(challenge.id)}
                      >
                        Yes, complete
                      </button>
                      <button
                        className="button button-quiet"
                        type="button"
                        onClick={() => cancelCompletion(challenge.id)}
                      >
                        Not yet
                      </button>
                    </div>
                  </div>
                ) : !loadState.profileExists ? (
                  <p className="challenge-inline-message" role="status">
                    Complete the <Link to="/quiz">Green Quiz</Link> first to
                    create a profile before completing challenges.
                  </p>
                ) : (
                  <>
                    {completion?.status === "error" && (
                      <p className="challenge-inline-error" role="alert">
                        {completion.message}
                      </p>
                    )}
                    <button
                      className="button button-primary challenge-action"
                      type="button"
                      disabled={isSubmitting}
                      onClick={() => askToComplete(challenge.id)}
                    >
                      {isSubmitting ? (
                        <>
                          <span
                            className="dashboard-spinner challenge-button-spinner"
                            aria-hidden="true"
                          />
                          Recording…
                        </>
                      ) : (
                        <>
                          Mark as completed
                          <Check size={16} aria-hidden="true" />
                        </>
                      )}
                    </button>
                  </>
                )}
              </article>
            );
          })}
        </section>
      )}

      <p className="challenge-email-note">
        Using profile email <strong>{email}</strong>. To change it, update your
        profile email in onboarding.
      </p>
      <Link className="button button-quiet challenge-back-link" to="/dashboard">
        <ArrowLeft size={16} aria-hidden="true" />
        Back to dashboard
      </Link>
    </main>
  );
}
