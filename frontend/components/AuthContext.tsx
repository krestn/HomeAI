"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { loginRequest } from "../lib/api";

type AuthContextValue = {
  token: string | null;
  login: (identifier: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticating: boolean;
  authError: string | null;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);
const STORAGE_KEY = "homeai_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = window.localStorage.getItem(STORAGE_KEY);
    if (storedToken) {
      setToken(storedToken);
    }
  }, []);

  const login = useCallback(async (identifier: string, password: string) => {
    setIsAuthenticating(true);
    setAuthError(null);
    try {
      const response = await loginRequest(identifier, password);
      setToken(response.access_token);
      window.localStorage.setItem(STORAGE_KEY, response.access_token);
    } catch (error) {
      if (error instanceof Error) {
        setAuthError(error.message);
        throw error;
      }
      setAuthError("Login failed");
      throw new Error("Login failed");
    } finally {
      setIsAuthenticating(false);
    }
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    window.localStorage.removeItem(STORAGE_KEY);
  }, []);

  const value: AuthContextValue = {
    token,
    login,
    logout,
    isAuthenticating,
    authError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
}
