"use client";

import { ChevronDown, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { TemplateMockup } from "@/components/marketing/TemplateMockup";
import { useGenerateResume, useResumeTemplates } from "@/features/resumes/hooks/use-resumes";
import { TEMPLATE_REGISTRY, TEMPLATE_SLUGS } from "@/features/resumes/templates/registry";
import { ACCENT_OPTIONS } from "@/features/resumes/templates/style-options";
import { ApiError } from "@/services/api-client";
import { cn } from "@/lib/utils";

const MIN_JOB_DESCRIPTION_LENGTH = 50;

export interface GenerateResumeInitialValues {
  title?: string;
  jobDescription?: string;
  targetRole?: string;
  targetCompany?: string;
}

/**
 * The primary way to create a resume: describe the role, let the AI select
 * and arrange your real profile data to fit it. Inline (not a dialog) so it
 * reads as the main flow, not a buried popup.
 */
export function GenerateResumeForm({
  presetTemplateId,
  presetAccentColor,
  initialValues,
}: {
  presetTemplateId?: string;
  presetAccentColor?: string;
  initialValues?: GenerateResumeInitialValues;
}) {
  const router = useRouter();
  const { data: templates } = useResumeTemplates();
  const generateResume = useGenerateResume();

  const [title, setTitle] = useState(initialValues?.title ?? "");
  const [jobDescription, setJobDescription] = useState(initialValues?.jobDescription ?? "");
  const [targetRole, setTargetRole] = useState(initialValues?.targetRole ?? "");
  const [targetCompany, setTargetCompany] = useState(initialValues?.targetCompany ?? "");
  const [showMore, setShowMore] = useState(
    Boolean(initialValues?.targetRole || initialValues?.targetCompany),
  );
  const [showTemplate, setShowTemplate] = useState(
    Boolean(presetTemplateId || presetAccentColor),
  );

  // Both optional, same as title -- template/color are presentation choices,
  // not part of "describe the role." Leaving them untouched means "use the
  // platform default," resolved server-side.
  const [templateId, setTemplateId] = useState<string | undefined>(presetTemplateId);
  const [accentColor, setAccentColor] = useState<string | undefined>(presetAccentColor);

  const isJobDescriptionTooShort = jobDescription.trim().length < MIN_JOB_DESCRIPTION_LENGTH;

  const handleGenerate = () => {
    if (isJobDescriptionTooShort) return;

    generateResume.mutate(
      {
        title: title.trim() || null,
        template_id: templateId || null,
        accent_color: accentColor || null,
        job_description: jobDescription.trim(),
        target_role: targetRole.trim() || null,
        target_company: targetCompany.trim() || null,
      },
      {
        onSuccess: (response) => {
          toast.success("Resume generated.");
          router.push(`/resumes/${response.resume_id}`);
        },
        onError: (error) => {
          toast.error(
            error instanceof ApiError ? error.message : "Failed to generate resume with AI.",
          );
        },
      },
    );
  };

  return (
    <div className="flex flex-col gap-4 rounded-2xl bg-card p-5 ring-1 ring-foreground/10">
      <div className="flex items-center gap-2">
        <span className="flex size-8 items-center justify-center rounded-lg bg-accent text-accent-foreground">
          <Sparkles className="size-4" />
        </span>
        <div>
          <h2 className="font-heading text-base font-medium text-foreground">
            Generate a tailored resume
          </h2>
          <p className="text-sm text-muted-foreground">
            Describe the role. The AI selects and arranges your real profile data to fit it.
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="resume-title">Title (optional)</Label>
        <Input
          id="resume-title"
          placeholder="Software Engineer Resume"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="job-description">Job description</Label>
        <Textarea
          id="job-description"
          rows={6}
          placeholder="Paste the job description here — this is what the AI tailors your resume to."
          value={jobDescription}
          onChange={(event) => setJobDescription(event.target.value)}
        />
        {isJobDescriptionTooShort && jobDescription.length > 0 && (
          <p className="text-xs text-muted-foreground">
            At least {MIN_JOB_DESCRIPTION_LENGTH} characters needed.
          </p>
        )}
      </div>

      <button
        type="button"
        onClick={() => setShowMore((v) => !v)}
        className="flex w-fit items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ChevronDown className={cn("size-4 transition-transform", showMore && "rotate-180")} />
        More details
      </button>

      {showMore && (
        <div className="grid gap-3 border-t border-border pt-4 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="target-role">Target role</Label>
            <Input
              id="target-role"
              placeholder="Backend Engineer"
              value={targetRole}
              onChange={(event) => setTargetRole(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="target-company">Target company</Label>
            <Input
              id="target-company"
              placeholder="Acme Corp"
              value={targetCompany}
              onChange={(event) => setTargetCompany(event.target.value)}
            />
          </div>
        </div>
      )}

      <button
        type="button"
        onClick={() => setShowTemplate((v) => !v)}
        className="flex w-fit items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ChevronDown className={cn("size-4 transition-transform", showTemplate && "rotate-180")} />
        Template (optional)
      </button>

      {showTemplate && (
        <div className="flex flex-col gap-4 border-t border-border pt-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {TEMPLATE_SLUGS.map((slug) => {
              const definition = TEMPLATE_REGISTRY[slug];
              const template = templates?.find((t) => t.slug === slug);
              const selected = template ? template.id === templateId : false;
              return (
                <button
                  key={slug}
                  type="button"
                  disabled={!template}
                  onClick={() => template && setTemplateId(template.id)}
                  className={cn(
                    "flex flex-col gap-1.5 rounded-xl p-1.5 text-left ring-1 ring-foreground/10 transition-colors hover:bg-muted disabled:opacity-50",
                    selected && "ring-2 ring-primary",
                  )}
                >
                  <div className="overflow-hidden rounded-lg bg-neutral-100">
                    <TemplateMockup
                      slug={slug}
                      accent={accentColor ?? definition.defaultConfig.accentColor}
                    />
                  </div>
                  <p className="truncate px-0.5 text-xs font-medium text-foreground">
                    {definition.name}
                  </p>
                </button>
              );
            })}
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="text-xs font-medium text-muted-foreground">Accent color</span>
            <div className="flex flex-wrap gap-2">
              {ACCENT_OPTIONS.map((accent) => (
                <button
                  key={accent.value}
                  type="button"
                  onClick={() => setAccentColor(accent.value)}
                  aria-label={accent.name}
                  aria-pressed={accentColor === accent.value}
                  className={cn(
                    "size-6 rounded-full ring-1 ring-foreground/10 transition-transform hover:scale-110",
                    accentColor === accent.value && "ring-2 ring-offset-2 ring-offset-card",
                  )}
                  style={{ backgroundColor: accent.value }}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      <Button
        onClick={handleGenerate}
        disabled={generateResume.isPending || isJobDescriptionTooShort}
        className="self-start"
      >
        {generateResume.isPending ? "Generating... this can take up to a minute" : "Generate with AI"}
      </Button>
    </div>
  );
}
