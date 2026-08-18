import { Check } from "lucide-react";

const GROUPS = [
  {
    title: "Your profile",
    items: [
      "16 structured career modules — education, experience, projects, skills, certifications, awards, research, and more",
      "Upload an existing resume as a PDF and review AI-extracted data before anything is saved",
      "Every section has full create, edit, and delete control",
    ],
  },
  {
    title: "AI generation",
    items: [
      "Resume content ranked and selected from your real profile — nothing invented",
      "Provider-agnostic AI layer with automatic fallback if one provider is unavailable",
      "Matching cover letters and LinkedIn About sections from the same profile data",
    ],
  },
  {
    title: "Job intelligence",
    items: [
      "Paste a job description to extract required and preferred keywords automatically",
      "ATS match scoring against your actual skills and experience",
      "Generate a resume pre-tailored to a specific saved job",
    ],
  },
  {
    title: "Export & versioning",
    items: [
      "Every save creates a new version — nothing is silently overwritten",
      "One-click export to a real, downloadable PDF",
      "Full version history for every resume",
    ],
  },
] as const;

export function FeaturesSection() {
  return (
    <section id="features" className="py-16 sm:py-20">
      <div className="mx-auto max-w-[1240px] px-4 sm:px-6">
        <div className="mx-auto max-w-xl text-center">
          <h2 className="font-heading text-3xl font-semibold tracking-tight text-foreground">
            What VitaForm actually does
          </h2>
          <p className="mt-3 text-muted-foreground">
            No filler features. Everything below is live in the product today.
          </p>
        </div>

        <div className="mx-auto mt-12 grid max-w-5xl gap-x-10 gap-y-10 sm:grid-cols-2">
          {GROUPS.map((group) => (
            <div key={group.title} className="flex flex-col gap-3">
              <h3 className="font-heading text-base font-medium text-foreground">
                {group.title}
              </h3>
              <ul className="flex flex-col gap-2.5">
                {group.items.map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-sm text-muted-foreground">
                    <Check className="mt-0.5 size-4 shrink-0 text-primary" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
