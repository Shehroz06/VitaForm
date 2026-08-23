import { create } from "zustand";
import type { User } from "@/features/auth/types";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  status: "idle" | "loading" | "authenticated" | "unauthenticated";
  setSession: (user: User, accessToken: string) => void;
  setAccessToken: (accessToken: string) => void;
  setUser: (user: User) => void;
  clearSession: () => void;
  setStatus: (status: AuthState["status"]) => void;
}

// No persist middleware: the refresh token lives only in an HttpOnly cookie
// (never readable by JS), so there is nothing left worth persisting to
// localStorage. AuthProvider re-establishes the session on every load by
// calling /auth/refresh, which the browser authenticates via that cookie.
export const useAuthStore = create<AuthState>()((set) => ({
  user: null,
  accessToken: null,
  status: "idle",
  setSession: (user, accessToken) => set({ user, accessToken, status: "authenticated" }),
  setAccessToken: (accessToken) => set({ accessToken, status: "authenticated" }),
  setUser: (user) => set({ user }),
  clearSession: () => set({ user: null, accessToken: null, status: "unauthenticated" }),
  setStatus: (status) => set({ status }),
}));
