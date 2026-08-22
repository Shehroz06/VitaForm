"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { CheckIcon, LayoutTemplate, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useResumeTemplates, useTemplateSamplePreview } from "@/features/resumes/hooks/use-resumes";
import { getTemplateDefinition } from "@/features/resumes/templates/registry";
import { ACCENT_OPTIONS } from "@/features/resumes/templates/style-options";
import { configToStyle } from "@/features/resumes/style-mapping";
import { cn } from "@/lib/utils";

/** A real backend render of the selected template filled with the user's
 * own profile (see resumeTemplateService.previewSample) -- there's no
 * resume yet at this point in the flow, so this is the one place a real
 * preview has to come from the profile directly rather than a saved
 * resume's content. */
function SamplePreview({
  templateId,
  slug,
  accent,
}: {
  templateId: string;
  slug: string;
  accent: string;
}) {
  const style = configToStyle({ ...getTemplateDefinition(slug).defaultConfig, accentColor: accent });
  const { data, isFetching, isError } = useTemplateSamplePreview(templateId, style, true);

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

  return (
    <div className="relative aspect-[210/297] w-full overflow-hidden rounded-lg bg-white shadow-sm ring-1 ring-black/10">
      {imageUrl && (
        // eslint-disable-next-line @next/next/no-img-element -- fetched, authenticated blob URL, not a static asset
        <img src={imageUrl} alt="" className="h-full w-full object-cover object-top" />
      )}
      {!imageUrl && isFetching && (
        <div className="flex h-full w-full items-center justify-center">
          <Loader2 className="size-6 animate-spin text-neutral-400" />
        </div>
      )}
      {!imageUrl && isError && (
        <div className="flex h-full w-full items-center justify-center p-4 text-center text-sm text-neutral-500">
          Preview failed to render.
        </div>
      )}
    </div>
  );
}

export default function TemplatesPage() {
  const { data: templates, isLoading } = useResumeTemplates();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [accent, setAccent] = useState<string>(ACCENT_OPTIONS[0].value);

  const selected = templates?.find((t) => t.id === selectedId) ?? templates?.[0];

  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 px-4 py-8 sm:px-6 lg:py-10">
      <PageHeader
        title="Templates"
        description="Pick a layout for your resume. The AI fills it in from your profile, tailored to a role."
      />

      {isLoading || !selected ? (
        <div className="grid gap-6 sm:grid-cols-[280px_1fr]">
          <Skeleton className="h-64 rounded-2xl" />
          <Skeleton className="h-96 rounded-2xl" />
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-[280px_1fr]">
          <div className="flex h-full flex-col justify-center gap-5 rounded-2xl bg-card p-4 ring-1 ring-foreground/10">
            <div className="flex flex-col gap-1">
              {templates?.map((template) => (
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
                      "mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-md",
                      selected.id === template.id
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground"
                    )}
                  >
                    <LayoutTemplate className="size-3.5" />
                  </span>
                  <div className="min-w-0">
                    <p
                      className={cn(
                        "text-sm font-medium",
                        selected.id === template.id ? "text-accent-foreground" : "text-foreground"
                      )}
                    >
                      {template.name}
                    </p>
                    {template.description && (
                      <p className="text-xs text-muted-foreground">{template.description}</p>
                    )}
                  </div>
                </button>
              ))}
            </div>

            <div className="flex flex-col gap-1.5 border-t border-border pt-4">
              <span className="text-xs font-medium text-muted-foreground">Accent color</span>
              <div className="flex flex-wrap gap-2">
                {ACCENT_OPTIONS.map((a) => (
                  <button
                    key={a.value}
                    type="button"
                    onClick={() => setAccent(a.value)}
                    aria-label={a.name}
                    aria-pressed={accent === a.value}
                    className={cn(
                      "relative flex size-7 items-center justify-center rounded-full ring-1 ring-foreground/10 transition-transform hover:scale-110",
                      accent === a.value && "ring-2 ring-offset-2 ring-offset-card"
                    )}
                    style={{ backgroundColor: a.value }}
                  >
                    {accent === a.value && <CheckIcon className="size-3.5 text-white" />}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="flex h-full flex-col gap-4 rounded-2xl bg-card p-6 ring-1 ring-foreground/10">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium text-muted-foreground">Preview</p>
              <p className="text-xs text-muted-foreground">{selected.name}</p>
            </div>
            <div className="mx-auto flex w-full max-w-[330px] flex-1 flex-col justify-center">
              <SamplePreview templateId={selected.id} slug={selected.slug} accent={accent} />
            </div>
            <Button asChild className="w-full sm:w-fit sm:self-center">
              <Link href={`/resumes?templateId=${selected.id}&accentColor=${encodeURIComponent(accent)}`}>
                Use this template
              </Link>
            </Button>
          </div>
        </div>
      )}
    </main>
  );
}
