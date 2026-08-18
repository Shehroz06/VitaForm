import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export function FinalCta() {
  return (
    <section className="border-t border-border py-16 sm:py-24">
      <div className="mx-auto max-w-2xl px-4 text-center sm:px-6">
        <h2 className="text-balance font-heading text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Ready to build your next opportunity?
        </h2>
        <p className="mt-3 text-muted-foreground">
          Set up your profile once. Generate a tailored resume for every role you apply to.
        </p>
        <Button asChild size="lg" className="mt-7 gap-1.5 px-7">
          <Link href="/register">
            Create Your Resume
            <ArrowRight className="size-4" />
          </Link>
        </Button>
      </div>
    </section>
  );
}
