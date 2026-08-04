"use client";

import { useEffect, useSyncExternalStore } from "react";
import { authService } from "@/features/auth/services/auth-service";
import { apiClient } from "@/services/api-client";
import { useAuthStore } from "@/store/auth-store";

function subscribeToHydration(onHydrated: () => void) {
  return useAuthStore.persist.onFinishHydration(onHydrated);
}

function getHydrationSnapshot() {
  return useAuthStore.persist.hasHydrated();
}

function getServerHydrationSnapshot() {
  return false;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const hasHydrated = useSyncExternalStore(
    subscribeToHydration,
    getHydrationSnapshot,
    getServerHydrationSnapshot,
  );

  useEffect(() => {
    if (!hasHydrated) return;

    const { refreshToken, setSession, clearSession, setStatus } = useAuthStore.getState();

    if (!refreshToken) {
      setStatus("unauthenticated");
      return;
    }

    setStatus("loading");
    apiClient
      .post<{ access_token: string; refresh_token: string }>("/auth/refresh", {
        refresh_token: refreshToken,
      })
      .then(async (tokens) => {
        useAuthStore.getState().setAccessToken(tokens.access_token, tokens.refresh_token);
        const user = await authService.getCurrentUser();
        setSession(user, tokens.access_token, tokens.refresh_token);
      })
      .catch(() => {
        clearSession();
      });
  }, [hasHydrated]);

  return children;
}
