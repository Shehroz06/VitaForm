"use client";

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
import { ProjectsSection } from "@/features/profile/components/ProjectsSection";
import { ReferencesSection } from "@/features/profile/components/ReferencesSection";
import { ResearchSection } from "@/features/profile/components/ResearchSection";
import { SkillsSection } from "@/features/profile/components/SkillsSection";
import { VolunteerExperienceSection } from "@/features/profile/components/VolunteerExperienceSection";
import { useProfile } from "@/features/profile/hooks/use-profile";

export default function ProfilePage() {
  const { data: profile, isLoading, isError, refetch, isRefetching } = useProfile();

  if (isLoading) {
    return (
      <main className="mx-auto flex max-w-2xl flex-1 items-center justify-center px-6">
        <p className="text-sm text-muted-foreground">Loading profile...</p>
      </main>
    );
  }

  if (isError || !profile) {
    return (
      <main className="mx-auto flex max-w-2xl flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
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
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-8 px-6 py-10">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold">Your profile</h1>
        <CompletionBar percentage={profile.completion_percentage} />
      </div>

      <ProfileBasicsForm profile={profile} />
      <EducationSection />
      <ExperienceSection />
      <ProjectsSection />
      <SkillsSection />
      <AchievementsSection />
      <CertificationsSection />
      <AwardsSection />
      <ResearchSection />
      <VolunteerExperienceSection />
      <LeadershipRolesSection />
      <OrganizationsSection />
      <LanguagesSection />
      <ReferencesSection />
      <HackathonsSection />
      <CompetitionsSection />
      <PatentsSection />
    </main>
  );
}
