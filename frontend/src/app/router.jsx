import { lazy, Suspense } from "react";
import { createBrowserRouter } from "react-router-dom";
import { AppLayout } from "../App.jsx";
import { RequireEmail } from "../context/UserContext.jsx";
import { NotFoundPage } from "../pages/NotFoundPage.jsx";

const HomePage = lazy(() =>
  import("../pages/HomePage.jsx").then((module) => ({
    default: module.HomePage,
  })),
);
const OnboardingPage = lazy(() =>
  import("../pages/OnboardingPage.jsx").then((module) => ({
    default: module.OnboardingPage,
  })),
);
const DashboardPage = lazy(() =>
  import("../pages/DashboardPage.jsx").then((module) => ({
    default: module.DashboardPage,
  })),
);
const QuizPage = lazy(() =>
  import("../pages/QuizPage.jsx").then((module) => ({
    default: module.QuizPage,
  })),
);
const EcoSortPage = lazy(() =>
  import("../pages/EcoSortPage.jsx").then((module) => ({
    default: module.EcoSortPage,
  })),
);
const ChallengesPage = lazy(() =>
  import("../pages/ChallengesPage.jsx").then((module) => ({
    default: module.ChallengesPage,
  })),
);
const AssistantPage = lazy(() =>
  import("../pages/AssistantPage.jsx").then((module) => ({
    default: module.AssistantPage,
  })),
);
const LeaderboardPage = lazy(() =>
  import("../pages/LeaderboardPage.jsx").then((module) => ({
    default: module.LeaderboardPage,
  })),
);

function RouteLoading() {
  return (
    <div className="dashboard-state" role="status">
      <span className="dashboard-spinner" aria-hidden="true" />
      <span>Loading page…</span>
    </div>
  );
}

function guardedPage(Page) {
  return (
    <Suspense fallback={<RouteLoading />}>
      <RequireEmail>
        <Page />
      </RequireEmail>
    </Suspense>
  );
}

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    errorElement: <NotFoundPage />,
    children: [
      { path: "/", element: <Suspense fallback={<RouteLoading />}><HomePage /></Suspense> },
      { path: "/onboarding", element: <Suspense fallback={<RouteLoading />}><OnboardingPage /></Suspense> },
      { path: "/dashboard", element: guardedPage(DashboardPage) },
      { path: "/quiz", element: guardedPage(QuizPage) },
      { path: "/challenges", element: guardedPage(ChallengesPage) },
      { path: "/eco-sort", element: guardedPage(EcoSortPage) },
      { path: "/assistant", element: guardedPage(AssistantPage) },
      { path: "/leaderboard", element: guardedPage(LeaderboardPage) },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
