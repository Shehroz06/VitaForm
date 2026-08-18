import { ContactLine } from "@/features/resumes/templates/shared/ContactLine";
import { EntryList } from "@/features/resumes/templates/shared/EntryList";
import { Section } from "@/features/resumes/templates/shared/Section";
import { SkillsList } from "@/features/resumes/templates/shared/SkillsList";
import { EmptyPreviewNotice, TemplateShell } from "@/features/resumes/templates/shared/TemplateShell";
import type { TemplateProps } from "@/features/resumes/templates/types";

export function ClassicTemplate({ data, config }: TemplateProps) {
  return (
    <TemplateShell config={config}>
      <header className="flex flex-col gap-1 border-b border-neutral-300 pb-4">
        <h1 className="text-2xl font-bold text-neutral-900">{data.fullName || "Your name"}</h1>
        {data.headline && <p className="text-neutral-700">{data.headline}</p>}
        <ContactLine items={data.contactLine} />
      </header>

      {data.summary && (
        <Section variant="classic" accentColor={config.accentColor} title={data.summary.title}>
          <p className="text-[13px] leading-relaxed text-neutral-800">{data.summary.text}</p>
        </Section>
      )}

      {data.sections.map((section) => (
        <Section
          key={section.type}
          variant="classic"
          accentColor={config.accentColor}
          title={section.title}
        >
          {section.type === "skills" ? (
            <SkillsList items={section.items} variant="classic" accentColor={config.accentColor} />
          ) : (
            <EntryList items={section.items} variant="classic" />
          )}
        </Section>
      ))}

      <EmptyPreviewNotice data={data} />
    </TemplateShell>
  );
}
