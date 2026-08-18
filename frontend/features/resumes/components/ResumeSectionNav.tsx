"use client";

import { EyeOff } from "lucide-react";
import { SECTION_ICONS, SECTION_LABELS } from "@/features/resumes/section-meta";
import type { ResumeSection } from "@/features/resumes/types";
import { cn } from "@/lib/utils";

export function ResumeSectionNav({
  sections,
  onNavigate,
}: {
  sections: ResumeSection[];
  onNavigate: (sectionType: ResumeSection["section_type"]) => void;
}) {
  return (
    <nav className="flex flex-col gap-0.5">
      {sections.map((section) => {
        const Icon = SECTION_ICONS[section.section_type];
        const label = section.section_type === "summary" ? "Summary" : SECTION_LABELS[section.section_type];
        const count = section.item_ids.length;

        return (
          <button
            key={section.section_type}
            type="button"
            onClick={() => onNavigate(section.section_type)}
            className="flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <Icon className="size-4 shrink-0" />
            <span className="min-w-0 flex-1 truncate">{section.custom_title || label}</span>
            {!section.visible && <EyeOff className="size-3.5 shrink-0 opacity-60" />}
            {section.section_type !== "summary" && count > 0 && (
              <span
                className={cn(
                  "flex h-4 min-w-4 shrink-0 items-center justify-center rounded-full px-1 text-[10px] font-medium",
                  "bg-accent text-accent-foreground"
                )}
              >
                {count}
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );
}
