"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[10px] font-semibold tracking-[0.14em] text-primary uppercase">
      {children}
    </p>
  );
}

/**
 * The same profile, re-tailored per role — this is the whole product thesis,
 * so the hero mockup demonstrates it directly: every line of the CV (summary,
 * both experience entries, skills) swaps together as the role rotates, while
 * the name/contact/education stay fixed — exactly what "one profile, many
 * tailored documents" means in practice.
 */
const ROLES = [
  {
    title: "Senior Product Designer",
    role: "Senior Product Designer · Nimbus Labs",
    dates: "2021 — Present",
    detail: "Led design for the core platform, improving activation by 32%.",
    prevRole: "Product Designer · Fieldnote Studio",
    prevDates: "2018 — 2021",
    prevDetail: "Owned the design system used across five product teams.",
    summary: "Product designer with 6+ years building design systems for high-growth SaaS companies.",
    skills: ["Figma", "Design Systems", "Prototyping", "User Research", "UI/UX"],
  },
  {
    title: "Backend Engineer",
    role: "Backend Engineer · Northwind Systems",
    dates: "2022 — Present",
    detail: "Rebuilt the payments service, cutting p95 latency by 40%.",
    prevRole: "Software Engineer · Cascade Data",
    prevDates: "2019 — 2022",
    prevDetail: "Migrated a monolith to microservices serving 2M+ daily requests.",
    summary: "Backend engineer with 5+ years building scalable APIs and distributed systems.",
    skills: ["Python", "PostgreSQL", "Docker", "REST APIs", "AWS"],
  },
  {
    title: "Marketing Lead",
    role: "Marketing Lead · Brightpath Co",
    dates: "2021 — Present",
    detail: "Grew organic traffic 3x through an overhauled content strategy.",
    prevRole: "Marketing Manager · Lumen Retail",
    prevDates: "2017 — 2021",
    prevDetail: "Launched campaigns that lifted quarterly revenue by 18%.",
    summary: "Marketing lead with 7+ years driving growth for consumer and SaaS brands.",
    skills: ["SEO", "Content Strategy", "Analytics", "Campaigns", "Branding"],
  },
  {
    title: "Data Scientist",
    role: "Data Scientist · Vertex Analytics",
    dates: "2020 — Present",
    detail: "Built churn-prediction models that cut attrition by 21%.",
    prevRole: "Data Analyst · Harbor Insights",
    prevDates: "2017 — 2020",
    prevDetail: "Automated reporting pipelines, saving 15 hours a week.",
    summary: "Data scientist with 6+ years turning raw data into product decisions.",
    skills: ["Python", "Machine Learning", "SQL", "Statistics", "Visualization"],
  },
  {
    title: "UX Researcher",
    role: "UX Researcher · Fieldnote Studio",
    dates: "2021 — Present",
    detail: "Ran 40+ studies that shaped three major product launches.",
    prevRole: "Research Associate · Northshore Labs",
    prevDates: "2018 — 2021",
    prevDetail: "Built the team's first repeatable usability-testing framework.",
    summary: "UX researcher with 6+ years translating user insight into product strategy.",
    skills: ["User Interviews", "Usability Testing", "Surveys", "Personas", "Figma"],
  },
] as const;

const ROLE_TITLES = ROLES.map((r) => r.title);

const TYPING_MS = 55;
const DELETING_MS = 30;
const PAUSE_MS = 1600;

/**
 * A single state machine drives both the typewriter (typing/pausing/
 * deleting the role title character by character) and the rest of the
 * card's rotation: the rest of the content fades out while the title is
 * being deleted and swaps in the moment a new word starts typing, so the
 * whole card reads as one synchronized transition, not two independent
 * animations racing each other.
 */
function useTypewriterCycle(words: readonly string[]) {
  const [index, setIndex] = useState(0);
  const [text, setText] = useState("");
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const word = words[index] ?? "";

    if (!deleting && text === word) {
      const timer = setTimeout(() => setDeleting(true), PAUSE_MS);
      return () => clearTimeout(timer);
    }
    if (deleting && text === "") {
      const timer = setTimeout(() => {
        setDeleting(false);
        setIndex((i) => (i + 1) % words.length);
      }, 0);
      return () => clearTimeout(timer);
    }
    const timer = setTimeout(
      () => {
        setText((prev) => (deleting ? word.slice(0, prev.length - 1) : word.slice(0, prev.length + 1)));
      },
      deleting ? DELETING_MS : TYPING_MS,
    );
    return () => clearTimeout(timer);
  }, [text, deleting, index, words]);

  return { text, index, deleting };
}

export function ResumeMockup() {
  const { text: typedTitle, index, deleting } = useTypewriterCycle(ROLE_TITLES);

  const current = ROLES[index];
  const fade = cn("transition-opacity duration-300", deleting ? "opacity-0" : "opacity-100");

  return (
    <div className="relative">
      <div
        className="absolute -inset-6 -z-10 rounded-[2rem] bg-[radial-gradient(50%_50%_at_50%_50%,var(--color-primary)_0%,transparent_70%)] opacity-[0.12]"
        aria-hidden="true"
      />
      <div className="animate-in fade-in slide-in-from-bottom-4 rounded-2xl bg-card p-6 shadow-2xl shadow-black/10 ring-1 ring-foreground/10 duration-700 sm:p-8">
        <div className="flex items-start justify-between gap-4 border-b border-border pb-4">
          <div className="flex flex-col gap-1.5">
            <p className="text-[15px] font-semibold text-foreground">Alex Morgan</p>
            <p className="text-[11px] font-medium whitespace-nowrap text-muted-foreground">
              {typedTitle}
              <span className="ml-0.5 animate-pulse text-primary">|</span>
            </p>
            <p className="mt-1 text-[9px] text-muted-foreground/70">
              alex@email.com · San Francisco, CA
            </p>
          </div>
          <div className="size-10 shrink-0 rounded-full bg-accent" />
        </div>

        <div className="flex flex-col gap-5 pt-5">
          <div className="flex flex-col gap-2">
            <SectionHeading>Summary</SectionHeading>
            <p className={cn("text-[10px] leading-snug text-muted-foreground", fade)}>
              {current.summary}
            </p>
          </div>

          <div className="flex flex-col gap-2.5">
            <SectionHeading>Experience</SectionHeading>
            <div className={cn("flex flex-col gap-1", fade)}>
              <div className="flex items-baseline justify-between gap-3">
                <p className="truncate text-[11px] font-semibold text-foreground/80">
                  {current.role}
                </p>
                <span className="shrink-0 text-[9px] text-muted-foreground/70">{current.dates}</span>
              </div>
              <p className="text-[9.5px] text-muted-foreground">{current.detail}</p>
            </div>
            <div className={cn("flex flex-col gap-1", fade)}>
              <div className="flex items-baseline justify-between gap-3">
                <p className="truncate text-[11px] font-semibold text-foreground/70">
                  {current.prevRole}
                </p>
                <span className="shrink-0 text-[9px] text-muted-foreground/70">{current.prevDates}</span>
              </div>
              <p className="text-[9.5px] text-muted-foreground">{current.prevDetail}</p>
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <SectionHeading>Skills</SectionHeading>
            <div className={cn("flex flex-wrap gap-1.5", fade)}>
              {current.skills.map((skill) => (
                <span
                  key={skill}
                  className="rounded-md border border-border bg-muted/60 px-2 py-1 text-[9px] font-medium text-muted-foreground"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="absolute -right-4 -bottom-4 flex items-center gap-2 rounded-xl bg-card px-3.5 py-2.5 shadow-lg ring-1 ring-foreground/10 sm:-right-6 sm:-bottom-6">
        <span className="flex size-6 items-center justify-center rounded-full bg-success/15 text-success">
          <svg viewBox="0 0 20 20" fill="none" className="size-3.5">
            <path
              d="M4 10.5 8 14.5 16 6"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
        <div className="flex flex-col">
          <span className="text-xs font-medium text-foreground">ATS-ready</span>
          <span className="text-[10px] text-muted-foreground">Export as PDF</span>
        </div>
      </div>
    </div>
  );
}
