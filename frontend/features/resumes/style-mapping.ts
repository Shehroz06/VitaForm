import type { TemplateConfig } from "@/features/resumes/templates/types";
import type { ResumeStyle } from "@/features/resumes/types";

/** camelCase (client-side template config) <-> snake_case (persisted
 * ResumeStyle) -- the one place this mapping happens, shared by the
 * builder's own style editing and the template picker's per-template
 * preview requests. */
export function styleToConfig(style: ResumeStyle): TemplateConfig {
  return {
    accentColor: style.accent_color,
    fontFamily: style.font_family,
    spacing: style.spacing,
    contentDensity: style.content_density,
  };
}

export function configToStyle(config: TemplateConfig): ResumeStyle {
  return {
    accent_color: config.accentColor,
    font_family: config.fontFamily,
    spacing: config.spacing,
    content_density: config.contentDensity ?? 1,
  };
}
