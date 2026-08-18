import { ContactLine } from "@/features/resumes/templates/shared/ContactLine";
import { EntryList } from "@/features/resumes/templates/shared/EntryList";
import { Section } from "@/features/resumes/templates/shared/Section";
import { SkillsList } from "@/features/resumes/templates/shared/SkillsList";
import { EmptyPreviewNotice, TemplateShell } from "@/features/resumes/templates/shared/TemplateShell";
import type { TemplateProps } from "@/features/resumes/templates/types";

/**
 * Deliberately the plainest of the six templates -- single column, no
 * pills/backgrounds/icons, matching the backend's ats_safe Jinja2 template
 * exactly (see backend/templates/resumes/ats_safe/resume.html.jinja2).
 */
export function AtsSafeTemplate({ data, config }: TemplateProps) {
  return (
    <TemplateShell config={config}>
      <header className="flex flex-col gap-1 border-b pb-4" style={{ borderColor: config.accentColor }}>
        <h1 className="text-xl font-bold text-neutral-900">{data.fullName || "Your name"}</h1>
        {data.headline && <p className="text-neutral-900">{data.headline}</p>}
        <ContactLine items={data.contactLine} />
      </header>

      {data.summary && (
        <Section variant="ats_safe" accentColor={config.accentColor} title={data.summary.title}>
          <p className="text-[13px] leading-relaxed text-neutral-900">{data.summary.text}</p>
        </Section>
      )}

      {data.sections.map((section) => (
        <Section
          key={section.type}
          variant="ats_safe"
          accentColor={config.accentColor}
          title={section.title}
        >
          {section.type === "skills" ? (
            <SkillsList items={section.items} variant="ats_safe" accentColor={config.accentColor} />
          ) : (
            <EntryList items={section.items} variant="ats_safe" />
          )}
        </Section>
      ))}

      <EmptyPreviewNotice data={data} />
    </TemplateShell>
  );
}
