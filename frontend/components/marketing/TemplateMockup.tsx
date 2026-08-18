import { cn } from "@/lib/utils";

export type TemplateSlug = "classic" | "modern" | "minimal" | "compact" | "executive" | "ats_safe";

const SAMPLE = {
  name: "Alex Morgan",
  headline: "Senior Product Designer",
  contact: "alex@email.com  ·  San Francisco, CA  ·  alexmorgan.design",
  summary:
    "Product designer with 6+ years building design systems for high-growth SaaS companies.",
  experience: [
    {
      title: "Senior Product Designer · Nimbus Labs",
      dates: "2021 — Present",
      detail: "Led design for the core platform, improving activation by 32%.",
    },
    {
      title: "Product Designer · Fieldnote Studio",
      dates: "2018 — 2021",
      detail: "Owned the design system used across five product teams.",
    },
    {
      title: "UX Designer · Harborline",
      dates: "2016 — 2018",
      detail: "Redesigned the onboarding flow, cutting drop-off by 24%.",
    },
  ],
  education: [{ title: "B.S. Cognitive Science, Stanford University", dates: "2014 — 2018" }],
  skills: [
    "Figma",
    "Design Systems",
    "Prototyping",
    "User Research",
    "TypeScript",
    "Accessibility",
  ],
};

function SectionTitle({
  slug,
  accent,
  children,
}: {
  slug: string;
  accent: string;
  children: React.ReactNode;
}) {
  const base = "text-[8px] font-semibold tracking-[0.14em] uppercase";
  if (slug === "minimal") {
    return (
      <p className={cn(base, "border-b border-dashed border-neutral-300 pb-1 font-normal text-neutral-400")}>
        {children}
      </p>
    );
  }
  if (slug === "modern") {
    return (
      <p className={cn(base, "border-l-2 pl-1.5")} style={{ color: accent, borderColor: accent }}>
        {children}
      </p>
    );
  }
  if (slug === "executive") {
    return (
      <p className={cn(base, "text-center")} style={{ color: accent }}>
        {children}
      </p>
    );
  }
  if (slug === "ats_safe") {
    // Deliberately the plainest: black text, no color on the label itself --
    // only a thin accent underline, matching the real template's minimal-
    // decoration philosophy (every visual choice exists to survive a parser).
    return (
      <p className={cn(base, "border-b pb-1 text-neutral-900")} style={{ borderColor: accent }}>
        {children}
      </p>
    );
  }
  return (
    <p className={base} style={{ color: accent }}>
      {children}
    </p>
  );
}

function SkillChips({ slug, accent }: { slug: string; accent: string }) {
  const justify = slug === "executive" ? "justify-center" : "";

  if (slug === "minimal") {
    return (
      <p className={cn("text-[8px] text-neutral-500", justify)}>{SAMPLE.skills.join("   ")}</p>
    );
  }
  if (slug === "modern") {
    return (
      <div className={cn("flex flex-wrap gap-1", justify)}>
        {SAMPLE.skills.map((skill) => (
          <span
            key={skill}
            className="rounded-full px-1.5 py-0.5 text-[7px] font-medium"
            style={{ backgroundColor: `${accent}29`, color: accent }}
          >
            {skill}
          </span>
        ))}
      </div>
    );
  }
  if (slug === "executive") {
    return (
      <div className={cn("flex flex-wrap gap-1.5", justify)}>
        {SAMPLE.skills.map((skill) => (
          <span
            key={skill}
            className="rounded-[1px] border px-1.5 py-0.5 text-[7px]"
            style={{ borderColor: accent, color: accent }}
          >
            {skill}
          </span>
        ))}
      </div>
    );
  }
  if (slug === "ats_safe") {
    // Plain comma-separated text, no pills/borders/backgrounds -- matches
    // the real backend template's most-conservative rendering exactly.
    return (
      <p className={cn("text-[8px] text-neutral-900", justify)}>{SAMPLE.skills.join(", ")}</p>
    );
  }
  return (
    <div className={cn("flex flex-wrap gap-1", justify)}>
      {SAMPLE.skills.map((skill) => (
        <span
          key={skill}
          className="rounded border border-neutral-300 px-1.5 py-0.5 text-[7px] text-neutral-700"
        >
          {skill}
        </span>
      ))}
    </div>
  );
}

/**
 * A resume preview is a document mockup, not app chrome — it's always shown
 * as white paper with dark ink, matching the real exported PDF, regardless
 * of whether the app itself is in light or dark mode.
 */
export function TemplateMockup({ slug, accent }: { slug: string; accent: string }) {
  const centered = slug === "executive";
  const serif = slug === "executive";
  const dense = slug === "compact";

  return (
    <div
      // A4 portrait ratio (210 × 297mm) — this is the real page size every
      // exported PDF renders at, so the preview should look like one.
      className={cn(
        "flex aspect-[210/297] w-full flex-col overflow-hidden rounded-xl bg-white p-5 text-neutral-900 shadow-sm ring-1 ring-black/10",
        dense ? "gap-2" : "gap-3",
      )}
    >
      <div
        className={cn(
          "flex pb-2",
          centered ? "flex-col items-center border-b-2 text-center" : "items-baseline justify-between border-b border-neutral-300",
          slug === "modern" ? "border-b-[3px]" : "",
        )}
        style={{
          borderColor: centered || slug === "modern" || slug === "ats_safe" ? accent : undefined,
        }}
      >
        <div className={cn("flex flex-col gap-0.5", centered && "items-center")}>
          <p className={cn("text-[13px] font-bold text-neutral-900", serif && "font-serif tracking-wide uppercase")}>
            {SAMPLE.name}
          </p>
          <p className="text-[9px] text-neutral-600 italic">{SAMPLE.headline}</p>
        </div>
      </div>
      <p className={cn("-mt-2 text-[7px] text-neutral-400", centered && "text-center")}>
        {SAMPLE.contact}
      </p>

      <div className={cn("flex flex-col", dense ? "gap-1" : "gap-1.5")}>
        <SectionTitle slug={slug} accent={accent}>
          Summary
        </SectionTitle>
        <p className={cn("text-[8.5px] leading-snug text-neutral-700", centered && "text-center")}>
          {SAMPLE.summary}
        </p>
      </div>

      <div className={cn("flex flex-col", dense ? "gap-1" : "gap-1.5")}>
        <SectionTitle slug={slug} accent={accent}>
          Experience
        </SectionTitle>
        {SAMPLE.experience.map((entry) => (
          <div key={entry.title}>
            <div className={cn("flex items-baseline justify-between gap-2", centered && "justify-center gap-3")}>
              <span className="text-[8.5px] font-semibold text-neutral-900">{entry.title}</span>
              <span className="shrink-0 text-[7.5px] text-neutral-400">{entry.dates}</span>
            </div>
            {!dense && (
              <p className={cn("text-[8px] text-neutral-600", centered && "text-center")}>
                {entry.detail}
              </p>
            )}
          </div>
        ))}
      </div>

      <div className={cn("flex flex-col", dense ? "gap-1" : "gap-1.5")}>
        <SectionTitle slug={slug} accent={accent}>
          Education
        </SectionTitle>
        {SAMPLE.education.map((entry) => (
          <div
            key={entry.title}
            className={cn("flex items-baseline justify-between gap-2", centered && "justify-center gap-3")}
          >
            <span className="text-[8.5px] font-semibold text-neutral-900">{entry.title}</span>
            <span className="shrink-0 text-[7.5px] text-neutral-400">{entry.dates}</span>
          </div>
        ))}
      </div>

      <div className={cn("flex flex-col", dense ? "gap-1" : "gap-1.5")}>
        <SectionTitle slug={slug} accent={accent}>
          Skills
        </SectionTitle>
        <SkillChips slug={slug} accent={accent} />
      </div>
    </div>
  );
}
