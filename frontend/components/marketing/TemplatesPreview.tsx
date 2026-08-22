"use client";

import * as React from "react";
import { CheckIcon, LayoutTemplate } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { TemplateMockup } from "@/components/marketing/TemplateMockup";
import { useResumeTemplates } from "@/features/resumes/hooks/use-resumes";
import { cn } from "@/lib/utils";

const ACCENTS = [
  { name: "Black", value: "#000000" },
  { name: "Wood Brown", value: "#8b5e3c" },
  { name: "Navy", value: "#35507e" },
  { name: "Emerald", value: "#2f6f56" },
  { name: "Burgundy", value: "#7a2f3f" },
  { name: "Slate", value: "#4a5563" },
  { name: "Purple", value: "#5b4a80" },
] as const;

export function TemplatesPreview() {
  const { data: templates, isLoading } = useResumeTemplates();
  const [accent, setAccent] = React.useState<string>(ACCENTS[0].value);
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
            Every template is ATS-friendly by design. Try an accent color below to see how it
            changes the look.
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

            <div className="flex flex-col gap-2">
              <span className="text-xs font-medium text-muted-foreground">Accent color</span>
              <div className="flex flex-wrap gap-2">
                {ACCENTS.map((a) => (
                  <button
                    key={a.value}
                    type="button"
                    onClick={() => setAccent(a.value)}
                    aria-label={a.name}
                    aria-pressed={accent === a.value}
                    className={cn(
                      "relative flex size-8 items-center justify-center rounded-full ring-1 ring-foreground/10 transition-transform hover:scale-110",
                      accent === a.value && "ring-2 ring-offset-2 ring-offset-background"
                    )}
                    style={{ backgroundColor: a.value }}
                  >
                    {accent === a.value && <CheckIcon className="size-3.5 text-white" />}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {selected && (
            // No h-full here: the grid's items-stretch already gives this
            // column a definite height, and adding h-full on top of that
            // pressures TemplateMockup's own aspect-[210/297] box to share
            // it rather than size purely from its own width -- letting the
            // wrapper size to content keeps the card genuinely A4-shaped.
            <div className="mx-auto flex w-full max-w-[280px] flex-col justify-center">
              <TemplateMockup slug={selected.slug} accent={accent} />
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
