import { getTemplateDefinition } from "@/features/resumes/templates/registry";
import type { ResumeTemplateData, TemplateConfig } from "@/features/resumes/templates/types";

/**
 * Resume Data -> Template Renderer -> Live CV. The one place resume content
 * and template choice meet: swapping `slug` re-renders the same `data`
 * through a different component, never touching or losing the data itself.
 */
export function TemplateRenderer({
  slug,
  data,
  config,
}: {
  slug: string;
  data: ResumeTemplateData;
  config: TemplateConfig;
}) {
  const definition = getTemplateDefinition(slug);
  const Component = definition.component;
  return <Component data={data} config={config} />;
}
