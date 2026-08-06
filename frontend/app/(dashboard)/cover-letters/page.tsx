"use client";

import { CoverLetterList } from "@/features/companion/components/CoverLetterList";
import { GenerateCoverLetterDialog } from "@/features/companion/components/GenerateCoverLetterDialog";

export default function CoverLettersPage() {
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Cover Letters</h1>
        <GenerateCoverLetterDialog />
      </div>
      <CoverLetterList />
    </main>
  );
}
