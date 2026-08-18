import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/features/auth/types";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  status: "idle" | "loading" | "authenticated" | "unauthenticated";
  setSession: (user: User, accessToken: string, refreshToken: string) => void;
  setAccessToken: (accessToken: string, refreshToken: string) => void;
  setUser: (user: User) => void;
  clearSession: () => void;
  setStatus: (status: AuthState["status"]) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      status: "idle",
      setSession: (user, accessToken, refreshToken) =>
        set({ user, accessToken, refreshToken, status: "authenticated" }),
      setAccessToken: (accessToken, refreshToken) =>
        set({ accessToken, refreshToken, status: "authenticated" }),
      setUser: (user) => set({ user }),
      clearSession: () =>
        set({ user: null, accessToken: null, refreshToken: null, status: "unauthenticated" }),
      setStatus: (status) => set({ status }),
    }),
    {
      name: "career-os-auth",
      partialize: (state) => ({ refreshToken: state.refreshToken }),
    },
  ),
);
