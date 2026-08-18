"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowLeft, FileOutput, Undo2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { useProfile } from "@/features/profile/hooks/use-profile";
import { useAchievementList } from "@/features/profile/hooks/use-achievements";
import { useAwardList } from "@/features/profile/hooks/use-awards";
import { useCertificationList } from "@/features/profile/hooks/use-certifications";
import { useCompetitionList } from "@/features/profile/hooks/use-competitions";
import { useEducationList } from "@/features/profile/hooks/use-education";
import { useExperienceList } from "@/features/profile/hooks/use-experience";
import { useHackathonList } from "@/features/profile/hooks/use-hackathons";
import { useLanguageList } from "@/features/profile/hooks/use-languages";
import { useLeadershipRoleList } from "@/features/profile/hooks/use-leadership-roles";
import { useOrganizationList } from "@/features/profile/hooks/use-organizations";
import { usePatentList } from "@/features/profile/hooks/use-patents";
import { useProjectList } from "@/features/profile/hooks/use-projects";
import { useReferenceList } from "@/features/profile/hooks/use-references";
import { useResearchList } from "@/features/profile/hooks/use-research";
import { useSkillList } from "@/features/profile/hooks/use-skills";
import { useVolunteerExperienceList } from "@/features/profile/hooks/use-volunteer-experience";
import { ResumeSectionNav } from "@/features/resumes/components/ResumeSectionNav";
import { SectionEditor, SummaryEditor } from "@/features/resumes/components/SectionEditor";
import { TemplateCustomizer } from "@/features/resumes/components/TemplateCustomizer";
import { TemplateSelector } from "@/features/resumes/components/TemplateSelector";
import { VersionHistory } from "@/features/resumes/components/VersionHistory";
import { CORE_SECTIONS, SECTION_LABELS, SECTION_ORDER } from "@/features/resumes/section-meta";
import {
  useAutosaveResumeContent,
  useExportResume,
  useResumeContent,
  useUpdateResumeContent,
} from "@/features/resumes/hooks/use-resume-content";
import { useResume, useResumeTemplates, useUpdateResume } from "@/features/resumes/hooks/use-resumes";
import { getTemplateDefinition } from "@/features/resumes/templates/registry";
import type { TemplateConfig } from "@/features/resumes/templates/types";
import {
  mapAchievements,
  mapAwards,
  mapCertifications,
  mapCompetitions,
  mapEducation,
  mapExperience,
  mapHackathons,
  mapLanguages,
  mapLeadershipRoles,
  mapOrganizations,
  mapPatents,
  mapProjects,
  mapReferences,
  mapResearch,
  mapSkills,
  mapVolunteerExperience,
  toSelectable,
} from "@/features/resumes/templates/item-mappers";
import { TemplateRenderer } from "@/features/resumes/templates/TemplateRenderer";
import type { ResumePreviewItem, ResumeTemplateData } from "@/features/resumes/templates/types";
import type {
  ContactVisibility,
  Resume,
  ResumeContent,
  ResumeSection,
  ResumeStyle,
  ResumeVersion,
  SectionType,
} from "@/features/resumes/types";
import { ApiError } from "@/services/api-client";
import { useAuthStore } from "@/store/auth-store";

interface BuilderState {
  summary: string;
  contact_visibility: ContactVisibility;
  sections: ResumeSection[];
  style: TemplateConfig;
}

function styleToConfig(style: ResumeStyle): TemplateConfig {
  return {
    accentColor: style.accent_color,
    fontFamily: style.font_family,
    spacing: style.spacing,
    contentDensity: style.content_density,
  };
}

function configToStyle(config: TemplateConfig): ResumeStyle {
  return {
    accent_color: config.accentColor,
    font_family: config.fontFamily,
    spacing: config.spacing,
    content_density: config.contentDensity ?? 1,
  };
}

function toBuilderState(
  content: ResumeContent,
  versionNumber: number,
  templateDefaultConfig: TemplateConfig,
): BuilderState {
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
    // A version-1 resume has never been through a manual save, so its
    // content.style is still the backend's generic placeholder default --
    // show the template's own intended look until the user actually
    // customizes and saves, at which point content.style becomes authoritative.
    style: versionNumber <= 1 ? templateDefaultConfig : styleToConfig(content.style),
  };
}

const AUTOSAVE_DEBOUNCE_MS = 1500;
const UNDO_HISTORY_LIMIT = 20;

function toContentPayload(state: BuilderState): ResumeContent {
  return {
    summary: state.summary.trim() || null,
    contact_visibility: state.contact_visibility,
    sections: state.sections.map((s) => ({
      ...s,
      item_ids: s.section_type === "summary" ? [] : s.item_ids,
    })),
    style: configToStyle(state.style),
  };
}

interface PreviewProfile {
  headline: string | null;
  phone: string | null;
  location: string | null;
  website_url: string | null;
  github_url: string | null;
  linkedin_url: string | null;
}

/** Resume Data -> the normalized contract every template renders from.
 * Runs once per render, independent of which template is selected -- the
 * same output feeds whichever TemplateRenderer the user has open. */
function buildTemplateData(
  fullName: string,
  profile: PreviewProfile | undefined,
  email: string | undefined,
  state: BuilderState,
  itemsByType: Record<Exclude<SectionType, "summary">, ResumePreviewItem[]>,
): ResumeTemplateData {
  const contactLine = [
    state.contact_visibility.email && email,
    state.contact_visibility.phone && profile?.phone,
    state.contact_visibility.location && profile?.location,
    state.contact_visibility.website && profile?.website_url,
    state.contact_visibility.github && profile?.github_url,
    state.contact_visibility.linkedin && profile?.linkedin_url,
  ].filter((value): value is string => Boolean(value));

  const summarySection = state.sections.find((s) => s.section_type === "summary");
  const summary =
    summarySection?.visible && state.summary.trim()
      ? { title: summarySection.custom_title || "Summary", text: state.summary.trim() }
      : null;

  const sections = state.sections
    .filter(
      (s): s is ResumeSection & { section_type: Exclude<SectionType, "summary"> } =>
        s.section_type !== "summary" && s.visible && s.item_ids.length > 0,
    )
    .map((s) => {
      const byId = new Map(itemsByType[s.section_type].map((item) => [item.id, item]));
      const items = s.item_ids
        .map((id) => byId.get(id))
        .filter((item): item is ResumePreviewItem => Boolean(item));
      return { type: s.section_type, title: s.custom_title || SECTION_LABELS[s.section_type], items };
    })
    .filter((section) => section.items.length > 0);

  return { fullName, headline: profile?.headline ?? null, contactLine, summary, sections };
}

export function ResumeBuilder({ resumeId }: { resumeId: string }) {
  const { data: resume, isLoading: isResumeLoading, isError: isResumeError } = useResume(resumeId);
  const { data: version, isLoading: isVersionLoading, isError: isVersionError } =
    useResumeContent(resumeId);

  if (isResumeLoading || isVersionLoading) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading resume...</p>
      </main>
    );
  }
  if (isResumeError || isVersionError || !resume || !version) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-sm text-destructive">Failed to load resume.</p>
      </main>
    );
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
  const autosaveContent = useAutosaveResumeContent(resumeId);
  const exportResume = useExportResume(resumeId);
  const { data: templates } = useResumeTemplates();
  const user = useAuthStore((state) => state.user);
  const { data: profile } = useProfile();
  const fullName = [user?.first_name, user?.last_name].filter(Boolean).join(" ");

  const currentTemplate = templates?.find((t) => t.id === resume.template_id);
  const currentSlug = currentTemplate?.slug ?? "classic";
  const templateDefaultConfig = getTemplateDefinition(currentSlug).defaultConfig;

  const [title, setTitle] = useState(resume.title);
  const [state, setState] = useState<BuilderState>(() =>
    toBuilderState(version.content, version.version_number, templateDefaultConfig),
  );
  const [expanded, setExpanded] = useState<Set<SectionType>>(
    () => new Set<SectionType>(["summary", ...CORE_SECTIONS]),
  );
  const [isDirty, setIsDirty] = useState(false);

  // Undo history + autosave share one debounce: whenever the user pauses
  // editing for AUTOSAVE_DEBOUNCE_MS, the state as it was *before* this
  // batch of changes is pushed as a single undo step (coalescing something
  // like a run of keystrokes into one step, not one per keystroke), and the
  // current state is persisted in place via PATCH -- so Export always
  // reflects what's on screen without requiring an explicit Save first.
  const historyRef = useRef<BuilderState[]>([]);
  const lastCommittedRef = useRef<BuilderState>(state);
  const isFirstRenderRef = useRef(true);

  useEffect(() => {
    if (isFirstRenderRef.current) {
      isFirstRenderRef.current = false;
      return;
    }
    setIsDirty(true);
    const timer = setTimeout(() => {
      historyRef.current = [...historyRef.current, lastCommittedRef.current].slice(
        -UNDO_HISTORY_LIMIT,
      );
      lastCommittedRef.current = state;
      autosaveContent.mutate(toContentPayload(state), {
        onSuccess: () => setIsDirty(false),
      });
    }, AUTOSAVE_DEBOUNCE_MS);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- fires on every state change, nothing else needed
  }, [state]);

  const handleUndo = () => {
    const previous = historyRef.current.pop();
    if (!previous) {
      toast.info("Nothing to undo.");
      return;
    }
    lastCommittedRef.current = previous;
    setState(previous);
  };

  useEffect(() => {
    const handleKeydown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "z") {
        event.preventDefault();
        handleUndo();
      }
    };
    window.addEventListener("keydown", handleKeydown);
    return () => window.removeEventListener("keydown", handleKeydown);
  }, []);

  const { data: education } = useEducationList();
  const { data: experience } = useExperienceList();
  const { data: projects } = useProjectList();
  const { data: skills } = useSkillList();
  const { data: certifications } = useCertificationList();
  const { data: achievements } = useAchievementList();
  const { data: awards } = useAwardList();
  const { data: research } = useResearchList();
  const { data: volunteerExperience } = useVolunteerExperienceList();
  const { data: leadershipRoles } = useLeadershipRoleList();
  const { data: organizations } = useOrganizationList();
  const { data: languages } = useLanguageList();
  const { data: references } = useReferenceList();
  const { data: hackathons } = useHackathonList();
  const { data: competitions } = useCompetitionList();
  const { data: patents } = usePatentList();

  const itemsByType: Record<Exclude<SectionType, "summary">, ResumePreviewItem[]> = {
    education: mapEducation(education),
    experience: mapExperience(experience),
    projects: mapProjects(projects),
    skills: mapSkills(skills),
    certifications: mapCertifications(certifications),
    achievements: mapAchievements(achievements),
    awards: mapAwards(awards),
    research: mapResearch(research),
    volunteer_experience: mapVolunteerExperience(volunteerExperience),
    leadership_roles: mapLeadershipRoles(leadershipRoles),
    organizations: mapOrganizations(organizations),
    languages: mapLanguages(languages),
    references: mapReferences(references),
    hackathons: mapHackathons(hackathons),
    competitions: mapCompetitions(competitions),
    patents: mapPatents(patents),
  };

  const templateData = buildTemplateData(fullName, profile, user?.email, state, itemsByType);

  const updateStyle = (patch: Partial<TemplateConfig>) => {
    setState((prev) => ({ ...prev, style: { ...prev.style, ...patch } }));
  };

  const resetStyle = () => {
    setState((prev) => ({ ...prev, style: templateDefaultConfig }));
  };

  const updateSection = (index: number, next: ResumeSection) => {
    setState((prev) => {
      const sections = [...prev.sections];
      sections[index] = next;
      return { ...prev, sections };
    });
  };

  const toggleOpen = (type: SectionType) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  };

  const handleNavigate = (type: SectionType) => {
    setExpanded((prev) => new Set(prev).add(type));
    requestAnimationFrame(() => {
      document.getElementById(`section-${type}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  };

  const handleSaveTitle = () => {
    if (title.trim() === resume.title || !title.trim()) return;
    updateResume.mutate(
      { id: resume.id, payload: { title: title.trim() } },
      { onError: () => toast.error("Failed to update title.") },
    );
  };

  const handleTemplateChange = (templateId: string) => {
    if (templateId === resume.template_id) return;
    updateResume.mutate(
      { id: resume.id, payload: { template_id: templateId } },
      {
        onSuccess: () => toast.success("Template updated."),
        onError: () => toast.error("Failed to update template."),
      },
    );
  };

  const handleTemplateSelect = (slug: string) => {
    const template = templates?.find((t) => t.slug === slug);
    if (!template) return;
    handleTemplateChange(template.id);
    // Only follow the new template's look if the user never customized away
    // from the current template's own default -- a deliberate accent/font
    // choice should survive switching layouts, matching how a user expects
    // "my color choice" to persist independent of "which layout I picked."
    const isUnmodified =
      JSON.stringify(state.style) === JSON.stringify(templateDefaultConfig);
    if (isUnmodified) {
      setState((prev) => ({ ...prev, style: getTemplateDefinition(slug).defaultConfig }));
    }
  };

  const handleSaveContent = () => {
    updateContent.mutate(toContentPayload(state), {
      onSuccess: () => {
        toast.success("Resume saved as a new version.");
        setIsDirty(false);
      },
      onError: (error) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to save resume.");
      },
    });
  };

  const handleExport = () => {
    exportResume.mutate(undefined, {
      onSuccess: (file) => {
        toast.success("Resume exported.");
        window.open(file.url, "_blank", "noopener,noreferrer");
      },
      onError: (error) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to export resume.");
      },
    });
  };

  return (
    <div className="flex flex-1 flex-col">
      <div className="sticky top-14 z-30 border-b border-border bg-background/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1400px] flex-wrap items-center gap-3 px-4 py-3 sm:px-6">
          <Link
            href="/resumes"
            className="flex shrink-0 items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="size-4" />
          </Link>
          <Input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            onBlur={handleSaveTitle}
            className="h-9 max-w-xs border-transparent bg-transparent px-2 text-base font-medium shadow-none hover:bg-muted focus-visible:border-input focus-visible:bg-background"
            aria-label="Resume title"
          />
          <span className="hidden text-xs text-muted-foreground sm:inline">
            v{resume.latest_version_number}
          </span>
          <TemplateSelector
            currentSlug={currentSlug}
            currentName={currentTemplate?.name ?? "Template"}
            previewData={templateData}
            onSelect={handleTemplateSelect}
          />
          <TemplateCustomizer config={state.style} onChange={updateStyle} onReset={resetStyle} />
          <div className="ml-auto flex items-center gap-3">
            <span className="hidden text-xs text-muted-foreground sm:inline">
              {autosaveContent.isPending
                ? "Saving..."
                : autosaveContent.isError
                  ? "Autosave failed"
                  : isDirty
                    ? "Unsaved changes"
                    : "All changes saved"}
            </span>
            <Button
              onClick={handleUndo}
              variant="ghost"
              size="sm"
              className="gap-1.5 text-muted-foreground"
              title="Undo (Ctrl/Cmd+Z)"
            >
              <Undo2 className="size-4" />
              Undo
            </Button>
            <Button
              onClick={handleSaveContent}
              disabled={updateContent.isPending}
              variant="outline"
              size="sm"
            >
              {updateContent.isPending ? "Saving..." : "Save version"}
            </Button>
            <Button onClick={handleExport} disabled={exportResume.isPending} size="sm" className="gap-1.5">
              <FileOutput className="size-4" />
              {exportResume.isPending ? "Exporting..." : "Export PDF"}
            </Button>
          </div>
        </div>
      </div>

      <details className="group mx-4 mt-4 rounded-xl bg-card ring-1 ring-foreground/10 lg:hidden">
        <summary className="flex cursor-pointer list-none items-center justify-between px-4 py-3 text-sm font-medium text-foreground">
          Preview
          <span className="text-xs text-muted-foreground group-open:hidden">Tap to show</span>
        </summary>
        <div className="border-t border-border p-4">
          <TemplateRenderer slug={currentSlug} data={templateData} config={state.style} />
        </div>
      </details>

      <div className="mx-auto grid w-full max-w-[1400px] flex-1 gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[200px_1fr_560px] lg:items-start">
        <aside className="hidden lg:sticky lg:top-32 lg:block">
          <ResumeSectionNav sections={state.sections} onNavigate={handleNavigate} />
        </aside>

        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-2 rounded-xl bg-card p-4 ring-1 ring-foreground/10">
            <h2 className="text-xs font-medium text-muted-foreground">Contact info shown</h2>
            <div className="flex flex-wrap gap-x-4 gap-y-2">
              {(Object.keys(state.contact_visibility) as (keyof ContactVisibility)[]).map((field) => (
                <label key={field} className="flex items-center gap-1.5 text-sm capitalize">
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
                  open={expanded.has("summary")}
                  onToggleOpen={() => toggleOpen("summary")}
                  onSectionChange={(next) => updateSection(index, next)}
                  onSummaryChange={(text) => setState((prev) => ({ ...prev, summary: text }))}
                />
              ) : (
                <SectionEditor
                  key={section.section_type}
                  section={section}
                  defaultTitle={SECTION_LABELS[section.section_type]}
                  items={toSelectable(itemsByType[section.section_type])}
                  open={expanded.has(section.section_type)}
                  onToggleOpen={() => toggleOpen(section.section_type)}
                  onChange={(next) => updateSection(index, next)}
                />
              ),
            )}
          </div>

          <VersionHistory resumeId={resumeId} />
        </div>

        <aside
          className="hidden lg:sticky lg:top-32 lg:mx-auto lg:block lg:w-full"
          style={{
            // Cap by whichever is smaller: a comfortable print-scale width,
            // or whatever width keeps the full A4-ratio page inside the
            // viewport under the sticky offset. Without the height-aware
            // half, a wide preview taller than the screen forces the whole
            // page to scroll just to see its bottom -- the point of sticky
            // positioning is that it stays fully visible while the editor
            // column scrolls past it, not the other way around.
            maxWidth: "min(640px, calc((100vh - 11rem) * 0.7071))",
          }}
        >
          <TemplateRenderer slug={currentSlug} data={templateData} config={state.style} />
        </aside>
      </div>
    </div>
  );
}
