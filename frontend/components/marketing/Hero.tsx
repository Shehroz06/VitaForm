import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ResumeMockup } from "@/components/marketing/ResumeMockup";

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div
        className="pointer-events-none absolute inset-x-0 -top-40 h-[560px] bg-[radial-gradient(60%_60%_at_50%_0%,var(--color-primary)_0%,transparent_70%)] opacity-[0.08]"
        aria-hidden="true"
      />
      <div className="mx-auto grid max-w-[1240px] gap-12 px-4 py-16 sm:px-6 sm:py-24 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:py-28">
        <div className="flex flex-col items-start gap-6">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
            <Sparkles className="size-3.5 text-primary" />
            One profile. Every document, tailored.
          </span>

          <h1 className="text-balance font-heading text-4xl font-semibold tracking-tight text-foreground sm:text-5xl lg:text-[3.4rem] lg:leading-[1.08]">
            Build a resume that gets noticed.
          </h1>

          <p className="max-w-lg text-balance text-lg text-muted-foreground">
            Store your career history once. VitaForm&apos;s AI selects and arranges your real
            experience, projects, and skills into a resume tailored to the job — never inventing,
            only ever using what you actually entered.
          </p>

          <div className="flex flex-col gap-3 sm:flex-row">
            <Button asChild size="lg" className="gap-1.5 px-6">
              <Link href="/register">
                Create Your Resume
                <ArrowRight className="size-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="px-6">
              <Link href="#templates">Explore Templates</Link>
            </Button>
          </div>
        </div>

        <div className="relative mx-auto w-full max-w-md lg:max-w-none">
          <ResumeMockup />
        </div>
      </div>
    </section>
  );
}
