import type { ComponentType } from "react";
import type { FontFamily, SectionType, Spacing } from "@/features/resumes/types";

/**
 * The one shape every template renders from. Built once (in item-mappers.ts)
 * from the raw profile API objects, so no template component ever touches
 * an Education/Experience/Project/etc. type directly -- templates are pure
 * presentation over this normalized contract.
 */
export interface ResumePreviewItem {
  id: string;
  title: string;
  subtitle?: string;
  /** Short qualifier shown near the title -- employment type, patent status,
   * a grade, a language's proficiency level. Not every section uses this. */
  meta?: string;
  /** Pre-formatted, e.g. "Jan 2021 — Present". Already localized/resolved
   * so templates never format dates themselves. */
  dateRange?: string;
  description?: string | null;
  tags?: string[];
  links?: string[];
}

export interface ResumeTemplateSection {
  type: Exclude<SectionType, "summary">;
  title: string;
  items: ResumePreviewItem[];
}

export interface ResumeTemplateData {
  fullName: string;
  headline: string | null;
  contactLine: string[];
  summary: { title: string; text: string } | null;
  sections: ResumeTemplateSection[];
}

export type TemplateSlug = "classic" | "modern" | "minimal" | "compact" | "executive" | "ats_safe";

// Re-exported under the Template* name for call sites in this directory --
// the canonical definitions live in resumes/types.ts, since they originate
// from the backend's ResumeStyle schema, not from the preview system.
export type TemplateFontFamily = FontFamily;
export type TemplateSpacing = Spacing;

/**
 * The visual knobs a template renders with, independent of its structure.
 * Every template must read exclusively from this object for color/font/
 * spacing rather than hardcoding values, so the same resume data can be
 * re-rendered with different configs without touching template code.
 */
export interface TemplateConfig {
  accentColor: string;
  fontFamily: TemplateFontFamily;
  spacing: TemplateSpacing;
  /** Computed-only content-fit scale (0.8-1.0), optional since only
   * AI-generated resumes ever set it. Defaults to 1 (no shrink) wherever
   * unset -- template defaultConfigs in registry.tsx don't need it. */
  contentDensity?: number;
}

export interface TemplateProps {
  data: ResumeTemplateData;
  config: TemplateConfig;
}

export interface TemplateDefinition {
  slug: TemplateSlug;
  name: string;
  description: string;
  component: ComponentType<TemplateProps>;
  defaultConfig: TemplateConfig;
}
