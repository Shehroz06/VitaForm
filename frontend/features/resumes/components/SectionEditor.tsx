"use client";

import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  Eye,
  EyeOff,
  Loader2,
  Pencil,
  Plus,
  Sparkles,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useRewriteResumeText } from "@/features/resumes/hooks/use-resume-content";
import { SECTION_ICONS } from "@/features/resumes/section-meta";
import type { ResumePreviewItem } from "@/features/resumes/templates/types";
import type { ResumeSection } from "@/features/resumes/types";
import { cn } from "@/lib/utils";

interface SectionCardShellProps {
  section: ResumeSection;
  defaultTitle: string;
  open: boolean;
  onToggleOpen: () => void;
  onVisibleChange: (visible: boolean) => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  canMoveUp: boolean;
  canMoveDown: boolean;
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
  onMoveUp,
  onMoveDown,
  canMoveUp,
  canMoveDown,
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
      <div className="flex items-center gap-1 px-4 py-3.5">
        <div className="flex shrink-0 flex-col">
          <button
            type="button"
            onClick={onMoveUp}
            disabled={!canMoveUp}
            className="flex size-4 items-center justify-center text-muted-foreground transition-colors hover:text-foreground disabled:opacity-25"
            aria-label="Move section up"
          >
            <ChevronUp className="size-3.5" />
          </button>
          <button
            type="button"
            onClick={onMoveDown}
            disabled={!canMoveDown}
            className="flex size-4 items-center justify-center text-muted-foreground transition-colors hover:text-foreground disabled:opacity-25"
            aria-label="Move section down"
          >
            <ChevronDown className="size-3.5" />
          </button>
        </div>

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

/** One selected item: reorder within the section, remove it, and -- for
 * section types with a sub-heading (see ITEM_EDITABLE_SECTIONS) -- edit its
 * title/org/description for this resume only, with an AI rephrase option
 * for the description. Collapsed by default so a section with several
 * entries doesn't turn into a wall of textareas. */
function ItemRow({
  item,
  editable,
  isFirst,
  isLast,
  resumeId,
  titleOverride,
  subtitleOverride,
  descriptionOverride,
  onMoveUp,
  onMoveDown,
  onRemove,
  onOverrideChange,
}: {
  item: ResumePreviewItem;
  editable: boolean;
  isFirst: boolean;
  isLast: boolean;
  resumeId: string;
  titleOverride: string | undefined;
  subtitleOverride: string | undefined;
  descriptionOverride: string | undefined;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onRemove: () => void;
  onOverrideChange: (field: "title" | "subtitle" | "description", value: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const rewrite = useRewriteResumeText(resumeId);
  const effectiveDescription = descriptionOverride ?? item.description ?? "";

  const handleRephrase = () => {
    if (!effectiveDescription.trim()) {
      toast.info("Nothing to rephrase -- this entry has no description yet.");
      return;
    }
    rewrite.mutate(
      { text: effectiveDescription },
      {
        onSuccess: (result) => {
          if (result.rewritten_text) {
            onOverrideChange("description", result.rewritten_text);
            toast.success("Description rephrased.");
          } else {
            toast.info("Couldn't improve this one -- kept the original.");
          }
        },
        onError: () => toast.error("Rephrase failed. Try again in a moment."),
      },
    );
  };

  return (
    <div className="rounded-lg border border-border">
      <div className="flex items-center gap-2 px-2.5 py-2">
        <div className="flex shrink-0 flex-col">
          <button
            type="button"
            onClick={onMoveUp}
            disabled={isFirst}
            className="flex size-4 items-center justify-center text-muted-foreground transition-colors hover:text-foreground disabled:opacity-25"
            aria-label="Move up"
          >
            <ChevronUp className="size-3" />
          </button>
          <button
            type="button"
            onClick={onMoveDown}
            disabled={isLast}
            className="flex size-4 items-center justify-center text-muted-foreground transition-colors hover:text-foreground disabled:opacity-25"
            aria-label="Move down"
          >
            <ChevronDown className="size-3" />
          </button>
        </div>

        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-foreground">
            {titleOverride || item.title}
          </p>
          {(subtitleOverride || item.subtitle) && (
            <p className="truncate text-xs text-muted-foreground">
              {subtitleOverride || item.subtitle}
            </p>
          )}
        </div>

        {editable && (
          <button
            type="button"
            onClick={() => setEditing((v) => !v)}
            className={cn(
              "flex size-7 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
              editing && "bg-muted text-foreground",
            )}
            aria-label="Edit for this resume"
            title="Edit title, org, or description for this resume only"
          >
            <Pencil className="size-3.5" />
          </button>
        )}
        <button
          type="button"
          onClick={onRemove}
          className="flex size-7 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
          aria-label="Remove from this resume"
        >
          <X className="size-3.5" />
        </button>
      </div>

      {editable && editing && (
        <div className="flex flex-col gap-2.5 border-t border-border px-2.5 py-2.5">
          <p className="text-[11px] text-muted-foreground">
            Overrides apply to this resume only -- your profile is never changed.
          </p>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            <div>
              <Label className="text-[11px] text-muted-foreground">Title</Label>
              <Input
                value={titleOverride ?? ""}
                placeholder={item.title}
                onChange={(event) => onOverrideChange("title", event.target.value)}
                className="h-8 text-sm"
              />
            </div>
            {item.subtitle !== undefined && (
              <div>
                <Label className="text-[11px] text-muted-foreground">Organization</Label>
                <Input
                  value={subtitleOverride ?? ""}
                  placeholder={item.subtitle}
                  onChange={(event) => onOverrideChange("subtitle", event.target.value)}
                  className="h-8 text-sm"
                />
              </div>
            )}
          </div>
          <div>
            <div className="mb-1 flex items-center justify-between">
              <Label className="text-[11px] text-muted-foreground">Description</Label>
              <button
                type="button"
                onClick={handleRephrase}
                disabled={rewrite.isPending}
                className="flex items-center gap-1 text-[11px] font-medium text-primary transition-opacity hover:opacity-80 disabled:opacity-50"
              >
                {rewrite.isPending ? (
                  <Loader2 className="size-3 animate-spin" />
                ) : (
                  <Sparkles className="size-3" />
                )}
                Rephrase with AI
              </button>
            </div>
            <textarea
              value={effectiveDescription}
              onChange={(event) => onOverrideChange("description", event.target.value)}
              rows={3}
              placeholder="No description on your profile yet."
              className="w-full rounded-lg border border-input bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>
        </div>
      )}
    </div>
  );
}

export function SectionEditor({
  section,
  defaultTitle,
  items,
  editable,
  open,
  onToggleOpen,
  onChange,
  onMoveUp,
  onMoveDown,
  canMoveUp,
  canMoveDown,
  resumeId,
  titleOverrides,
  subtitleOverrides,
  descriptionOverrides,
  onOverrideChange,
}: {
  section: ResumeSection;
  defaultTitle: string;
  items: ResumePreviewItem[];
  editable: boolean;
  open: boolean;
  onToggleOpen: () => void;
  onChange: (next: ResumeSection) => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  canMoveUp: boolean;
  canMoveDown: boolean;
  resumeId: string;
  titleOverrides: Record<string, string>;
  subtitleOverrides: Record<string, string>;
  descriptionOverrides: Record<string, string>;
  onOverrideChange: (field: "title" | "subtitle" | "description", itemId: string, value: string) => void;
}) {
  const [query, setQuery] = useState("");

  const byId = new Map(items.map((item) => [item.id, item]));
  const selectedItems = section.item_ids
    .map((id) => byId.get(id))
    .filter((item): item is ResumePreviewItem => Boolean(item));
  const unselectedItems = items.filter((item) => !section.item_ids.includes(item.id));

  const addItem = (itemId: string) => {
    onChange({ ...section, item_ids: [...section.item_ids, itemId] });
  };

  const removeItem = (itemId: string) => {
    onChange({ ...section, item_ids: section.item_ids.filter((id) => id !== itemId) });
  };

  const moveItem = (index: number, direction: -1 | 1) => {
    const target = index + direction;
    if (target < 0 || target >= section.item_ids.length) return;
    const item_ids = [...section.item_ids];
    [item_ids[index], item_ids[target]] = [item_ids[target], item_ids[index]];
    onChange({ ...section, item_ids });
  };

  const filtered = query
    ? unselectedItems.filter((item) => item.title.toLowerCase().includes(query.toLowerCase()))
    : unselectedItems;

  return (
    <SectionCardShell
      section={section}
      defaultTitle={defaultTitle}
      open={open}
      onToggleOpen={onToggleOpen}
      onVisibleChange={(visible) => onChange({ ...section, visible })}
      onMoveUp={onMoveUp}
      onMoveDown={onMoveDown}
      canMoveUp={canMoveUp}
      canMoveDown={canMoveDown}
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
          {selectedItems.length > 0 && (
            <div className="flex flex-col gap-1.5">
              {selectedItems.map((item, index) => (
                <ItemRow
                  key={item.id}
                  item={item}
                  editable={editable}
                  isFirst={index === 0}
                  isLast={index === selectedItems.length - 1}
                  resumeId={resumeId}
                  titleOverride={titleOverrides[item.id]}
                  subtitleOverride={subtitleOverrides[item.id]}
                  descriptionOverride={descriptionOverrides[item.id]}
                  onMoveUp={() => moveItem(index, -1)}
                  onMoveDown={() => moveItem(index, 1)}
                  onRemove={() => removeItem(item.id)}
                  onOverrideChange={(field, value) => onOverrideChange(field, item.id, value)}
                />
              ))}
            </div>
          )}

          {unselectedItems.length > 0 && (
            <div className="flex flex-col gap-1.5">
              {unselectedItems.length > 6 && (
                <div className="relative">
                  <Input
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder={`Search ${defaultTitle.toLowerCase()}...`}
                    className="h-8 text-xs"
                  />
                </div>
              )}
              <div className="flex max-h-56 flex-col gap-0.5 overflow-y-auto">
                {filtered.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => addItem(item.id)}
                    className="flex items-center gap-2 rounded-md px-1.5 py-1.5 text-left text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                  >
                    <Plus className="size-3.5 shrink-0" />
                    <span className="truncate">{item.title}</span>
                  </button>
                ))}
                {filtered.length === 0 && (
                  <p className="px-1.5 py-1 text-xs text-muted-foreground">No matches.</p>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </SectionCardShell>
  );
}

export function SummaryEditor({
  section,
  summary,
  resumeId,
  open,
  onToggleOpen,
  onSectionChange,
  onSummaryChange,
  onMoveUp,
  onMoveDown,
  canMoveUp,
  canMoveDown,
}: {
  section: ResumeSection;
  summary: string;
  resumeId: string;
  open: boolean;
  onToggleOpen: () => void;
  onSectionChange: (next: ResumeSection) => void;
  onSummaryChange: (text: string) => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  canMoveUp: boolean;
  canMoveDown: boolean;
}) {
  const rewrite = useRewriteResumeText(resumeId);

  const handleRephrase = () => {
    if (!summary.trim()) {
      toast.info("Write a summary first, then rephrase it.");
      return;
    }
    rewrite.mutate(
      { text: summary },
      {
        onSuccess: (result) => {
          if (result.rewritten_text) {
            onSummaryChange(result.rewritten_text);
            toast.success("Summary rephrased.");
          } else {
            toast.info("Couldn't improve this one -- kept the original.");
          }
        },
        onError: () => toast.error("Rephrase failed. Try again in a moment."),
      },
    );
  };

  return (
    <SectionCardShell
      section={section}
      defaultTitle="Summary"
      open={open}
      onToggleOpen={onToggleOpen}
      onVisibleChange={(visible) => onSectionChange({ ...section, visible })}
      onMoveUp={onMoveUp}
      onMoveDown={onMoveDown}
      canMoveUp={canMoveUp}
      canMoveDown={canMoveDown}
    >
      <Label htmlFor="resume-summary" className="sr-only">
        Summary
      </Label>
      <div className="flex items-center justify-end">
        <button
          type="button"
          onClick={handleRephrase}
          disabled={rewrite.isPending}
          className="flex items-center gap-1 text-xs font-medium text-primary transition-opacity hover:opacity-80 disabled:opacity-50"
        >
          {rewrite.isPending ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : (
            <Sparkles className="size-3.5" />
          )}
          Rephrase with AI
        </button>
      </div>
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
