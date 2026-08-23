"use client";

import { useEffect } from "react";
import { authService } from "@/features/auth/services/auth-service";
import { apiClient } from "@/services/api-client";
import { useAuthStore } from "@/store/auth-store";

// Re-establishes the session on every load. There's no persisted client
// state to check first (see auth-store.ts): the refresh token lives in an
// HttpOnly cookie, so the browser sends it automatically and this either
// succeeds (still logged in) or 401s (never logged in / cookie expired).
export function AuthProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const { setSession, clearSession, setStatus } = useAuthStore.getState();
    setStatus("loading");

    apiClient
      .post<{ access_token: string }>("/auth/refresh")
      .then(async (tokens) => {
        useAuthStore.getState().setAccessToken(tokens.access_token);
        const user = await authService.getCurrentUser();
        setSession(user, tokens.access_token);
      })
      .catch(() => {
        clearSession();
      });
  }, []);

  return children;
}
