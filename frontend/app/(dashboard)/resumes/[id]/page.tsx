"use client";

import { use } from "react";
import { ResumeBuilder } from "@/features/resumes/components/ResumeBuilder";

export default function ResumeBuilderPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  return <ResumeBuilder resumeId={id} />;
}
