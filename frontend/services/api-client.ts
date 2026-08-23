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
  // FormData bodies must not get a manual Content-Type: the browser sets its
  // own multipart boundary, which we'd otherwise clobber.
  const isFormData = init?.body instanceof FormData;

  return fetch(`${API_BASE_URL}${path}`, {
    ...init,
    // The refresh token travels as an HttpOnly cookie (never readable by
    // JS), which only gets attached -- on this cross-origin dev setup and
    // any same-site production deployment -- when the request opts in.
    credentials: "include",
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...init?.headers,
    },
  });
}

// Several TanStack queries can 401 at once when the access token expires,
// each independently calling refreshAccessToken(). Without memoizing the
// in-flight request, the first caller's refresh rotates the (single-use)
// refresh cookie, and every other caller's own refresh attempt then hits
// an already-rotated-away token and fails, logging the user out. Sharing
// one in-flight promise across concurrent callers avoids that race.
let inFlightRefresh: Promise<boolean> | null = null;

async function refreshAccessToken(): Promise<boolean> {
  if (inFlightRefresh) return inFlightRefresh;

  inFlightRefresh = (async () => {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });

    if (!response.ok) return false;

    const body = (await response.json()) as ApiResponse<{ access_token: string }>;
    if (!body.success) return false;

    useAuthStore.getState().setAccessToken(body.data.access_token);
    return true;
  })().finally(() => {
    inFlightRefresh = null;
  });

  return inFlightRefresh;
}

async function requestWithRetry(path: string, init?: RequestInit): Promise<Response> {
  let response = await rawRequest(path, init);

  if (response.status === 401 && !NO_RETRY_PATHS.includes(path)) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      response = await rawRequest(path, init);
    } else {
      useAuthStore.getState().clearSession();
    }
  }

  return response;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await requestWithRetry(path, init);

  if (response.status === 204) {
    return undefined as T;
  }

  const body = (await response.json()) as ApiResponse<T>;

  if (!body.success) {
    throw new ApiError(body.message, response.status, body.errors);
  }

  return body.data;
}

// For endpoints that return raw binary (e.g. the resume preview image)
// instead of the standard {success, data} JSON envelope -- request()'s
// .json() parsing doesn't apply here, but the same 401-refresh-retry
// behavior does, so this shares requestWithRetry rather than duplicating it.
async function requestBlob(
  path: string,
  init?: RequestInit,
): Promise<{ blob: Blob; headers: Headers }> {
  const response = await requestWithRetry(path, init);
  if (!response.ok) {
    throw new ApiError(`Request failed with status ${response.status}`, response.status);
  }
  return { blob: await response.blob(), headers: response.headers };
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "POST", body: data ? JSON.stringify(data) : undefined }),
  patch: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "PATCH", body: data ? JSON.stringify(data) : undefined }),
  put: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "PUT", body: data ? JSON.stringify(data) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  upload: <T>(path: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<T>(path, { method: "POST", body: formData });
  },
  getBlob: async (path: string): Promise<{ blob: Blob; pageCount: number }> => {
    const { blob, headers } = await requestBlob(path, { method: "GET" });
    const pageCount = Number(headers.get("X-Page-Count") ?? "1");
    return { blob, pageCount: Number.isFinite(pageCount) && pageCount > 0 ? pageCount : 1 };
  },
  // Same contract as getBlob, but for endpoints that render a POSTed body
  // (e.g. "preview this not-yet-saved content against template X") rather
  // than GETting an already-saved resource.
  postBlob: async (path: string, data: unknown): Promise<{ blob: Blob; pageCount: number }> => {
    const { blob, headers } = await requestBlob(path, {
      method: "POST",
      body: JSON.stringify(data),
    });
    const pageCount = Number(headers.get("X-Page-Count") ?? "1");
    return { blob, pageCount: Number.isFinite(pageCount) && pageCount > 0 ? pageCount : 1 };
  },
  // Fetches an authenticated binary/text response and saves it as a file --
  // a plain <a href> can't carry the Authorization header this API requires,
  // so the browser's native download flow doesn't apply directly; this
  // fetches the bytes ourselves and hands them to the browser via a
  // throwaway object URL instead. Reads the real filename off
  // Content-Disposition when the server sends one (every endpoint that
  // supports this does), falling back to `fallbackFilename` otherwise.
  downloadFile: async (path: string, fallbackFilename: string): Promise<void> => {
    const { blob, headers } = await requestBlob(path, { method: "GET" });
    const disposition = headers.get("Content-Disposition") ?? "";
    const match = /filename="?([^"]+)"?/.exec(disposition);
    const filename = match?.[1] ?? fallbackFilename;

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  },
  // Fetches an authenticated binary response and opens it in a new tab --
  // preserves the "view in browser" UX a plain <a target="_blank"> would
  // give, which isn't otherwise possible since the browser can't attach the
  // Authorization header itself to a bare navigation.
  openInNewTab: async (path: string): Promise<void> => {
    const { blob } = await requestBlob(path, { method: "GET" });
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank", "noopener,noreferrer");
    // Revoke after a delay long enough for the new tab to load the resource;
    // an immediate revoke can race the tab's own fetch of the blob: URL.
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
  },
  // Fetches an authenticated binary response as a raw Blob, for callers that
  // display the bytes themselves (e.g. rendering an <img> from an object
  // URL) rather than triggering a download or a new-tab view.
  fetchBlob: async (path: string): Promise<Blob> => {
    const { blob } = await requestBlob(path, { method: "GET" });
    return blob;
  },
};
