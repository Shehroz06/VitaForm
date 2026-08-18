import { FileDown, LayoutTemplate, UserRoundPen } from "lucide-react";

const STEPS = [
  {
    icon: UserRoundPen,
    title: "Add your information",
    description:
      "Fill out your profile once — education, experience, projects, skills, and more.",
  },
  {
    icon: LayoutTemplate,
    title: "Choose a template",
    description: "Start from an ATS-friendly resume layout built for clarity, not decoration.",
  },
  {
    icon: FileDown,
    title: "Download your resume",
    description: "Generate a tailored resume for any job and export it as a polished PDF.",
  },
] as const;

export function HowItWorks() {
  return (
    <section id="how-it-works" className="border-t border-border bg-accent/50 py-16 sm:py-20">
      <div className="mx-auto max-w-[1240px] px-4 sm:px-6">
        <div className="mx-auto max-w-xl text-center">
          <h2 className="font-heading text-3xl font-semibold tracking-tight text-foreground">
            How it works
          </h2>
        </div>

        <div className="relative mx-auto mt-12 grid max-w-4xl gap-8 sm:grid-cols-3">
          <div
            className="absolute top-6 right-[16.5%] left-[16.5%] hidden h-px bg-border sm:block"
            aria-hidden="true"
          />
          {STEPS.map(({ icon: Icon, title, description }, i) => (
            <div key={title} className="relative flex flex-col items-center gap-3 text-center">
              <div className="relative flex size-12 items-center justify-center rounded-full bg-card text-primary ring-1 ring-foreground/10">
                <Icon className="size-5" />
                <span className="absolute -top-2 -right-2 flex size-5 items-center justify-center rounded-full bg-primary text-[10px] font-semibold text-primary-foreground">
                  {i + 1}
                </span>
              </div>
              <h3 className="font-heading text-base font-medium text-foreground">{title}</h3>
              <p className="max-w-[220px] text-sm text-muted-foreground">{description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
