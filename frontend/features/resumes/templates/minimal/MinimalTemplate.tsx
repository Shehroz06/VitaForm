import { ContactLine } from "@/features/resumes/templates/shared/ContactLine";
import { EntryList } from "@/features/resumes/templates/shared/EntryList";
import { Section } from "@/features/resumes/templates/shared/Section";
import { SkillsList } from "@/features/resumes/templates/shared/SkillsList";
import { EmptyPreviewNotice, TemplateShell } from "@/features/resumes/templates/shared/TemplateShell";
import type { TemplateProps } from "@/features/resumes/templates/types";

export function MinimalTemplate({ data, config }: TemplateProps) {
  return (
    <TemplateShell config={config} className="font-light">
      <header className="flex flex-col gap-1.5">
        <h1 className="text-xl font-normal tracking-wide text-neutral-900">
          {data.fullName || "Your name"}
        </h1>
        {data.headline && <p className="text-[13px] font-light text-neutral-500">{data.headline}</p>}
        <ContactLine items={data.contactLine} />
      </header>

      {data.summary && (
        <Section variant="minimal" accentColor={config.accentColor} title={data.summary.title}>
          <p className="text-[13px] leading-relaxed font-light text-neutral-800">
            {data.summary.text}
          </p>
        </Section>
      )}

      {data.sections.map((section) => (
        <Section
          key={section.type}
          variant="minimal"
          accentColor={config.accentColor}
          title={section.title}
        >
          {section.type === "skills" ? (
            <SkillsList items={section.items} variant="minimal" accentColor={config.accentColor} />
          ) : (
            <EntryList items={section.items} variant="minimal" />
          )}
        </Section>
      ))}

      <EmptyPreviewNotice data={data} />
    </TemplateShell>
  );
}
