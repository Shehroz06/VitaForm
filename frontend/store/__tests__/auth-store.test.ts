import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/store/auth-store";

const user = {
  id: "user-1",
  email: "user@example.com",
  first_name: "Test",
  last_name: "User",
  is_email_verified: true,
  roles: ["student"],
  created_at: "2026-01-01T00:00:00Z",
};

function resetStore() {
  useAuthStore.setState({ user: null, accessToken: null, status: "idle" });
}

describe("useAuthStore", () => {
  beforeEach(() => {
    resetStore();
  });

  it("starts idle with no user or token", () => {
    const state = useAuthStore.getState();
    expect(state.status).toBe("idle");
    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
  });

  it("setSession stores the user and token and marks authenticated", () => {
    useAuthStore.getState().setSession(user, "access-token-1");

    const state = useAuthStore.getState();
    expect(state.user).toEqual(user);
    expect(state.accessToken).toBe("access-token-1");
    expect(state.status).toBe("authenticated");
  });

  it("setAccessToken updates only the token, keeping status authenticated", () => {
    useAuthStore.getState().setSession(user, "access-token-1");
    useAuthStore.getState().setAccessToken("access-token-2");

    const state = useAuthStore.getState();
    expect(state.accessToken).toBe("access-token-2");
    expect(state.user).toEqual(user);
    expect(state.status).toBe("authenticated");
  });

  it("setUser updates only the user, leaving token and status untouched", () => {
    useAuthStore.getState().setSession(user, "access-token-1");
    const updatedUser = { ...user, first_name: "Updated" };
    useAuthStore.getState().setUser(updatedUser);

    const state = useAuthStore.getState();
    expect(state.user).toEqual(updatedUser);
    expect(state.accessToken).toBe("access-token-1");
  });

  it("clearSession wipes user and token and marks unauthenticated", () => {
    useAuthStore.getState().setSession(user, "access-token-1");
    useAuthStore.getState().clearSession();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
    expect(state.status).toBe("unauthenticated");
  });

  it("setStatus updates status independently of user/token", () => {
    useAuthStore.getState().setStatus("loading");
    expect(useAuthStore.getState().status).toBe("loading");
  });
});
