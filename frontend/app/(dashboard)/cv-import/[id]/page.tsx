"use client";

import { use } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { ImportSessionReview } from "@/features/cv-import/components/ImportSessionReview";

export default function CvImportReviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8 sm:px-6 lg:py-10">
      <PageHeader title="Review your import" backHref="/profile" backLabel="Back to profile" />
      <ImportSessionReview sessionId={id} />
    </main>
  );
}
