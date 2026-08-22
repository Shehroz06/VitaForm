"use client";

import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { ArrowLeft, Code2, FileOutput, Shrink, Undo2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
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
import { ResumePreviewCard } from "@/features/resumes/components/ResumePreviewCard";
import { ResumeSectionNav } from "@/features/resumes/components/ResumeSectionNav";
import { SectionEditor, SummaryEditor } from "@/features/resumes/components/SectionEditor";
import { TemplateCustomizer } from "@/features/resumes/components/TemplateCustomizer";
import { TemplateSelector } from "@/features/resumes/components/TemplateSelector";
import { VersionHistory } from "@/features/resumes/components/VersionHistory";
import { resumeService } from "@/features/resumes/services/resume-service";
import { configToStyle, styleToConfig } from "@/features/resumes/style-mapping";
import {
  CORE_SECTIONS,
  ITEM_EDITABLE_SECTIONS,
  SECTION_LABELS,
  SECTION_ORDER,
} from "@/features/resumes/section-meta";
import {
  useAutofitResume,
  useAutofitResumeAggressive,
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
} from "@/features/resumes/templates/item-mappers";
import type { ResumePreviewItem } from "@/features/resumes/templates/types";
import type {
  ContactVisibility,
  Resume,
  ResumeContent,
  ResumeSection,
  ResumeVersion,
  SectionType,
} from "@/features/resumes/types";
import { ApiError } from "@/services/api-client";

interface BuilderState {
  summary: string;
  contact_visibility: ContactVisibility;
  sections: ResumeSection[];
  style: TemplateConfig;
  descriptionOverrides: Record<string, string>;
  titleOverrides: Record<string, string>;
  subtitleOverrides: Record<string, string>;
}

function toBuilderState(
  content: ResumeContent,
  versionNumber: number,
  templateDefaultConfig: TemplateConfig,
): BuilderState {
  const bySectionType = new Map(content.sections.map((s) => [s.section_type, s]));
  // Preserve the saved section order (so a reorder round-trips through
  // autosave/reload) rather than always resetting to the canonical
  // SECTION_ORDER -- any section type missing from a saved version (an
  // older resume, or a type introduced after it was created) is appended
  // at the end so nothing is silently dropped.
  const savedOrder = content.sections.map((s) => s.section_type);
  const missingTypes = SECTION_ORDER.filter((type) => !bySectionType.has(type));
  const orderedTypes = [...savedOrder, ...missingTypes];
  return {
    summary: content.summary ?? "",
    contact_visibility: content.contact_visibility,
    sections: orderedTypes.map(
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
    descriptionOverrides: content.description_overrides ?? {},
    titleOverrides: content.title_overrides ?? {},
    subtitleOverrides: content.subtitle_overrides ?? {},
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
    description_overrides: state.descriptionOverrides,
    title_overrides: state.titleOverrides,
    subtitle_overrides: state.subtitleOverrides,
  };
}

const _PLACEHOLDER_SUMMARY =
  "Experienced professional with a track record of delivering results across engineering, research, and product work.";

/** A "fill every section with everything on your profile" ResumeContent --
 * not this resume's actual saved selection, which might be sparse (a
 * work-in-progress draft with only a couple of items toggled on). The
 * template picker's comparison cards use this instead of the real
 * selection so choosing a template is judged against a realistic amount
 * of content, not whatever happens to be checked at that moment. */
function buildMaximalPreviewContent(
  summary: string,
  itemsByType: Record<Exclude<SectionType, "summary">, ResumePreviewItem[]>,
): ResumeContent {
  return {
    summary: summary.trim() || _PLACEHOLDER_SUMMARY,
    contact_visibility: {
      phone: true,
      location: true,
      website: true,
      github: true,
      linkedin: true,
      email: true,
    },
    sections: SECTION_ORDER.map((type) =>
      type === "summary"
        ? { section_type: type, custom_title: null, visible: true, item_ids: [] }
        : {
            section_type: type,
            custom_title: null,
            visible: true,
            item_ids: itemsByType[type].map((item) => item.id),
          },
    ),
    style: configToStyle({ accentColor: "#1a1a1a", fontFamily: "arial", spacing: "cozy" }),
    description_overrides: {},
    title_overrides: {},
    subtitle_overrides: {},
  };
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
  const queryClient = useQueryClient();
  const updateResume = useUpdateResume();
  const updateContent = useUpdateResumeContent(resumeId);
  const autosaveContent = useAutosaveResumeContent(resumeId);
  const exportResume = useExportResume(resumeId);
  const autofitResume = useAutofitResume(resumeId);
  const autofitResumeAggressive = useAutofitResumeAggressive(resumeId);
  const { data: templates } = useResumeTemplates();

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
  const [isExportingTex, setIsExportingTex] = useState(false);

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

  const maximalPreviewContent = buildMaximalPreviewContent(state.summary, itemsByType);

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

  const moveSection = (index: number, direction: -1 | 1) => {
    setState((prev) => {
      const target = index + direction;
      if (target < 0 || target >= prev.sections.length) return prev;
      const sections = [...prev.sections];
      [sections[index], sections[target]] = [sections[target], sections[index]];
      return { ...prev, sections };
    });
  };

  const overrideKeyFor = {
    title: "titleOverrides",
    subtitle: "subtitleOverrides",
    description: "descriptionOverrides",
  } as const;

  const updateOverride = (
    field: "title" | "subtitle" | "description",
    itemId: string,
    value: string,
  ) => {
    setState((prev) => {
      const key = overrideKeyFor[field];
      const next = { ...prev[key] };
      if (value.trim()) {
        next[itemId] = value;
      } else {
        delete next[itemId];
      }
      return { ...prev, [key]: next };
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
        onSuccess: () => {
          toast.success("Template updated.");
          // The rendered preview image is a function of resume.template_id,
          // not just the content useAutosaveResumeContent already
          // invalidates -- switching templates needs its own invalidation.
          queryClient.invalidateQueries({ queryKey: ["resumes", resumeId, "preview"] });
        },
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

  const handleAutofit = () => {
    autofitResume.mutate(undefined, {
      onSuccess: (result) => {
        setState((prev) => ({ ...prev, style: styleToConfig(result.version.content.style) }));
        toast[result.overflowing ? "warning" : "success"](
          result.overflowing
            ? "Tightened spacing as much as possible, but content still exceeds one page — remove or shorten something."
            : "Resume now fits one page.",
        );
      },
      onError: (error) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to auto-fit resume.");
      },
    });
  };

  const handleAutofitAggressive = () => {
    autofitResumeAggressive.mutate(undefined, {
      onSuccess: (result) => {
        // Unlike plain autofit (style only), this can also condense
        // descriptions and drop items -- sync everything the server could
        // have changed, keeping summary/contact_visibility/title+subtitle
        // overrides as-is since page_fit.py never touches those.
        setState((prev) => ({
          ...prev,
          sections: result.version.content.sections,
          style: styleToConfig(result.version.content.style),
          descriptionOverrides: result.version.content.description_overrides ?? {},
        }));
        toast[result.overflowing ? "warning" : "success"](
          result.overflowing
            ? "Shortened and trimmed as much as possible, but content still exceeds one page — remove something yourself."
            : "Resume now fits one page — some descriptions were shortened or lower-priority items removed. Undo (Ctrl/Cmd+Z) if you'd rather choose yourself.",
        );
      },
      onError: (error) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to auto-fit resume.");
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

  const handleExportTex = async () => {
    setIsExportingTex(true);
    try {
      await resumeService.exportTex(resumeId, `${title || "resume"}.tex`);
      toast.success(".tex source downloaded.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Failed to download .tex source.");
    } finally {
      setIsExportingTex(false);
    }
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
            resumeId={resumeId}
            currentSlug={currentSlug}
            currentName={currentTemplate?.name ?? "Template"}
            previewContent={maximalPreviewContent}
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
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  disabled={autofitResume.isPending || autofitResumeAggressive.isPending}
                  variant="outline"
                  size="sm"
                  className="gap-1.5"
                  title="Fit this resume to one page"
                >
                  <Shrink className="size-4" />
                  {autofitResume.isPending || autofitResumeAggressive.isPending
                    ? "Fitting..."
                    : "Auto-fit"}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                <DropdownMenuItem onClick={handleAutofit}>
                  <Shrink className="size-4" />
                  Auto-fit
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={handleAutofitAggressive}
                  className="text-amber-700 dark:text-amber-500"
                  title="Go further: shorten descriptions or remove the lowest-priority items if needed to fit one page"
                >
                  <Shrink className="size-4" />
                  Extreme fit
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  disabled={exportResume.isPending || isExportingTex}
                  size="sm"
                  className="gap-1.5"
                >
                  <FileOutput className="size-4" />
                  {exportResume.isPending ? "Exporting..." : "Export CV"}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleExport}>
                  <FileOutput className="size-4" />
                  Export PDF
                </DropdownMenuItem>
                {currentSlug === "ats_safe" && (
                  <DropdownMenuItem
                    onClick={handleExportTex}
                    title="Download the raw .tex source this template compiles -- verify or recompile it yourself, e.g. in Overleaf"
                  >
                    <Code2 className="size-4" />
                    Download .tex
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      <details className="group mx-4 mt-4 rounded-xl bg-card ring-1 ring-foreground/10 lg:hidden">
        <summary className="flex cursor-pointer list-none items-center justify-between px-4 py-3 text-sm font-medium text-foreground">
          Preview
          <span className="text-xs text-muted-foreground group-open:hidden">Tap to show</span>
        </summary>
        <div className="border-t border-border p-4">
          <ResumePreviewCard resumeId={resumeId} />
        </div>
      </details>

      <div className="mx-auto grid w-full max-w-[1400px] flex-1 gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[180px_1fr_430px] lg:items-start">
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
                  resumeId={resumeId}
                  open={expanded.has("summary")}
                  onToggleOpen={() => toggleOpen("summary")}
                  onSectionChange={(next) => updateSection(index, next)}
                  onSummaryChange={(text) => setState((prev) => ({ ...prev, summary: text }))}
                  onMoveUp={() => moveSection(index, -1)}
                  onMoveDown={() => moveSection(index, 1)}
                  canMoveUp={index > 0}
                  canMoveDown={index < state.sections.length - 1}
                />
              ) : (
                <SectionEditor
                  key={section.section_type}
                  section={section}
                  defaultTitle={SECTION_LABELS[section.section_type]}
                  items={itemsByType[section.section_type]}
                  editable={ITEM_EDITABLE_SECTIONS.has(section.section_type)}
                  open={expanded.has(section.section_type)}
                  onToggleOpen={() => toggleOpen(section.section_type)}
                  onChange={(next) => updateSection(index, next)}
                  onMoveUp={() => moveSection(index, -1)}
                  onMoveDown={() => moveSection(index, 1)}
                  canMoveUp={index > 0}
                  canMoveDown={index < state.sections.length - 1}
                  resumeId={resumeId}
                  titleOverrides={state.titleOverrides}
                  subtitleOverrides={state.subtitleOverrides}
                  descriptionOverrides={state.descriptionOverrides}
                  onOverrideChange={updateOverride}
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
          <ResumePreviewCard resumeId={resumeId} />
        </aside>
      </div>
    </div>
  );
}
