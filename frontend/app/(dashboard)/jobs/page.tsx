"use client";

import { JobList } from "@/features/jobs/components/JobList";
import { SaveJobDialog } from "@/features/jobs/components/SaveJobDialog";

export default function JobsPage() {
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Jobs</h1>
        <SaveJobDialog />
      </div>
      <JobList />
    </main>
  );
}
