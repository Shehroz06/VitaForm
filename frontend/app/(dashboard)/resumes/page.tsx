"use client";

import { useSearchParams } from "next/navigation";
import { CreateResumeDialog } from "@/features/resumes/components/CreateResumeDialog";
import { GenerateResumeDialog } from "@/features/resumes/components/GenerateResumeDialog";
import { ResumeList } from "@/features/resumes/components/ResumeList";
import { useJob } from "@/features/jobs/hooks/use-jobs";

export default function ResumesPage() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get("jobId");

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Resumes</h1>
        <div className="flex gap-2">
          {jobId ? <JobPrefilledGenerateDialog jobId={jobId} /> : <GenerateResumeDialog />}
          <CreateResumeDialog />
        </div>
      </div>
      <ResumeList />
    </main>
  );
}

function JobPrefilledGenerateDialog({ jobId }: { jobId: string }) {
  const { data: job, isLoading } = useJob(jobId);

  if (isLoading || !job) {
    return <GenerateResumeDialog />;
  }

  return (
    <GenerateResumeDialog
      key={job.id}
      autoOpen
      initialValues={{
        jobDescription: job.raw_text,
        targetRole: job.title,
        targetCompany: job.company_name ?? "",
      }}
    />
  );
}
