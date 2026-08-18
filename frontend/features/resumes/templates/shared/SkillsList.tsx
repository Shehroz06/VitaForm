import { cn } from "@/lib/utils";
import type { ResumePreviewItem, TemplateSlug } from "@/features/resumes/templates/types";

export function SkillsList({
  items,
  variant,
  accentColor,
  centered,
}: {
  items: ResumePreviewItem[];
  variant: TemplateSlug;
  accentColor: string;
  centered?: boolean;
}) {
  if (items.length === 0) return null;
  const justify = centered ? "justify-center" : "";

  if (variant === "minimal") {
    return (
      <p className={cn("text-[12px] text-neutral-500", centered && "text-center")}>
        {items.map((item) => item.title).join("   ")}
      </p>
    );
  }

  if (variant === "ats_safe") {
    // Plain comma-separated text, no pills/borders -- matches the backend
    // template's most-conservative rendering exactly.
    return (
      <p className={cn("text-[12px] text-neutral-900", centered && "text-center")}>
        {items.map((item) => item.title).join(", ")}
      </p>
    );
  }

  if (variant === "modern") {
    return (
      <div className={cn("flex flex-wrap gap-1.5", justify)}>
        {items.map((item) => (
          <span
            key={item.id}
            className="rounded-full px-2.5 py-1 text-[11px] font-medium"
            style={{ backgroundColor: `${accentColor}22`, color: accentColor }}
          >
            {item.title}
          </span>
        ))}
      </div>
    );
  }

  if (variant === "executive") {
    return (
      <div className={cn("flex flex-wrap gap-2", justify)}>
        {items.map((item) => (
          <span
            key={item.id}
            className="rounded-[2px] border px-2.5 py-1 text-[11px]"
            style={{ borderColor: accentColor, color: accentColor }}
          >
            {item.title}
          </span>
        ))}
      </div>
    );
  }

  // classic + compact
  return (
    <div className={cn("flex flex-wrap gap-1.5", justify)}>
      {items.map((item) => (
        <span
          key={item.id}
          className="rounded border border-neutral-300 px-2.5 py-1 text-[11px] text-neutral-700"
        >
          {item.title}
        </span>
      ))}
    </div>
  );
}
