"use client";

import { useState } from "react";
import { ChevronDown, Eye, EyeOff, Search } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SECTION_ICONS } from "@/features/resumes/section-meta";
import type { ResumeSection } from "@/features/resumes/types";
import { cn } from "@/lib/utils";

export interface SelectableItem {
  id: string;
  label: string;
}

interface SectionCardShellProps {
  section: ResumeSection;
  defaultTitle: string;
  open: boolean;
  onToggleOpen: () => void;
  onVisibleChange: (visible: boolean) => void;
  badge?: string;
  titleSlot?: React.ReactNode;
  children: React.ReactNode;
}

function SectionCardShell({
  section,
  defaultTitle,
  open,
  onToggleOpen,
  onVisibleChange,
  badge,
  titleSlot,
  children,
}: SectionCardShellProps) {
  const Icon = SECTION_ICONS[section.section_type];

  return (
    <Card
      id={`section-${section.section_type}`}
      className={cn("scroll-mt-20 py-0 transition-opacity", !section.visible && "opacity-60")}
    >
      <div className="flex items-center gap-3 px-4 py-3.5">
        <button
          type="button"
          onClick={onToggleOpen}
          className="flex flex-1 items-center gap-3 text-left"
          aria-expanded={open}
        >
          <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground">
            <Icon className="size-4" />
          </span>
          <div className="min-w-0 flex-1">
            {titleSlot ?? (
              <p className="truncate text-sm font-medium text-foreground">
                {section.custom_title || defaultTitle}
              </p>
            )}
            {badge && <p className="text-xs text-muted-foreground">{badge}</p>}
          </div>
          <ChevronDown
            className={cn("size-4 shrink-0 text-muted-foreground transition-transform", open && "rotate-180")}
          />
        </button>

        <button
          type="button"
          onClick={() => onVisibleChange(!section.visible)}
          className="flex size-8 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          aria-label={section.visible ? "Hide section" : "Show section"}
          title={section.visible ? "Visible on resume" : "Hidden from resume"}
        >
          {section.visible ? <Eye className="size-4" /> : <EyeOff className="size-4" />}
        </button>
      </div>

      {open && <div className="flex flex-col gap-3 border-t border-border px-4 py-4">{children}</div>}
    </Card>
  );
}

export function SectionEditor({
  section,
  defaultTitle,
  items,
  open,
  onToggleOpen,
  onChange,
}: {
  section: ResumeSection;
  defaultTitle: string;
  items: SelectableItem[];
  open: boolean;
  onToggleOpen: () => void;
  onChange: (next: ResumeSection) => void;
}) {
  const [query, setQuery] = useState("");

  const toggleItem = (itemId: string, checked: boolean) => {
    onChange({
      ...section,
      item_ids: checked
        ? [...section.item_ids, itemId]
        : section.item_ids.filter((id) => id !== itemId),
    });
  };

  const filtered = query
    ? items.filter((item) => item.label.toLowerCase().includes(query.toLowerCase()))
    : items;

  return (
    <SectionCardShell
      section={section}
      defaultTitle={defaultTitle}
      open={open}
      onToggleOpen={onToggleOpen}
      onVisibleChange={(visible) => onChange({ ...section, visible })}
      badge={`${section.item_ids.length} of ${items.length} selected`}
    >
      <Input
        value={section.custom_title ?? ""}
        placeholder={defaultTitle}
        onChange={(event) => onChange({ ...section, custom_title: event.target.value || null })}
        className="h-8 max-w-xs"
        aria-label="Section title"
      />

      {items.length === 0 ? (
        <p className="text-xs text-muted-foreground">
          No {defaultTitle.toLowerCase()} on your profile yet.
        </p>
      ) : (
        <>
          {items.length > 6 && (
            <div className="relative">
              <Search className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={`Search ${defaultTitle.toLowerCase()}...`}
                className="h-8 pl-8 text-xs"
              />
            </div>
          )}
          <div className="flex max-h-56 flex-col gap-0.5 overflow-y-auto">
            {filtered.map((item) => (
              <label
                key={item.id}
                className="flex items-center gap-2.5 rounded-md px-1.5 py-1.5 text-sm transition-colors hover:bg-muted"
              >
                <Checkbox
                  checked={section.item_ids.includes(item.id)}
                  onCheckedChange={(checked) => toggleItem(item.id, checked === true)}
                />
                <span className="truncate">{item.label}</span>
              </label>
            ))}
            {filtered.length === 0 && (
              <p className="px-1.5 py-1 text-xs text-muted-foreground">No matches.</p>
            )}
          </div>
        </>
      )}
    </SectionCardShell>
  );
}

export function SummaryEditor({
  section,
  summary,
  open,
  onToggleOpen,
  onSectionChange,
  onSummaryChange,
}: {
  section: ResumeSection;
  summary: string;
  open: boolean;
  onToggleOpen: () => void;
  onSectionChange: (next: ResumeSection) => void;
  onSummaryChange: (text: string) => void;
}) {
  return (
    <SectionCardShell
      section={section}
      defaultTitle="Summary"
      open={open}
      onToggleOpen={onToggleOpen}
      onVisibleChange={(visible) => onSectionChange({ ...section, visible })}
    >
      <Label htmlFor="resume-summary" className="sr-only">
        Summary
      </Label>
      <textarea
        id="resume-summary"
        value={summary}
        onChange={(event) => onSummaryChange(event.target.value)}
        rows={4}
        placeholder="A short professional summary..."
        className="w-full rounded-lg border border-input bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
      />
    </SectionCardShell>
  );
}
