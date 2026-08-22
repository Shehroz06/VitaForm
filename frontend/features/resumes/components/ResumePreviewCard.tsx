"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useResumePreview } from "@/features/resumes/hooks/use-resume-content";

// A4 is 210mm x 297mm -- the exact ratio the backend renders to (see
// backend's WeasyPrint `@page { size: A4 }` and the LaTeX template's
// [letterpaper] margins, both of which the rasterized preview image
// already reflects at its own native aspect ratio). This is the frame the
// multi-page case scrolls *within* -- the card itself always stays one
// page tall, however many pages are stacked inside it.
const A4_RATIO = 297 / 210;

/**
 * The single source of truth for "what does this resume look like": renders
 * the same PNGs the backend produces from the same pipeline that powers
 * Export, rather than a second, hand-maintained React re-implementation of
 * each template that can silently drift from the real one (see
 * TemplateShell.tsx's docstring and this session's history for why that
 * drift was a real, user-facing problem). When a resume overflows one
 * page, every page is stacked inside a scrollable frame with a persistent
 * warning banner, rather than silently cropping to page 1.
 */
export function ResumePreviewCard({
  resumeId,
  className,
  fillHeight = false,
}: {
  resumeId: string;
  className?: string;
  // Desktop's sticky sidebar gives this card a real, explicit height (see
  // ResumeBuilder.tsx's aside) so the preview can size itself to reach the
  // bottom of that space instead of floating above it -- this flips the
  // measurement direction (measure height, derive width) to make that
  // possible. Mobile's collapsible panel has no such height (it's sized by
  // its own content), so it keeps the original width-driven-height mode,
  // the only one that works when there's no externally imposed height.
  fillHeight?: boolean;
}) {
  const { data, isFetching, isError, error } = useResumePreview(resumeId);
  // The URLs are derived state (computed from the fetched blobs), not
  // something to setState-from-an-effect for -- useMemo computes them
  // directly during render. The effect below exists purely to talk to the
  // external system (the browser's object-URL registry): its only job is
  // revoking the previous URLs when new ones replace them, or on unmount.
  //
  // createObjectURL throws (not rejects) on anything that isn't actually a
  // Blob, and a throw inside useMemo's render-time computation takes the
  // whole page down with it, not just this card -- guarding here means a
  // malformed response degrades to the "preview failed" state below
  // instead of a blank screen.
  const imageUrls = useMemo(() => {
    if (!data) return null;
    try {
      return data.pages.map((page) => URL.createObjectURL(page.blob));
    } catch {
      return null;
    }
  }, [data]);

  useEffect(() => {
    return () => {
      imageUrls?.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [imageUrls]);

  const overflowing = Boolean(data && data.pageCount > 1);

  // CSS `aspect-ratio` combined with `overflow-y: auto` is inconsistent
  // about whether the box holds its computed height or grows to fit
  // content that wants to be taller -- which is exactly the ambiguity that
  // would make multi-page content silently clip instead of scroll. Sidestep
  // it entirely: measure the real box this card has to fit in and compute
  // an explicit pixel width/height for it directly, "object-fit: contain"
  // style. An explicit size with overflow-y:auto has no ambiguity in any
  // browser -- content taller than that height scrolls, full stop. (auto,
  // not scroll: a single-page resume has nothing to scroll to, and a
  // permanently-shown scrollbar that doesn't move reads as broken, not as
  // "there's more below.")
  //
  // Mobile's collapsible panel has no externally imposed height (it's
  // sized by its own content) -- offsetHeight there would just reflect
  // whatever height the card last rendered at, feeding back into its own
  // input. `fillHeight` selects which real box to fit into: the wrapper's
  // full (width, height) when it has both, and just its width otherwise.
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState<{ width: number; height: number } | null>(null);

  useEffect(() => {
    const el = wrapperRef.current;
    if (!el) return;
    const update = () => {
      const width = fillHeight
        ? Math.min(el.offsetWidth, el.offsetHeight / A4_RATIO)
        : el.offsetWidth;
      setDims({ width, height: width * A4_RATIO });
    };
    update();
    const observer = new ResizeObserver(update);
    observer.observe(el);
    return () => observer.disconnect();
  }, [fillHeight]);

  return (
    <div ref={wrapperRef} className={cn("relative", fillHeight && "h-full")}>
      <div
        style={dims ? { width: dims.width, height: dims.height } : undefined}
        className={cn(
          "relative mx-auto overflow-y-auto bg-white shadow-lg ring-1 ring-black/10",
          className,
        )}
      >
        {imageUrls && (
          <div className="flex flex-col gap-6 bg-neutral-200 p-2">
            {imageUrls.map((url, index) => (
              // eslint-disable-next-line @next/next/no-img-element -- fetched, authenticated blob URLs, not static assets next/image can optimize
              <img
                key={url}
                src={url}
                alt={`Resume preview, page ${index + 1} of ${imageUrls.length}`}
                className="w-full shadow-sm"
              />
            ))}
          </div>
        )}

        {!imageUrls && isFetching && (
          <div className="flex h-full w-full items-center justify-center text-neutral-400">
            <Loader2 className="size-6 animate-spin" />
          </div>
        )}

        {!imageUrls && isError && (
          <div className="flex h-full w-full flex-col items-center justify-center gap-2 p-6 text-center text-sm text-neutral-500">
            <AlertTriangle className="size-6 text-amber-500" />
            Preview failed to render.
            <span className="text-xs text-neutral-400">
              {error instanceof Error ? error.message : "Try again in a moment."}
            </span>
          </div>
        )}

        {imageUrls && isFetching && (
          <div className="absolute inset-x-3 top-3 flex items-center gap-1.5 rounded-lg bg-black/70 px-2.5 py-1 text-xs font-medium text-white">
            <Loader2 className="size-3 animate-spin" />
            Updating preview…
          </div>
        )}
      </div>

      {overflowing && (
        <div className="absolute inset-x-3 bottom-3 z-10 flex items-center justify-center gap-1.5 rounded-lg border border-orange-700 bg-orange-500 px-3 py-2 text-xs font-bold text-white shadow-lg">
          <AlertTriangle className="size-4 shrink-0" />
          {data?.pageCount} pages — exceeds one page. Scroll to see the rest, or use Auto-fit /
          remove some items.
        </div>
      )}
    </div>
  );
}
