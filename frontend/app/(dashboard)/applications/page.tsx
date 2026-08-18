"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Briefcase, IdCard, Mail } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CoverLetterList } from "@/features/companion/components/CoverLetterList";
import { GenerateCoverLetterForm } from "@/features/companion/components/GenerateCoverLetterForm";
import { GenerateLinkedinForm } from "@/features/companion/components/GenerateLinkedinForm";
import { LinkedinList } from "@/features/companion/components/LinkedinList";
import { JobList } from "@/features/jobs/components/JobList";
import { SaveJobForm } from "@/features/jobs/components/SaveJobForm";

const TABS = [
  { value: "jobs", label: "Jobs", icon: Briefcase },
  { value: "cover-letters", label: "Cover Letters", icon: Mail },
  { value: "linkedin", label: "LinkedIn", icon: IdCard },
] as const;

type TabValue = (typeof TABS)[number]["value"];

function ApplicationsPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialTab = (searchParams.get("tab") as TabValue) ?? "jobs";
  const [tab, setTab] = useState<TabValue>(TABS.some((t) => t.value === initialTab) ? initialTab : "jobs");

  const handleTabChange = (value: string) => {
    setTab(value as TabValue);
    router.replace(`/applications?tab=${value}`, { scroll: false });
  };

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8 sm:px-6 lg:py-10">
      <PageHeader title="Applications" />

      <Tabs value={tab} onValueChange={handleTabChange}>
        <TabsList className="h-auto w-full justify-start gap-1 bg-transparent p-0">
          {TABS.map(({ value, label, icon: Icon }) => (
            <TabsTrigger
              key={value}
              value={value}
              className="gap-1.5 rounded-lg border-none px-3 py-1.5 text-muted-foreground data-active:bg-accent data-active:text-accent-foreground dark:data-active:bg-accent dark:data-active:text-accent-foreground"
            >
              <Icon className="size-4" />
              {label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="jobs" className="mt-6 flex flex-col gap-6">
          <SaveJobForm />
          <JobList />
        </TabsContent>
        <TabsContent value="cover-letters" className="mt-6 flex flex-col gap-6">
          <GenerateCoverLetterForm />
          <CoverLetterList />
        </TabsContent>
        <TabsContent value="linkedin" className="mt-6 flex flex-col gap-6">
          <GenerateLinkedinForm />
          <LinkedinList />
        </TabsContent>
      </Tabs>
    </main>
  );
}

export default function ApplicationsPage() {
  return (
    <Suspense fallback={null}>
      <ApplicationsPageContent />
    </Suspense>
  );
}
