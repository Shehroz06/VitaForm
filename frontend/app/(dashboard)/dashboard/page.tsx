"use client";

import Link from "next/link";
import { Briefcase, FileText, IdCard, LayoutTemplate, Mail, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { OnboardingChecklist } from "@/components/dashboard/OnboardingChecklist";
import { useResumeList } from "@/features/resumes/hooks/use-resumes";
import { useJobList } from "@/features/jobs/hooks/use-jobs";
import { useCoverLetterList, useLinkedinList } from "@/features/companion/hooks/use-companion";
import { useProfile } from "@/features/profile/hooks/use-profile";
import { useAuthStore } from "@/store/auth-store";

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user);
  const { data: profile } = useProfile();
  const { data: resumes, isLoading: resumesLoading } = useResumeList();
  const { data: jobs } = useJobList();
  const { data: coverLetters } = useCoverLetterList();
  const { data: linkedinGenerations } = useLinkedinList();

  const recentResumes = [...(resumes ?? [])]
    .sort((a, b) => +new Date(b.updated_at) - +new Date(a.updated_at))
    .slice(0, 4);

  const stats = [
    { href: "/resumes", label: "Resumes", count: resumes?.length, icon: FileText },
    { href: "/applications?tab=jobs", label: "Saved jobs", count: jobs?.length, icon: Briefcase },
    {
      href: "/applications?tab=cover-letters",
      label: "Cover letters",
      count: coverLetters?.length,
      icon: Mail,
    },
    {
      href: "/applications?tab=linkedin",
      label: "LinkedIn drafts",
      count: linkedinGenerations?.length,
      icon: IdCard,
    },
  ];

  return (
    <main className="mx-auto flex w-full max-w-[1100px] flex-1 flex-col gap-8 px-4 py-8 sm:px-6 lg:py-10">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            {greeting()}{user?.first_name ? `, ${user.first_name}` : ""}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Here&apos;s what&apos;s happening with your career documents.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline" className="gap-1.5">
            <Link href="/templates">
              <LayoutTemplate className="size-4" />
              Browse templates
            </Link>
          </Button>
          <Button asChild className="gap-1.5">
            <Link href="/resumes">
              <Sparkles className="size-4" />
              Generate a resume
            </Link>
          </Button>
        </div>
      </div>

      {profile && (
        <OnboardingChecklist
          profileComplete={profile.completion_percentage >= 100}
          hasResumes={(resumes?.length ?? 0) > 0}
        />
      )}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {stats.map(({ href, label, count, icon: Icon }) => (
          <Link key={href} href={href}>
            <Card className="h-full transition-colors hover:bg-muted/40">
              <CardContent className="flex flex-col gap-2.5">
                <div className="flex size-8 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                  <Icon className="size-4" />
                </div>
                <div>
                  <p className="text-2xl font-semibold tabular-nums">{count ?? "–"}</p>
                  <p className="text-xs text-muted-foreground">{label}</p>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-lg font-medium">Recent resumes</h2>
          {resumes && resumes.length > 0 && (
            <Link href="/resumes" className="text-sm text-primary hover:underline">
              View all
            </Link>
          )}
        </div>

        {resumesLoading ? (
          <div className="grid gap-3 sm:grid-cols-2">
            {Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} className="h-20 rounded-xl" />
            ))}
          </div>
        ) : recentResumes.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center gap-3 py-8 text-center">
              <div className="flex size-10 items-center justify-center rounded-full bg-accent text-accent-foreground">
                <FileText className="size-5" />
              </div>
              <div>
                <p className="text-sm font-medium">No resumes yet</p>
                <p className="text-sm text-muted-foreground">
                  Generate one from your profile data, tailored to a role.
                </p>
              </div>
              <Button asChild className="gap-1.5">
                <Link href="/resumes">
                  <Sparkles className="size-4" />
                  Generate a resume
                </Link>
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {recentResumes.map((resume) => (
              <Link key={resume.id} href={`/resumes/${resume.id}`}>
                <Card className="h-full transition-colors hover:bg-muted/40">
                  <CardContent className="flex items-center gap-3">
                    <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                      <FileText className="size-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{resume.title}</p>
                      <p className="text-xs text-muted-foreground">
                        v{resume.latest_version_number} · updated{" "}
                        {new Date(resume.updated_at).toLocaleDateString()}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
