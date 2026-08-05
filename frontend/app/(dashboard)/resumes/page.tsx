"use client";

import { CreateResumeDialog } from "@/features/resumes/components/CreateResumeDialog";
import { GenerateResumeDialog } from "@/features/resumes/components/GenerateResumeDialog";
import { ResumeList } from "@/features/resumes/components/ResumeList";

export default function ResumesPage() {
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Resumes</h1>
        <div className="flex gap-2">
          <GenerateResumeDialog />
          <CreateResumeDialog />
        </div>
      </div>
      <ResumeList />
    </main>
  );
}
