"use client";

import { GenerateLinkedinDialog } from "@/features/companion/components/GenerateLinkedinDialog";
import { LinkedinList } from "@/features/companion/components/LinkedinList";

export default function LinkedinPage() {
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">LinkedIn</h1>
        <GenerateLinkedinDialog />
      </div>
      <LinkedinList />
    </main>
  );
}
