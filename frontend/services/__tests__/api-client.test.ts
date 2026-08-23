import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiClient, ApiError } from "@/services/api-client";
import { useAuthStore } from "@/store/auth-store";

const API_BASE_URL = "http://localhost:8000/api/v1";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("apiClient", () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, accessToken: "old-token", status: "authenticated" });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("sends credentials: include and the bearer token on every request", async () => {
    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockResolvedValue(jsonResponse({ success: true, data: { ok: true } }));

    await apiClient.get("/health");

    expect(fetchMock).toHaveBeenCalledWith(
      `${API_BASE_URL}/health`,
      expect.objectContaining({
        credentials: "include",
        headers: expect.objectContaining({ Authorization: "Bearer old-token" }),
      }),
    );
  });

  it("refreshes the token once and retries after a single 401", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (url) => {
      const target = String(url);
      if (target.endsWith("/auth/refresh")) {
        return jsonResponse({ success: true, data: { access_token: "new-token" } });
      }
      if (target.endsWith("/protected")) {
        const isFresh = useAuthStore.getState().accessToken === "new-token";
        return isFresh
          ? jsonResponse({ success: true, data: { ok: true } })
          : jsonResponse({ success: false, message: "unauthorized" }, 401);
      }
      throw new Error(`unexpected fetch to ${target}`);
    });

    const result = await apiClient.get<{ ok: boolean }>("/protected");

    expect(result).toEqual({ ok: true });
    expect(useAuthStore.getState().accessToken).toBe("new-token");
    const refreshCalls = fetchMock.mock.calls.filter(([url]) =>
      String(url).endsWith("/auth/refresh"),
    );
    expect(refreshCalls).toHaveLength(1);
  });

  it("coalesces concurrent 401s into a single /auth/refresh call", async () => {
    let refreshCallCount = 0;
    vi.spyOn(global, "fetch").mockImplementation(async (url) => {
      const target = String(url);
      if (target.endsWith("/auth/refresh")) {
        refreshCallCount += 1;
        // A small delay so the three concurrent callers below are all
        // mid-flight (all already 401'd) before this resolves -- without
        // the single-flight guard this fix added, each would kick off its
        // own /auth/refresh instead of sharing this one.
        await new Promise((resolve) => setTimeout(resolve, 10));
        return jsonResponse({ success: true, data: { access_token: "new-token" } });
      }
      if (target.endsWith("/protected")) {
        const isFresh = useAuthStore.getState().accessToken === "new-token";
        return isFresh
          ? jsonResponse({ success: true, data: { ok: true } })
          : jsonResponse({ success: false, message: "unauthorized" }, 401);
      }
      throw new Error(`unexpected fetch to ${target}`);
    });

    const results = await Promise.all([
      apiClient.get("/protected"),
      apiClient.get("/protected"),
      apiClient.get("/protected"),
    ]);

    expect(results).toEqual([{ ok: true }, { ok: true }, { ok: true }]);
    expect(refreshCallCount).toBe(1);
  });

  it("clears the session when refresh itself fails", async () => {
    vi.spyOn(global, "fetch").mockImplementation(async (url) => {
      const target = String(url);
      if (target.endsWith("/auth/refresh")) {
        return new Response(null, { status: 401 });
      }
      return jsonResponse({ success: false, message: "unauthorized" }, 401);
    });

    await expect(apiClient.get("/protected")).rejects.toThrow(ApiError);
    expect(useAuthStore.getState().status).toBe("unauthenticated");
    expect(useAuthStore.getState().accessToken).toBeNull();
  });
});
