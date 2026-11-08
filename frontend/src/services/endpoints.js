export const endpoints = {
  root: "/",
  health: "/health",
  quizQuestions: "/api/v1/quiz/questions",
  quizSessionStart: "/api/v1/quiz/session/start",
  quizSessionSubmit: "/api/v1/quiz/session/submit",
  quizSubmit: "/api/v1/quiz/submit",
  challenges: "/api/v1/challenges/",
  challengeCompletions: (email) =>
    `/api/v1/challenges/completions?email=${encodeURIComponent(email)}`,
  completeChallenge: (challengeId) =>
    `/api/v1/challenges/${encodeURIComponent(challengeId)}/complete`,
  leaderboard: "/api/v1/leaderboard/",
  assistant: "/api/v1/ai/assistant",
  ecoSortItems: "/api/v1/eco-sort/items",
  ecoSortStart: "/api/v1/eco-sort/start",
  ecoSortSubmit: "/api/v1/eco-sort/submit",
  greenScore: (email) =>
    `/api/v1/green-score?email=${encodeURIComponent(email)}`,
};
