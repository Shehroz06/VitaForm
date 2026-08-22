"use client";

import * as React from "react";
import Image from "next/image";
import { LayoutTemplate } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useResumeTemplates } from "@/features/resumes/hooks/use-resumes";
import { cn } from "@/lib/utils";

export function TemplatesPreview() {
  const { data: templates, isLoading } = useResumeTemplates();
  const [selectedId, setSelectedId] = React.useState<string | null>(null);

  const selected = templates?.find((t) => t.id === selectedId) ?? templates?.[0];

  return (
    <section id="templates" className="py-16 sm:py-20">
      <div className="mx-auto max-w-[1240px] px-4 sm:px-6">
        <div className="mx-auto max-w-xl text-center">
          <h2 className="font-heading text-3xl font-semibold tracking-tight text-foreground">
            Templates
          </h2>
          <p className="mt-3 text-muted-foreground">
            Every template is ATS-friendly by design.
          </p>
        </div>

        <div className="mx-auto mt-10 grid max-w-3xl items-stretch gap-8 sm:grid-cols-[1fr_0.9fr]">
          <div className="flex h-full flex-col justify-center gap-1">
            {isLoading || !selected ? (
              <>
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-16 w-full" />
              </>
            ) : (
              templates?.map((template) => (
                <button
                  key={template.id}
                  type="button"
                  onClick={() => setSelectedId(template.id)}
                  className={cn(
                    "flex items-start gap-2.5 rounded-lg px-2.5 py-2 text-left transition-colors hover:bg-muted",
                    selected.id === template.id && "bg-accent"
                  )}
                >
                  <span
                    className={cn(
                      "mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg",
                      selected.id === template.id
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground"
                    )}
                  >
                    <LayoutTemplate className="size-4" />
                  </span>
                  <div className="min-w-0">
                    <h3
                      className={cn(
                        "font-heading text-base font-medium",
                        selected.id === template.id ? "text-accent-foreground" : "text-foreground"
                      )}
                    >
                      {template.name}
                    </h3>
                    <p className="text-sm text-muted-foreground">{template.description}</p>
                  </div>
                </button>
              ))
            )}
          </div>

          {selected && (
            // No h-full here: the grid's items-stretch already gives this
            // column a definite height, and adding h-full on top of that
            // pressures the image's own aspect-[210/297] box to share it
            // rather than size purely from its own width -- letting the
            // wrapper size to content keeps the card genuinely A4-shaped.
            <div className="mx-auto flex w-full max-w-[280px] flex-col justify-center">
              <div className="relative aspect-[210/297] w-full overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-black/10">
                {/* Static, pre-rendered by the real backend pipeline (not a
                    client-side approximation) -- this section is shown to
                    logged-out visitors with no profile of their own to
                    render, so unlike the authenticated template picker
                    these can't be live per-visitor renders without opening
                    an unauthenticated compile endpoint to the public
                    internet. Regenerate frontend/public/template-samples/
                    if the templates' layout changes. */}
                <Image
                  src={`/template-samples/${selected.slug}.png`}
                  alt={`${selected.name} template preview`}
                  fill
                  sizes="280px"
                  className="object-cover object-top"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
