"use client";

import { useSearchParams } from "next/navigation";
import { PageHeader } from "@/components/layout/PageHeader";
import { GenerateResumeForm } from "@/features/resumes/components/GenerateResumeForm";
import { ResumeList } from "@/features/resumes/components/ResumeList";
import { useJob } from "@/features/jobs/hooks/use-jobs";

export default function ResumesPage() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get("jobId");
  const templateId = searchParams.get("templateId");
  const accentColor = searchParams.get("accentColor");

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8 sm:px-6 lg:py-10">
      <PageHeader
        title="Resumes"
        description="Every version you save is kept — nothing is ever silently overwritten."
      />

      {jobId ? (
        <JobPrefilledForm jobId={jobId} templateId={templateId} accentColor={accentColor} />
      ) : (
        <GenerateResumeForm
          presetTemplateId={templateId ?? undefined}
          presetAccentColor={accentColor ?? undefined}
        />
      )}

      <ResumeList />
    </main>
  );
}

function JobPrefilledForm({
  jobId,
  templateId,
  accentColor,
}: {
  jobId: string;
  templateId: string | null;
  accentColor: string | null;
}) {
  const { data: job, isLoading } = useJob(jobId);

  if (isLoading || !job) {
    return (
      <GenerateResumeForm
        presetTemplateId={templateId ?? undefined}
        presetAccentColor={accentColor ?? undefined}
      />
    );
  }

  return (
    <GenerateResumeForm
      key={job.id}
      presetTemplateId={templateId ?? undefined}
      presetAccentColor={accentColor ?? undefined}
      initialValues={{
        jobDescription: job.raw_text,
        targetRole: job.title,
        targetCompany: job.company_name ?? "",
      }}
    />
  );
}
