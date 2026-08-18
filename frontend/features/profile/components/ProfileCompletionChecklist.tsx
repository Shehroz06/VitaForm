"use client";

import { Check } from "lucide-react";
import type { User } from "@/features/auth/types";
import { useEducationList } from "@/features/profile/hooks/use-education";
import { useExperienceList } from "@/features/profile/hooks/use-experience";
import { useProjectList } from "@/features/profile/hooks/use-projects";
import { useSkillList } from "@/features/profile/hooks/use-skills";
import { cn } from "@/lib/utils";

/**
 * Mirrors the backend's exact completion formula (ProfileService.compute_completion_percentage):
 * 5 equal-weight checks — a full name, and at least one education/experience/project/skill.
 * Nothing else (certifications, awards, etc.) affects the percentage.
 */
export function ProfileCompletionChecklist({
  user,
  onJump,
}: {
  user: User;
  onJump: (tab: "basics" | "core") => void;
}) {
  const { data: education } = useEducationList();
  const { data: experience } = useExperienceList();
  const { data: projects } = useProjectList();
  const { data: skills } = useSkillList();

  const checks = [
    { label: "Your name", done: Boolean(user.first_name && user.last_name), tab: "basics" as const },
    { label: "At least one education entry", done: (education?.length ?? 0) > 0, tab: "core" as const },
    { label: "At least one experience entry", done: (experience?.length ?? 0) > 0, tab: "core" as const },
    { label: "At least one project", done: (projects?.length ?? 0) > 0, tab: "core" as const },
    { label: "At least one skill", done: (skills?.length ?? 0) > 0, tab: "core" as const },
  ];

  return (
    <div className="flex flex-col gap-1.5">
      <p className="text-xs font-medium text-muted-foreground">What counts toward 100%</p>
      <ul className="flex flex-col gap-0.5">
        {checks.map((check) => (
          <li key={check.label}>
            <button
              type="button"
              onClick={() => onJump(check.tab)}
              className="flex w-full items-center gap-2 rounded-md px-1.5 py-1 text-left text-sm transition-colors hover:bg-muted"
            >
              <span
                className={cn(
                  "flex size-4 shrink-0 items-center justify-center rounded-full ring-1 ring-inset",
                  check.done
                    ? "bg-success/15 text-success ring-success/30"
                    : "text-transparent ring-border",
                )}
              >
                <Check className="size-3" strokeWidth={3} />
              </span>
              <span className={cn(check.done ? "text-muted-foreground line-through" : "text-foreground")}>
                {check.label}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
