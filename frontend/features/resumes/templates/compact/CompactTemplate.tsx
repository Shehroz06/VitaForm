import { ContactLine } from "@/features/resumes/templates/shared/ContactLine";
import { EntryList } from "@/features/resumes/templates/shared/EntryList";
import { Section } from "@/features/resumes/templates/shared/Section";
import { SkillsList } from "@/features/resumes/templates/shared/SkillsList";
import { EmptyPreviewNotice, TemplateShell } from "@/features/resumes/templates/shared/TemplateShell";
import type { TemplateProps } from "@/features/resumes/templates/types";

export function CompactTemplate({ data, config }: TemplateProps) {
  return (
    <TemplateShell config={config} className="gap-3 p-6">
      <header className="flex flex-col gap-0.5 border-b border-neutral-900 pb-2.5">
        <h1 className="text-lg font-bold text-neutral-900">{data.fullName || "Your name"}</h1>
        {data.headline && <p className="text-[12px] text-neutral-600">{data.headline}</p>}
        <ContactLine items={data.contactLine} />
      </header>

      {data.summary && (
        <Section variant="compact" accentColor={config.accentColor} title={data.summary.title}>
          <p className="text-[12px] leading-snug text-neutral-800">{data.summary.text}</p>
        </Section>
      )}

      {data.sections.map((section) => (
        <Section
          key={section.type}
          variant="compact"
          accentColor={config.accentColor}
          title={section.title}
        >
          {section.type === "skills" ? (
            <SkillsList items={section.items} variant="compact" accentColor={config.accentColor} />
          ) : (
            <EntryList items={section.items} variant="compact" />
          )}
        </Section>
      ))}

      <EmptyPreviewNotice data={data} />
    </TemplateShell>
  );
}
