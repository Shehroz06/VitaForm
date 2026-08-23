"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/services/api-client";

const FILE_ID_PATTERN = /\/files\/([0-9a-fA-F-]{36})(?:[/?#]|$)/;

/**
 * Renders a `/files/{id}` URL (which requires an Authorization header the
 * browser won't attach to a plain <img src>) by fetching it through the
 * authenticated API client and exposing it as a local object URL instead.
 */
export function useAuthenticatedFileUrl(fileUrl: string | null | undefined): string | null {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  useEffect(() => {
    const fileId = fileUrl ? FILE_ID_PATTERN.exec(fileUrl)?.[1] : undefined;
    let cancelled = false;

    if (!fileId) {
      // Deferred via a microtask so this reset isn't a synchronous setState
      // call inside the effect body itself.
      queueMicrotask(() => {
        if (!cancelled) setObjectUrl(null);
      });
      return () => {
        cancelled = true;
      };
    }

    let createdUrl: string | null = null;

    apiClient
      .fetchBlob(`/files/${fileId}`)
      .then((blob) => {
        if (cancelled) return;
        createdUrl = URL.createObjectURL(blob);
        setObjectUrl(createdUrl);
      })
      .catch(() => {
        if (!cancelled) setObjectUrl(null);
      });

    return () => {
      cancelled = true;
      if (createdUrl) URL.revokeObjectURL(createdUrl);
    };
  }, [fileUrl]);

  return objectUrl;
}
