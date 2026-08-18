import { createContext, useContext, useEffect, useRef, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import type {
  ResumeTemplateData,
  TemplateConfig,
  TemplateFontFamily,
  TemplateSpacing,
} from "@/features/resumes/templates/types";

const SPACING_GAP: Record<TemplateSpacing, string> = {
  compact: "gap-4",
  cozy: "gap-5",
  relaxed: "gap-7",
};

// Approximate, browser-safe stacks for the live preview -- the exported PDF
// is always the source of truth for exact metrics (see backend's
// renderer.py FONT_STACKS), this just needs to read as "the same font family"
// in-browser even where the real font (e.g. Carlito for Calibri) isn't
// installed on the viewer's machine.
const FONT_STACKS: Record<TemplateFontFamily, string> = {
  arial: 'Arial, "Liberation Sans", Helvetica, sans-serif',
  calibri: 'Calibri, Carlito, "Segoe UI", sans-serif',
  times: '"Times New Roman", "Liberation Serif", Times, serif',
  georgia: 'Georgia, Caladea, Cambria, serif',
};

// A4 is 210mm x 297mm -- the exact ratio the backend renders to (WeasyPrint's
// `@page { size: A4 }`). Fixing the preview to this ratio, rather than
// letting the card grow with content, is what makes it a page instead of an
// arbitrarily long scrollable card.
const A4_ASPECT_RATIO = "210 / 297";

// The overflow warning is only useful in the one full-size preview the user
// is actually editing against -- inside a small side-by-side comparison
// (the template picker), the same real data renders at a fraction of its
// normal size, so it *always* looks like it overflows and the badge would
// show on every single card, telling the user nothing. Contexts that only
// want a visual comparison of styles wrap themselves in this to suppress it.
const ShowOverflowWarningContext = createContext(true);

export function TemplateComparisonPreview({ children }: { children: React.ReactNode }) {
  return (
    <ShowOverflowWarningContext.Provider value={false}>
      {children}
    </ShowOverflowWarningContext.Provider>
  );
}

/**
 * A resume is a printed document, not app UI -- it renders on white paper
 * with dark ink whether the app itself is in light or dark mode, matching
 * what the exported PDF actually looks like. Colors here are intentionally
 * fixed (not theme tokens). Every template renders through this shell so
 * the outer "page" chrome and font-family/spacing config application never
 * has to be reimplemented per template.
 *
 * The page is a fixed A4 rectangle that clips overflow, exactly like the
 * real export (which is strictly one page) -- it never grows taller than
 * one page's worth of content. If the user has manually added more than
 * fits, a warning badge appears instead of silently hiding that fact.
 */
export function TemplateShell({
  config,
  className,
  children,
}: {
  config: TemplateConfig;
  className?: string;
  children: React.ReactNode;
}) {
  const pageRef = useRef<HTMLDivElement>(null);
  const [overflowing, setOverflowing] = useState(false);
  const showOverflowWarning = useContext(ShowOverflowWarningContext);

  useEffect(() => {
    const page = pageRef.current;
    if (!page) return;

    const checkOverflow = () => setOverflowing(page.scrollHeight > page.clientHeight + 1);
    checkOverflow();

    const observer = new ResizeObserver(checkOverflow);
    observer.observe(page);
    return () => observer.disconnect();
  });

  return (
    <div className="relative">
      <div
        ref={pageRef}
        style={{ aspectRatio: A4_ASPECT_RATIO, fontFamily: FONT_STACKS[config.fontFamily] }}
        className={cn(
          "flex w-full flex-col overflow-hidden rounded-2xl bg-white p-8 text-neutral-900 shadow-lg ring-1 ring-black/10",
          className,
        )}
      >
        {/* Approximates the backend's continuous content-density scaling
            (features/ai/page_fit.py) -- only ever set for AI-generated
            resumes that needed shrinking to fit one page. `zoom` is
            Chromium/Safari-only, same tradeoff already accepted for the
            template-picker thumbnails elsewhere in this file's usages. */}
        <div
          style={{ zoom: config.contentDensity ?? 1 }}
          className={cn("flex flex-1 flex-col", SPACING_GAP[config.spacing])}
        >
          {children}
        </div>
      </div>
      {overflowing && showOverflowWarning && (
        <div className="absolute inset-x-3 bottom-3 flex items-center gap-1.5 rounded-lg bg-amber-500/95 px-3 py-1.5 text-xs font-medium text-white shadow-md">
          <AlertTriangle className="size-3.5 shrink-0" />
          Content exceeds one page. Try Compact spacing, or remove some items.
        </div>
      )}
    </div>
  );
}

export function isTemplateDataEmpty(data: ResumeTemplateData): boolean {
  return !data.summary && data.sections.every((section) => section.items.length === 0);
}

export function EmptyPreviewNotice({ data }: { data: ResumeTemplateData }) {
  if (!isTemplateDataEmpty(data)) return null;
  return (
    <p className="text-sm text-neutral-400 italic">
      Select items in the editor to see them appear here.
    </p>
  );
}
