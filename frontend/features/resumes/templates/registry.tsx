import { AtsSafeTemplate } from "@/features/resumes/templates/ats_safe/AtsSafeTemplate";
import { ClassicTemplate } from "@/features/resumes/templates/classic/ClassicTemplate";
import { CompactTemplate } from "@/features/resumes/templates/compact/CompactTemplate";
import { ExecutiveTemplate } from "@/features/resumes/templates/executive/ExecutiveTemplate";
import { MinimalTemplate } from "@/features/resumes/templates/minimal/MinimalTemplate";
import { ModernTemplate } from "@/features/resumes/templates/modern/ModernTemplate";
import type { TemplateDefinition, TemplateSlug } from "@/features/resumes/templates/types";

/**
 * The one place that knows every template that exists. Adding a template
 * means writing the component and registering it here -- nothing else in
 * the editor, selector, or renderer needs to change to pick it up.
 *
 * Slugs are shared with the backend's 6 real Jinja2/CSS templates (which
 * render the actual exported PDF) so the live in-app preview always matches
 * what "Export PDF" produces -- this registry never introduces a template
 * with no server-side counterpart.
 */
export const TEMPLATE_REGISTRY: Record<TemplateSlug, TemplateDefinition> = {
  classic: {
    slug: "classic",
    name: "Classic",
    description: "A clean, single-column, ATS-friendly layout.",
    component: ClassicTemplate,
    defaultConfig: { accentColor: "#1a1a1a", fontFamily: "arial", spacing: "cozy" },
  },
  modern: {
    slug: "modern",
    name: "Modern",
    description: "Bold headings with a strong accent, built for a contemporary look.",
    component: ModernTemplate,
    defaultConfig: { accentColor: "#2c4a6e", fontFamily: "calibri", spacing: "cozy" },
  },
  minimal: {
    slug: "minimal",
    name: "Minimal",
    description: "Light typography and generous whitespace for an understated resume.",
    component: MinimalTemplate,
    defaultConfig: { accentColor: "#4a5563", fontFamily: "arial", spacing: "relaxed" },
  },
  compact: {
    slug: "compact",
    name: "Compact",
    description: "Denser spacing that fits more on the page — for longer histories.",
    component: CompactTemplate,
    defaultConfig: { accentColor: "#1a1a1a", fontFamily: "arial", spacing: "compact" },
  },
  executive: {
    slug: "executive",
    name: "Executive",
    description: "A centered, formal layout for senior and leadership roles.",
    component: ExecutiveTemplate,
    defaultConfig: { accentColor: "#6b2b3a", fontFamily: "georgia", spacing: "cozy" },
  },
  ats_safe: {
    slug: "ats_safe",
    name: "ATS Safe",
    description: "The most conservative layout, built purely for maximum parser compatibility.",
    component: AtsSafeTemplate,
    // Deliberately not #1a1a1a -- that's Classic's (and Compact's) default,
    // and both are already single-column/minimal, so an identical accent
    // made them read as near-twins in the picker. Steel blue keeps things
    // professional while making the two immediately distinguishable.
    defaultConfig: { accentColor: "#3b6690", fontFamily: "arial", spacing: "cozy" },
  },
};

export const TEMPLATE_SLUGS = Object.keys(TEMPLATE_REGISTRY) as TemplateSlug[];

export function isTemplateSlug(value: string): value is TemplateSlug {
  return value in TEMPLATE_REGISTRY;
}

export function getTemplateDefinition(slug: string): TemplateDefinition {
  return isTemplateSlug(slug) ? TEMPLATE_REGISTRY[slug] : TEMPLATE_REGISTRY.classic;
}
