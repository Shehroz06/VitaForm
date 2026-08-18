import { cn } from "@/lib/utils";
import type { TemplateSlug } from "@/features/resumes/templates/types";

/**
 * Section-title treatment is one of the biggest visual signatures of a
 * resume template (underline vs. left-border vs. dashed vs. centered), so
 * it's parameterized by variant here rather than hardcoded per template --
 * every template still renders through the same component, just styled
 * differently, matching the real server-rendered PDF's per-template CSS.
 */
function SectionTitle({
  variant,
  accentColor,
  children,
}: {
  variant: TemplateSlug;
  accentColor: string;
  children: React.ReactNode;
}) {
  const base = "text-[11px] font-semibold uppercase";

  if (variant === "minimal") {
    return (
      <p
        className={cn(
          base,
          "border-b border-dashed border-neutral-300 pb-1.5 font-normal tracking-[0.18em] text-neutral-400",
        )}
      >
        {children}
      </p>
    );
  }
  if (variant === "modern") {
    return (
      <p
        className={cn(base, "border-l-[3px] py-0.5 pl-2.5 tracking-[0.1em]")}
        style={{ color: accentColor, borderColor: accentColor }}
      >
        {children}
      </p>
    );
  }
  if (variant === "executive") {
    return (
      <p className={cn(base, "text-center tracking-[0.18em]")} style={{ color: accentColor }}>
        {children}
      </p>
    );
  }
  if (variant === "compact") {
    return (
      <p className={cn(base, "border-b border-neutral-300 pb-1 tracking-[0.08em] text-neutral-900")}>
        {children}
      </p>
    );
  }
  if (variant === "ats_safe") {
    return (
      <p
        className={cn(base, "border-b pb-1 tracking-[0.03em] text-neutral-900")}
        style={{ borderColor: accentColor }}
      >
        {children}
      </p>
    );
  }
  // classic
  return (
    <p className={cn(base, "tracking-[0.1em]")} style={{ color: accentColor }}>
      {children}
    </p>
  );
}

export function Section({
  variant,
  accentColor,
  title,
  centered,
  children,
}: {
  variant: TemplateSlug;
  accentColor: string;
  title: string;
  centered?: boolean;
  children: React.ReactNode;
}) {
  return (
    <section className={cn("flex flex-col", variant === "compact" ? "gap-1.5" : "gap-2.5")}>
      <SectionTitle variant={variant} accentColor={accentColor}>
        {title}
      </SectionTitle>
      <div
        className={cn(
          "flex flex-col",
          variant === "compact" ? "gap-2" : "gap-3",
          centered && "items-center text-center",
        )}
      >
        {children}
      </div>
    </section>
  );
}
