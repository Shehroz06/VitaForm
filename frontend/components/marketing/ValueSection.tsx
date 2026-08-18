import { Database, FileCheck2, Sparkles, Target, Wand2, Zap } from "lucide-react";

const VALUES = [
  {
    icon: Database,
    title: "One structured profile",
    description:
      "Education, experience, projects, skills, and more — entered once, reused for every document you generate.",
    swatch: "var(--swatch-navy)",
  },
  {
    icon: Wand2,
    title: "AI that never invents",
    description:
      "The AI only selects and arranges your real achievements. It never fabricates experience, projects, or skills.",
    swatch: "var(--swatch-wood)",
  },
  {
    icon: Target,
    title: "Tailored to the job",
    description:
      "Paste a job description and the resume is ranked and assembled around what that role actually asks for.",
    swatch: "var(--swatch-burgundy)",
  },
  {
    icon: FileCheck2,
    title: "ATS-friendly output",
    description:
      "Clean, single-column layouts built to parse correctly in applicant tracking systems — not just look good.",
    swatch: "var(--swatch-emerald)",
  },
  {
    icon: Zap,
    title: "Export-ready in seconds",
    description:
      "Every resume renders to a real, downloadable PDF — reproducible from your structured data at any time.",
    swatch: "var(--swatch-slate)",
  },
  {
    icon: Sparkles,
    title: "Cover letters & LinkedIn, too",
    description:
      "Generate a matching cover letter and LinkedIn About section from the same profile, no retyping required.",
    swatch: "var(--swatch-purple)",
  },
] as const;

export function ValueSection() {
  return (
    <section className="border-t border-border bg-accent/50 py-16 sm:py-20">
      <div className="mx-auto max-w-[1240px] px-4 sm:px-6">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {VALUES.map(({ icon: Icon, title, description, swatch }) => (
            <div
              key={title}
              className="flex flex-col gap-3 rounded-2xl bg-card p-6 ring-1 ring-foreground/10 transition-transform duration-200 hover:-translate-y-0.5"
            >
              <div
                className="flex size-10 items-center justify-center rounded-xl"
                style={{ backgroundColor: swatch }}
              >
                <Icon className="size-5 text-white" />
              </div>
              <h3 className="font-heading text-base font-medium text-foreground">{title}</h3>
              <p className="text-sm text-muted-foreground">{description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
