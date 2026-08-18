import Link from "next/link";
import { ArrowRight, Check } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface Step {
  label: string;
  description: string;
  href: string;
  cta: string;
  done: boolean;
}

export function OnboardingChecklist({
  profileComplete,
  hasResumes,
}: {
  profileComplete: boolean;
  hasResumes: boolean;
}) {
  const steps: Step[] = [
    {
      label: "Complete your profile",
      description: "Add your education, experience, projects, and skills.",
      href: "/profile",
      cta: "Go to profile",
      done: profileComplete,
    },
    {
      label: "Choose a template",
      description: "Pick a layout that fits the role you're applying for.",
      href: "/templates",
      cta: "Browse templates",
      done: hasResumes,
    },
    {
      label: "Generate your resume",
      description: "Describe the role and let the AI build your resume from your profile.",
      href: "/resumes",
      cta: "Generate a resume",
      done: hasResumes,
    },
  ];

  if (steps.every((step) => step.done)) return null;

  const nextStep = steps.find((step) => !step.done);

  return (
    <Card>
      <CardContent className="flex flex-col gap-4">
        <div>
          <h2 className="font-heading text-base font-medium text-foreground">Getting started</h2>
          <p className="text-sm text-muted-foreground">
            Follow these steps to generate your first tailored resume.
          </p>
        </div>
        <ol className="flex flex-col gap-1">
          {steps.map((step, index) => {
            const isNext = step === nextStep;
            return (
              <li key={step.label}>
                <Link
                  href={step.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-2 py-2 transition-colors hover:bg-muted",
                    isNext && "bg-accent/60"
                  )}
                >
                  <span
                    className={cn(
                      "flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-medium ring-1 ring-inset",
                      step.done
                        ? "bg-success/15 text-success ring-success/30"
                        : "text-muted-foreground ring-border"
                    )}
                  >
                    {step.done ? <Check className="size-3.5" strokeWidth={3} /> : index + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p
                      className={cn(
                        "text-sm font-medium",
                        step.done ? "text-muted-foreground line-through" : "text-foreground"
                      )}
                    >
                      {step.label}
                    </p>
                    {isNext && <p className="text-xs text-muted-foreground">{step.description}</p>}
                  </div>
                  {isNext && (
                    <span className="flex shrink-0 items-center gap-1 text-xs font-medium text-primary">
                      {step.cta}
                      <ArrowRight className="size-3.5" />
                    </span>
                  )}
                </Link>
              </li>
            );
          })}
        </ol>
      </CardContent>
    </Card>
  );
}
