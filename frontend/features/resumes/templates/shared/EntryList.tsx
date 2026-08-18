import { cn } from "@/lib/utils";
import type { ResumePreviewItem, TemplateSlug } from "@/features/resumes/templates/types";

export function EntryList({
  items,
  variant,
  centered,
}: {
  items: ResumePreviewItem[];
  variant: TemplateSlug;
  centered?: boolean;
}) {
  if (items.length === 0) return null;

  return (
    <div className={cn("flex flex-col", variant === "compact" ? "gap-2.5" : "gap-3.5")}>
      {items.map((item) => (
        <div key={item.id} className="flex flex-col gap-0.5">
          <div
            className={cn(
              "flex items-baseline justify-between gap-3",
              centered && "justify-center gap-4",
            )}
          >
            <span className="text-[13px] font-semibold text-neutral-900">{item.title}</span>
            {item.dateRange && (
              <span className="shrink-0 text-[11px] whitespace-nowrap text-neutral-400">
                {item.dateRange}
              </span>
            )}
          </div>
          {(item.subtitle || item.meta) && (
            <p
              className={cn(
                "text-[12px] text-neutral-600",
                variant === "modern" ? "font-semibold" : "italic",
                centered && "text-center",
              )}
            >
              {[item.subtitle, item.meta].filter(Boolean).join(" · ")}
            </p>
          )}
          {item.description && (
            <p
              className={cn(
                "text-[12px] leading-snug whitespace-pre-line text-neutral-700",
                centered && "text-center",
              )}
            >
              {item.description}
            </p>
          )}
          {item.tags && item.tags.length > 0 && (
            <p className={cn("text-[11px] text-neutral-500", centered && "text-center")}>
              {item.tags.join(", ")}
            </p>
          )}
          {item.links && item.links.length > 0 && (
            <p className={cn("text-[11px] text-neutral-500", centered && "text-center")}>
              {item.links.join(" · ")}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
