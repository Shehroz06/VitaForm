import type {
  ResumeTemplateData,
  TemplateConfig,
  TemplateFontFamily,
  TemplateSpacing,
} from "@/features/resumes/templates/types";
import type { SectionType } from "@/features/resumes/types";

/**
 * Foundation for a future user-created template builder. Nothing in the
 * app constructs or reads this schema yet -- no PDF upload, no computer
 * vision, no AI generation. It exists so that pipeline, when it's built,
 * has a target shape to produce rather than inventing one under pressure:
 *
 *   Built-in template ──► TemplateDefinition (registry.tsx)
 *   AI-generated / user-built template ──► TemplateSchema (this file)
 *                                              │
 *                                     schemaToTemplateDefinition()
 *                                              │
 *                                              ▼
 *                                     same TemplateRenderer, same
 *                                     ResumeTemplateData contract
 *
 * A schema is data (JSON-serializable), not code -- unlike the 5 built-in
 * templates, it never needs a new React component to exist. The renderer
 * this schema eventually feeds is `shared/SchemaTemplate.tsx`, not yet
 * built: it would read `layout`/`sections`/`style` and compose the exact
 * same Section/EntryList/SkillsList/ContactLine primitives every built-in
 * template already uses, so a schema-driven template is never a second,
 * parallel rendering system.
 */

export type TemplatePageSize = "a4" | "letter";
export type TemplateLayoutMode = "single-column" | "two-column";

export interface TemplateSchemaColumns {
  left: Exclude<SectionType, "summary">[];
  right: Exclude<SectionType, "summary">[];
}

export interface TemplateSchemaStyle {
  fontFamily: TemplateFontFamily;
  primaryColor: string;
  accentColor: string;
  spacing: TemplateSpacing;
  headerStyle: "left" | "centered";
}

/**
 * A template as portable, storable configuration. `sectionOrder` and
 * `sectionVisibility` describe intent the same way ResumeContent's
 * `sections[]` already does on the backend, so mapping a schema onto an
 * actual resume's data never requires a new data-shape translation layer.
 */
export interface TemplateSchema {
  id: string;
  name: string;
  pageSize: TemplatePageSize;
  layout: TemplateLayoutMode;
  columns?: TemplateSchemaColumns;
  sectionOrder: SectionType[];
  sectionVisibility: Partial<Record<SectionType, boolean>>;
  style: TemplateSchemaStyle;
}

/** A single-column schema matching one of today's built-in templates --
 * demonstrates that every existing template is already expressible in this
 * shape, so adopting it later isn't a breaking redesign. */
export const EXAMPLE_SINGLE_COLUMN_SCHEMA: TemplateSchema = {
  id: "schema-example-single-column",
  name: "Example single-column",
  pageSize: "a4",
  layout: "single-column",
  sectionOrder: ["summary", "experience", "education", "projects", "skills"],
  sectionVisibility: {},
  style: {
    fontFamily: "arial",
    primaryColor: "#1a1a1a",
    accentColor: "#2c4a6e",
    spacing: "cozy",
    headerStyle: "left",
  },
};

/** A two-column schema -- not renderable by any built-in template today,
 * included to prove the schema shape isn't just a re-description of what
 * already exists. */
export const EXAMPLE_TWO_COLUMN_SCHEMA: TemplateSchema = {
  id: "schema-example-two-column",
  name: "Example two-column",
  pageSize: "a4",
  layout: "two-column",
  columns: {
    left: ["skills", "languages", "certifications"],
    right: ["experience", "education", "projects"],
  },
  sectionOrder: ["summary", "experience", "education", "projects", "skills", "languages", "certifications"],
  sectionVisibility: {},
  style: {
    fontFamily: "arial",
    primaryColor: "#1a1a1a",
    accentColor: "#35507e",
    spacing: "cozy",
    headerStyle: "left",
  },
};

/**
 * Maps a schema's style onto the same TemplateConfig every built-in
 * template already renders with. Deliberately the only "schema ->
 * something the renderer understands" function that exists today --
 * schemas aren't otherwise wired into TemplateRenderer/registry yet.
 */
export function schemaStyleToTemplateConfig(style: TemplateSchemaStyle): TemplateConfig {
  return {
    accentColor: style.accentColor,
    fontFamily: style.fontFamily,
    spacing: style.spacing,
  };
}

/** Reduces a schema's section configuration onto an existing set of mapped
 * resume sections, in case a future schema-driven renderer needs to filter/
 * reorder `ResumeTemplateData.sections` before passing it to a template. */
export function applySchemaSectionOrder(
  data: ResumeTemplateData,
  schema: TemplateSchema,
): ResumeTemplateData {
  const order = schema.sectionOrder.filter(
    (type): type is Exclude<SectionType, "summary"> => type !== "summary",
  );
  const bySectionType = new Map(data.sections.map((section) => [section.type, section]));
  const visible = schema.sectionVisibility;

  const sections = order
    .filter((type) => visible[type] !== false)
    .map((type) => bySectionType.get(type))
    .filter((section): section is NonNullable<typeof section> => Boolean(section));

  return { ...data, sections };
}
