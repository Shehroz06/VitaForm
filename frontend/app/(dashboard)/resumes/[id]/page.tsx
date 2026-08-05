"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { use } from "react";
import { ResumeBuilder } from "@/features/resumes/components/ResumeBuilder";

export default function ResumeBuilderPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-6 py-10">
      <Link
        href="/resumes"
        className="flex items-center gap-1 text-sm text-muted-foreground hover:underline"
      >
        <ArrowLeft className="size-4" /> Back to resumes
      </Link>
      <ResumeBuilder resumeId={id} />
    </main>
  );
}
