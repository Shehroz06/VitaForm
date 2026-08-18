import { Database, RefreshCw, ShieldCheck } from "lucide-react";

const PRINCIPLES = [
  {
    icon: Database,
    title: "Structured, not typed",
    description: "Your career lives in real fields — not a wall of text you retype every time.",
  },
  {
    icon: RefreshCw,
    title: "Reproducible",
    description: "Regenerate any document at any time from the same source, always up to date.",
  },
  {
    icon: ShieldCheck,
    title: "Nothing invented",
    description: "The AI only selects and arranges what you actually entered. Never fabricated.",
  },
] as const;

export function AboutSection() {
  return (
    <section id="about" className="border-t border-border bg-accent/50 py-16 sm:py-20">
      <div className="mx-auto grid max-w-[1240px] gap-10 px-4 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-center lg:gap-16">
        <div>
          <h2 className="text-balance font-heading text-3xl font-semibold tracking-tight text-foreground">
            The profile is permanent. The documents are temporary.
          </h2>
          <p className="mt-4 text-muted-foreground">
            Most resume builders make you retype your career every time you apply somewhere new.
            VitaForm inverts that: your structured profile is the single source of truth, and
            every document is generated from it on demand.
          </p>
        </div>

        <div className="flex flex-col gap-5">
          {PRINCIPLES.map(({ icon: Icon, title, description }) => (
            <div key={title} className="flex items-start gap-4">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-card text-primary ring-1 ring-foreground/10">
                <Icon className="size-5" />
              </span>
              <div>
                <h3 className="font-heading text-base font-medium text-foreground">{title}</h3>
                <p className="text-sm text-muted-foreground">{description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
