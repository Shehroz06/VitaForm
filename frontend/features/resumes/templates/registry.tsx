import type { TemplateDefinition, TemplateSlug } from "@/features/resumes/templates/types";

/**
 * The one place that knows every template that exists. Slugs, names, and
 * defaultConfig here are the only client-side knowledge of each template --
 * layout and typography live entirely in the backend's 6 Jinja2 templates
 * (see backend/templates/resumes/), since every preview (builder, template
 * picker) is now a real render of those, not a client-side
 * reimplementation. Adding a template means adding the backend template
 * plus an entry here; nothing else needs to change to pick it up.
 */
export const TEMPLATE_REGISTRY: Record<TemplateSlug, TemplateDefinition> = {
  classic: {
    slug: "classic",
    name: "Classic",
    description: "A clean, single-column, ATS-friendly layout.",
    defaultConfig: { accentColor: "#1a1a1a", fontFamily: "arial", spacing: "cozy" },
  },
  modern: {
    slug: "modern",
    name: "Modern",
    description: "Bold headings with a strong accent, built for a contemporary look.",
    defaultConfig: { accentColor: "#2c4a6e", fontFamily: "calibri", spacing: "cozy" },
  },
  minimal: {
    slug: "minimal",
    name: "Minimal",
    description: "Light typography and generous whitespace for an understated resume.",
    defaultConfig: { accentColor: "#4a5563", fontFamily: "arial", spacing: "relaxed" },
  },
  compact: {
    slug: "compact",
    name: "Compact",
    description: "Denser spacing that fits more on the page — for longer histories.",
    defaultConfig: { accentColor: "#1a1a1a", fontFamily: "arial", spacing: "compact" },
  },
  executive: {
    slug: "executive",
    name: "Executive",
    description: "A centered, formal layout for senior and leadership roles.",
    defaultConfig: { accentColor: "#6b2b3a", fontFamily: "georgia", spacing: "cozy" },
  },
  ats_safe: {
    slug: "ats_safe",
    name: "LaTeX",
    description: "The most conservative layout, built purely for maximum parser compatibility.",
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
