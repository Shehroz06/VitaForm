"use client";

import { useState } from "react";
import { Check, LayoutTemplate } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { TemplateComparisonPreview } from "@/features/resumes/templates/shared/TemplateShell";
import { TemplateRenderer } from "@/features/resumes/templates/TemplateRenderer";
import { TEMPLATE_REGISTRY, TEMPLATE_SLUGS } from "@/features/resumes/templates/registry";
import type { ResumeTemplateData } from "@/features/resumes/templates/types";
import { cn } from "@/lib/utils";

/**
 * Each card renders the SAME live TemplateRenderer used in the main
 * preview, fed the resume's real (already-mapped) data, at a small zoom --
 * a genuine live preview per template, not a separate fake mockup.
 */
export function TemplateSelector({
  currentSlug,
  currentName,
  previewData,
  onSelect,
}: {
  currentSlug: string;
  currentName: string;
  previewData: ResumeTemplateData;
  onSelect: (slug: string) => void;
}) {
  const [open, setOpen] = useState(false);

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
          <TemplateComparisonPreview>
            {TEMPLATE_SLUGS.map((slug) => {
              const definition = TEMPLATE_REGISTRY[slug];
              const selected = slug === currentSlug;
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
                  <div className="relative h-48 w-full overflow-hidden rounded-lg bg-neutral-100">
                    <div className="pointer-events-none" style={{ zoom: 0.32 }}>
                      <TemplateRenderer
                        slug={slug}
                        data={previewData}
                        config={definition.defaultConfig}
                      />
                    </div>
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
          </TemplateComparisonPreview>
        </div>
      </DialogContent>
    </Dialog>
  );
}
