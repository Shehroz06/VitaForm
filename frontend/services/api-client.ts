import { useAuthStore } from "@/store/auth-store";
import type { ApiResponse, ErrorDetail } from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const NO_RETRY_PATHS = ["/auth/login", "/auth/refresh", "/auth/register"];

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public errors: ErrorDetail[] = [],
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function rawRequest(path: string, init?: RequestInit): Promise<Response> {
  const accessToken = useAuthStore.getState().accessToken;

  return fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...init?.headers,
    },
  });
}

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) return false;

  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) return false;

  const body = (await response.json()) as ApiResponse<{
    access_token: string;
    refresh_token: string;
  }>;
  if (!body.success) return false;

  useAuthStore.getState().setAccessToken(body.data.access_token, body.data.refresh_token);
  return true;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response = await rawRequest(path, init);

  if (response.status === 401 && !NO_RETRY_PATHS.includes(path)) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      response = await rawRequest(path, init);
    } else {
      useAuthStore.getState().clearSession();
    }
  }

  const body = (await response.json()) as ApiResponse<T>;

  if (!body.success) {
    throw new ApiError(body.message, response.status, body.errors);
  }

  return body.data;
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "POST", body: data ? JSON.stringify(data) : undefined }),
  patch: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "PATCH", body: data ? JSON.stringify(data) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
