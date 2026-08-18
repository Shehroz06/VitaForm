import { ContactLine } from "@/features/resumes/templates/shared/ContactLine";
import { EntryList } from "@/features/resumes/templates/shared/EntryList";
import { Section } from "@/features/resumes/templates/shared/Section";
import { SkillsList } from "@/features/resumes/templates/shared/SkillsList";
import { EmptyPreviewNotice, TemplateShell } from "@/features/resumes/templates/shared/TemplateShell";
import type { TemplateProps } from "@/features/resumes/templates/types";

export function ExecutiveTemplate({ data, config }: TemplateProps) {
  return (
    <TemplateShell config={config}>
      <header
        className="flex flex-col items-center gap-1 border-b-2 border-double pb-4 text-center"
        style={{ borderColor: config.accentColor }}
      >
        <h1 className="text-2xl font-bold tracking-[0.08em] text-neutral-900 uppercase">
          {data.fullName || "Your name"}
        </h1>
        {data.headline && (
          <p className="text-[13px] italic" style={{ color: config.accentColor }}>
            {data.headline}
          </p>
        )}
        <ContactLine items={data.contactLine} centered />
      </header>

      {data.summary && (
        <Section
          variant="executive"
          accentColor={config.accentColor}
          title={data.summary.title}
          centered
        >
          <p className="text-[13px] leading-relaxed text-justify text-neutral-800">
            {data.summary.text}
          </p>
        </Section>
      )}

      {data.sections.map((section) => (
        <Section
          key={section.type}
          variant="executive"
          accentColor={config.accentColor}
          title={section.title}
          centered
        >
          {section.type === "skills" ? (
            <SkillsList
              items={section.items}
              variant="executive"
              accentColor={config.accentColor}
              centered
            />
          ) : (
            <EntryList items={section.items} variant="executive" centered />
          )}
        </Section>
      ))}

      <EmptyPreviewNotice data={data} />
    </TemplateShell>
  );
}
