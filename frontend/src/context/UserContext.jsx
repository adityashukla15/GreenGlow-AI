import { createContext, useContext, useMemo, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

const STORAGE_KEY = "greenglow.selectedEmail";
const UserContext = createContext(null);

function getStoredEmail() {
  try {
    return window.localStorage.getItem(STORAGE_KEY) || "";
  } catch {
    return "";
  }
}

export function UserProvider({ children }) {
  const [email, setEmailState] = useState(getStoredEmail);

  function setEmail(value) {
    const normalizedEmail = value.trim().toLowerCase();
    window.localStorage.setItem(STORAGE_KEY, normalizedEmail);
    setEmailState(normalizedEmail);
  }

  function clearEmail() {
    window.localStorage.removeItem(STORAGE_KEY);
    setEmailState("");
  }

  const contextValue = useMemo(
    () => ({ email, setEmail, clearEmail }),
    [email],
  );

  return (
    <UserContext.Provider value={contextValue}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === null) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return context;
}

export function RequireEmail({ children }) {
  const { email } = useUser();
  const location = useLocation();

  if (!email) {
    return (
      <Navigate
        to="/onboarding"
        replace
        state={{ from: location }}
      />
    );
  }

  return children;
}
