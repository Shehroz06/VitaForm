"use client";

import { useEffect, useMemo, useState } from "react";
import { Check, LayoutTemplate, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useTemplatePreview } from "@/features/resumes/hooks/use-resume-content";
import { useResumeTemplates } from "@/features/resumes/hooks/use-resumes";
import { TEMPLATE_REGISTRY, TEMPLATE_SLUGS } from "@/features/resumes/templates/registry";
import { configToStyle } from "@/features/resumes/style-mapping";
import type { ResumeContent } from "@/features/resumes/types";
import { cn } from "@/lib/utils";

/** One template card's live preview: a real backend render (same pipeline
 * as Export/the main editing preview), not a client-side approximation --
 * see resumeService.previewWith's docstring. Only fetches once the picker
 * dialog is actually open. */
function TemplateCardImage({
  resumeId,
  content,
  templateId,
  open,
}: {
  resumeId: string;
  content: ResumeContent;
  templateId: string;
  open: boolean;
}) {
  const { data, isLoading, isError } = useTemplatePreview(resumeId, content, templateId, open);

  const imageUrl = useMemo(() => {
    if (!data) return null;
    try {
      return URL.createObjectURL(data.blob);
    } catch {
      return null;
    }
  }, [data]);

  useEffect(() => {
    return () => {
      if (imageUrl) URL.revokeObjectURL(imageUrl);
    };
  }, [imageUrl]);

  if (imageUrl) {
    // eslint-disable-next-line @next/next/no-img-element -- fetched, authenticated blob URL, not a static asset
    return <img src={imageUrl} alt="" className="h-full w-full object-cover object-top" />;
  }
  if (isError) {
    return (
      <div className="flex h-full w-full items-center justify-center text-xs text-muted-foreground">
        Preview failed
      </div>
    );
  }
  return (
    <div className="flex h-full w-full items-center justify-center">
      {isLoading && <Loader2 className="size-5 animate-spin text-muted-foreground" />}
    </div>
  );
}

/**
 * Every card renders a real, backend-rendered A4 page for its template
 * (via TemplateCardImage) instead of a hand-maintained React
 * re-implementation, so comparing templates is judged on what they'll
 * actually look like -- and filled with everything on the profile
 * (previewContent), not just whatever's currently toggled on in this
 * resume's own draft, so the comparison reflects a realistic amount of
 * content rather than a possibly-sparse work in progress.
 */
export function TemplateSelector({
  resumeId,
  currentSlug,
  currentName,
  previewContent,
  onSelect,
}: {
  resumeId: string;
  currentSlug: string;
  currentName: string;
  previewContent: ResumeContent;
  onSelect: (slug: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const { data: templates } = useResumeTemplates();
  const templateIdBySlug = new Map(templates?.map((t) => [t.slug, t.id]) ?? []);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5 border-transparent bg-transparent text-sm font-normal shadow-none hover:bg-muted"
        >
          <LayoutTemplate className="size-4" />
          {currentName}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[85vh] max-w-3xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Choose a template</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 sm:grid-cols-3">
          {TEMPLATE_SLUGS.map((slug) => {
            const definition = TEMPLATE_REGISTRY[slug];
            const templateId = templateIdBySlug.get(slug);
            const selected = slug === currentSlug;
            const content: ResumeContent = {
              ...previewContent,
              style: configToStyle(definition.defaultConfig),
            };
            return (
              <button
                key={slug}
                type="button"
                onClick={() => {
                  onSelect(slug);
                  setOpen(false);
                }}
                className={cn(
                  "flex flex-col gap-2 rounded-xl p-2 text-left ring-1 ring-foreground/10 transition-colors hover:bg-muted",
                  selected && "ring-2 ring-primary",
                )}
              >
                <div className="relative aspect-[210/297] w-full overflow-hidden rounded-lg bg-neutral-100">
                  {templateId && (
                    <TemplateCardImage
                      resumeId={resumeId}
                      content={content}
                      templateId={templateId}
                      open={open}
                    />
                  )}
                </div>
                <div className="flex items-center justify-between gap-2 px-1">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-foreground">
                      {definition.name}
                    </p>
                    <p className="truncate text-xs text-muted-foreground">
                      {definition.description}
                    </p>
                  </div>
                  {selected && (
                    <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                      <Check className="size-3" />
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </DialogContent>
    </Dialog>
  );
}
