import { ContactLine } from "@/features/resumes/templates/shared/ContactLine";
import { EntryList } from "@/features/resumes/templates/shared/EntryList";
import { Section } from "@/features/resumes/templates/shared/Section";
import { SkillsList } from "@/features/resumes/templates/shared/SkillsList";
import { EmptyPreviewNotice, TemplateShell } from "@/features/resumes/templates/shared/TemplateShell";
import type { TemplateProps } from "@/features/resumes/templates/types";

export function ModernTemplate({ data, config }: TemplateProps) {
  return (
    <TemplateShell config={config}>
      <header
        className="flex flex-col gap-1 border-b-[3px] pb-4"
        style={{ borderColor: config.accentColor }}
      >
        <h1 className="text-[26px] font-extrabold tracking-tight text-neutral-900">
          {data.fullName || "Your name"}
        </h1>
        {data.headline && (
          <p className="text-[15px] font-semibold" style={{ color: config.accentColor }}>
            {data.headline}
          </p>
        )}
        <ContactLine items={data.contactLine} />
      </header>

      {data.summary && (
        <Section variant="modern" accentColor={config.accentColor} title={data.summary.title}>
          <p className="text-[13px] leading-relaxed text-neutral-800">{data.summary.text}</p>
        </Section>
      )}

      {data.sections.map((section) => (
        <Section
          key={section.type}
          variant="modern"
          accentColor={config.accentColor}
          title={section.title}
        >
          {section.type === "skills" ? (
            <SkillsList items={section.items} variant="modern" accentColor={config.accentColor} />
          ) : (
            <EntryList items={section.items} variant="modern" />
          )}
        </Section>
      ))}

      <EmptyPreviewNotice data={data} />
    </TemplateShell>
  );
}
