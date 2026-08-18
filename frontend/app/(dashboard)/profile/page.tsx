"use client";

import { useState } from "react";
import { BadgeCheck, GraduationCap, Layers, MoreHorizontal, User, Users } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AchievementsSection } from "@/features/profile/components/AchievementsSection";
import { AwardsSection } from "@/features/profile/components/AwardsSection";
import { CertificationsSection } from "@/features/profile/components/CertificationsSection";
import { CompetitionsSection } from "@/features/profile/components/CompetitionsSection";
import { CompletionBar } from "@/features/profile/components/CompletionBar";
import { EducationSection } from "@/features/profile/components/EducationSection";
import { ExperienceSection } from "@/features/profile/components/ExperienceSection";
import { HackathonsSection } from "@/features/profile/components/HackathonsSection";
import { LanguagesSection } from "@/features/profile/components/LanguagesSection";
import { LeadershipRolesSection } from "@/features/profile/components/LeadershipRolesSection";
import { OrganizationsSection } from "@/features/profile/components/OrganizationsSection";
import { PatentsSection } from "@/features/profile/components/PatentsSection";
import { ProfileBasicsForm } from "@/features/profile/components/ProfileBasicsForm";
import { ProfileCompletionChecklist } from "@/features/profile/components/ProfileCompletionChecklist";
import { ProjectsSection } from "@/features/profile/components/ProjectsSection";
import { ReferencesSection } from "@/features/profile/components/ReferencesSection";
import { ResearchSection } from "@/features/profile/components/ResearchSection";
import { SkillsSection } from "@/features/profile/components/SkillsSection";
import { VolunteerExperienceSection } from "@/features/profile/components/VolunteerExperienceSection";
import { useProfile } from "@/features/profile/hooks/use-profile";
import { UploadCvDialog } from "@/features/cv-import/components/UploadCvDialog";
import { useAuthStore } from "@/store/auth-store";

const TABS = [
  { value: "basics", label: "Basics", icon: User },
  { value: "core", label: "Core", icon: Layers },
  { value: "credentials", label: "Credentials", icon: BadgeCheck },
  { value: "academic", label: "Academic", icon: GraduationCap },
  { value: "community", label: "Community", icon: Users },
  { value: "other", label: "Other", icon: MoreHorizontal },
] as const;

type TabValue = (typeof TABS)[number]["value"];

export default function ProfilePage() {
  const { data: profile, isLoading, isError, refetch, isRefetching } = useProfile();
  const authUser = useAuthStore((state) => state.user);
  const [tab, setTab] = useState<TabValue>("basics");

  if (isLoading) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading profile...</p>
      </main>
    );
  }

  if (isError || !profile || !authUser) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
        <p className="text-sm text-destructive">Failed to load your profile.</p>
        <button
          type="button"
          onClick={() => refetch()}
          className="text-sm underline"
          disabled={isRefetching}
        >
          {isRefetching ? "Retrying..." : "Try again"}
        </button>
      </main>
    );
  }

  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 px-4 py-8 sm:px-6 lg:py-10">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-3">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Your profile</h1>
          <div className="max-w-sm">
            <CompletionBar
              percentage={profile.completion_percentage}
              infoContent={<ProfileCompletionChecklist user={authUser} onJump={setTab} />}
            />
          </div>
        </div>
        <UploadCvDialog
          triggerLabel="Import data"
          description="Upload a PDF of your existing resume. We'll extract what we can find and let you review everything before anything is added to your profile — nothing is invented and nothing is saved automatically."
        />
      </div>

      <Tabs value={tab} onValueChange={(value) => setTab(value as TabValue)}>
        <div className="-mx-4 overflow-x-auto no-scrollbar px-4 sm:mx-0 sm:px-0">
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
        </div>

        <TabsContent value="basics" className="mt-6">
          <div className="rounded-xl bg-card p-5 ring-1 ring-foreground/10">
            <ProfileBasicsForm profile={profile} user={authUser} />
          </div>
        </TabsContent>

        <TabsContent value="core" className="mt-6 flex flex-col gap-8">
          <EducationSection />
          <ExperienceSection />
          <ProjectsSection />
          <SkillsSection />
        </TabsContent>

        <TabsContent value="credentials" className="mt-6 flex flex-col gap-8">
          <CertificationsSection />
          <AchievementsSection />
          <AwardsSection />
          <PatentsSection />
        </TabsContent>

        <TabsContent value="academic" className="mt-6 flex flex-col gap-8">
          <ResearchSection />
          <HackathonsSection />
          <CompetitionsSection />
        </TabsContent>

        <TabsContent value="community" className="mt-6 flex flex-col gap-8">
          <VolunteerExperienceSection />
          <LeadershipRolesSection />
          <OrganizationsSection />
        </TabsContent>

        <TabsContent value="other" className="mt-6 flex flex-col gap-8">
          <LanguagesSection />
          <ReferencesSection />
        </TabsContent>
      </Tabs>
    </main>
  );
}
