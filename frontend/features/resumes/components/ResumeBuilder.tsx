"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAchievementList } from "@/features/profile/hooks/use-achievements";
import { useAwardList } from "@/features/profile/hooks/use-awards";
import { useCertificationList } from "@/features/profile/hooks/use-certifications";
import { useEducationList } from "@/features/profile/hooks/use-education";
import { useExperienceList } from "@/features/profile/hooks/use-experience";
import { useProjectList } from "@/features/profile/hooks/use-projects";
import { useSkillList } from "@/features/profile/hooks/use-skills";
import { SectionEditor, SummaryEditor } from "@/features/resumes/components/SectionEditor";
import { VersionHistory } from "@/features/resumes/components/VersionHistory";
import { useUpdateResumeContent, useResumeContent } from "@/features/resumes/hooks/use-resume-content";
import { useResume, useUpdateResume } from "@/features/resumes/hooks/use-resumes";
import type {
  ContactVisibility,
  Resume,
  ResumeContent,
  ResumeSection,
  ResumeVersion,
  SectionType,
} from "@/features/resumes/types";
import { ApiError } from "@/services/api-client";

const SECTION_ORDER: SectionType[] = [
  "summary",
  "education",
  "experience",
  "projects",
  "skills",
  "certifications",
  "achievements",
  "awards",
];

const SECTION_LABELS: Record<Exclude<SectionType, "summary">, string> = {
  education: "Education",
  experience: "Experience",
  projects: "Projects",
  skills: "Skills",
  certifications: "Certifications",
  achievements: "Achievements",
  awards: "Awards",
};

interface BuilderState {
  summary: string;
  contact_visibility: ContactVisibility;
  sections: ResumeSection[];
}

function toBuilderState(content: ResumeContent): BuilderState {
  const bySectionType = new Map(content.sections.map((s) => [s.section_type, s]));
  return {
    summary: content.summary ?? "",
    contact_visibility: content.contact_visibility,
    sections: SECTION_ORDER.map(
      (type) =>
        bySectionType.get(type) ?? {
          section_type: type,
          custom_title: null,
          visible: true,
          item_ids: [],
        },
    ),
  };
}

function toContentPayload(state: BuilderState): ResumeContent {
  return {
    summary: state.summary.trim() || null,
    contact_visibility: state.contact_visibility,
    sections: state.sections.map((s) => ({
      ...s,
      item_ids: s.section_type === "summary" ? [] : s.item_ids,
    })),
  };
}

export function ResumeBuilder({ resumeId }: { resumeId: string }) {
  const { data: resume, isLoading: isResumeLoading, isError: isResumeError } = useResume(resumeId);
  const { data: version, isLoading: isVersionLoading, isError: isVersionError } =
    useResumeContent(resumeId);

  if (isResumeLoading || isVersionLoading) {
    return <p className="text-sm text-muted-foreground">Loading resume...</p>;
  }
  if (isResumeError || isVersionError || !resume || !version) {
    return <p className="text-sm text-destructive">Failed to load resume.</p>;
  }

  // Keying on the version id remounts the form (and its lazily-initialized
  // local state) whenever a fresh version loads, instead of syncing state
  // from props via an effect.
  return <ResumeBuilderForm key={version.id} resumeId={resumeId} resume={resume} version={version} />;
}

function ResumeBuilderForm({
  resumeId,
  resume,
  version,
}: {
  resumeId: string;
  resume: Resume;
  version: ResumeVersion;
}) {
  const updateResume = useUpdateResume();
  const updateContent = useUpdateResumeContent(resumeId);

  const [title, setTitle] = useState(resume.title);
  const [state, setState] = useState<BuilderState>(() => toBuilderState(version.content));

  const { data: education } = useEducationList();
  const { data: experience } = useExperienceList();
  const { data: projects } = useProjectList();
  const { data: skills } = useSkillList();
  const { data: certifications } = useCertificationList();
  const { data: achievements } = useAchievementList();
  const { data: awards } = useAwardList();

  const itemsByType: Record<Exclude<SectionType, "summary">, { id: string; label: string }[]> = {
    education: (education ?? []).map((e) => ({
      id: e.id,
      label: `${e.institution_name} — ${e.degree}`,
    })),
    experience: (experience ?? []).map((e) => ({
      id: e.id,
      label: `${e.job_title} @ ${e.company_name}`,
    })),
    projects: (projects ?? []).map((p) => ({ id: p.id, label: p.title })),
    skills: (skills ?? []).map((s) => ({ id: s.id, label: s.name })),
    certifications: (certifications ?? []).map((c) => ({
      id: c.id,
      label: `${c.name} — ${c.issuing_organization}`,
    })),
    achievements: (achievements ?? []).map((a) => ({ id: a.id, label: a.title })),
    awards: (awards ?? []).map((a) => ({ id: a.id, label: a.title })),
  };

  const updateSection = (index: number, next: ResumeSection) => {
    setState((prev) => {
      const sections = [...prev.sections];
      sections[index] = next;
      return { ...prev, sections };
    });
  };

  const handleSaveTitle = () => {
    if (title.trim() === resume.title || !title.trim()) return;
    updateResume.mutate(
      { id: resume.id, payload: { title: title.trim() } },
      { onError: () => toast.error("Failed to update title.") },
    );
  };

  const handleSaveContent = () => {
    updateContent.mutate(toContentPayload(state), {
      onSuccess: () => toast.success("Resume saved as a new version."),
      onError: (error) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to save resume.");
      },
    });
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="resume-title">Title</Label>
        <Input
          id="resume-title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          onBlur={handleSaveTitle}
        />
      </div>

      <div className="flex flex-col gap-2">
        <h2 className="text-sm font-semibold text-muted-foreground">Contact info shown</h2>
        <div className="flex flex-wrap gap-4">
          {(Object.keys(state.contact_visibility) as (keyof ContactVisibility)[]).map((field) => (
            <label key={field} className="flex items-center gap-2 text-sm capitalize">
              <Checkbox
                checked={state.contact_visibility[field]}
                onCheckedChange={(checked) =>
                  setState((prev) => ({
                    ...prev,
                    contact_visibility: { ...prev.contact_visibility, [field]: checked === true },
                  }))
                }
              />
              {field}
            </label>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {state.sections.map((section, index) =>
          section.section_type === "summary" ? (
            <SummaryEditor
              key="summary"
              section={section}
              summary={state.summary}
              onSectionChange={(next) => updateSection(index, next)}
              onSummaryChange={(text) => setState((prev) => ({ ...prev, summary: text }))}
            />
          ) : (
            <SectionEditor
              key={section.section_type}
              section={section}
              defaultTitle={SECTION_LABELS[section.section_type]}
              items={itemsByType[section.section_type]}
              onChange={(next) => updateSection(index, next)}
            />
          ),
        )}
      </div>

      <Button onClick={handleSaveContent} disabled={updateContent.isPending} className="self-start">
        {updateContent.isPending ? "Saving..." : "Save (creates a new version)"}
      </Button>

      <VersionHistory resumeId={resumeId} />
    </div>
  );
}
