import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useAuthenticatedFileUrl } from "@/hooks/use-authenticated-file-url";
import { apiClient } from "@/services/api-client";

vi.mock("@/services/api-client", () => ({
  apiClient: { fetchBlob: vi.fn() },
}));

const FILE_URL =
  "http://localhost:8000/api/v1/files/11111111-1111-1111-1111-111111111111";

beforeEach(() => {
  URL.createObjectURL = vi.fn().mockReturnValue("blob:mock-url");
  URL.revokeObjectURL = vi.fn();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("useAuthenticatedFileUrl", () => {
  it("returns null when given no url", () => {
    const { result } = renderHook(() => useAuthenticatedFileUrl(null));
    expect(result.current).toBeNull();
  });

  it("fetches the file by the id extracted from the url and returns an object URL", async () => {
    vi.mocked(apiClient.fetchBlob).mockResolvedValue(new Blob(["hello"]));

    const { result } = renderHook(() => useAuthenticatedFileUrl(FILE_URL));

    await waitFor(() => expect(result.current).toBe("blob:mock-url"));
    expect(apiClient.fetchBlob).toHaveBeenCalledWith(
      "/files/11111111-1111-1111-1111-111111111111",
    );
  });

  it("revokes the object URL when the component unmounts", async () => {
    vi.mocked(apiClient.fetchBlob).mockResolvedValue(new Blob(["hello"]));

    const { result, unmount } = renderHook(() => useAuthenticatedFileUrl(FILE_URL));
    await waitFor(() => expect(result.current).toBe("blob:mock-url"));

    unmount();

    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:mock-url");
  });

  it("resolves to null if the fetch fails", async () => {
    vi.mocked(apiClient.fetchBlob).mockRejectedValue(new Error("network error"));

    const { result } = renderHook(() => useAuthenticatedFileUrl(FILE_URL));

    await waitFor(() => expect(vi.mocked(apiClient.fetchBlob)).toHaveBeenCalled());
    expect(result.current).toBeNull();
  });
});
