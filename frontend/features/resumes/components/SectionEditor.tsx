"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { ResumeSection } from "@/features/resumes/types";

export interface SelectableItem {
  id: string;
  label: string;
}

export function SectionEditor({
  section,
  defaultTitle,
  items,
  onChange,
}: {
  section: ResumeSection;
  defaultTitle: string;
  items: SelectableItem[];
  onChange: (next: ResumeSection) => void;
}) {
  const toggleItem = (itemId: string, checked: boolean) => {
    onChange({
      ...section,
      item_ids: checked
        ? [...section.item_ids, itemId]
        : section.item_ids.filter((id) => id !== itemId),
    });
  };

  return (
    <div className="rounded-lg border p-3">
      <div className="flex items-center gap-3">
        <Checkbox
          checked={section.visible}
          onCheckedChange={(checked) => onChange({ ...section, visible: checked === true })}
          aria-label={`Show ${defaultTitle} section`}
        />
        <Input
          value={section.custom_title ?? ""}
          placeholder={defaultTitle}
          onChange={(event) => onChange({ ...section, custom_title: event.target.value || null })}
          className="h-8 max-w-xs"
        />
      </div>

      {items.length === 0 ? (
        <p className="mt-2 pl-7 text-xs text-muted-foreground">
          No {defaultTitle.toLowerCase()} on your profile yet.
        </p>
      ) : (
        <div className="mt-2 flex flex-col gap-1.5 pl-7">
          {items.map((item) => (
            <label key={item.id} className="flex items-center gap-2 text-sm">
              <Checkbox
                checked={section.item_ids.includes(item.id)}
                onCheckedChange={(checked) => toggleItem(item.id, checked === true)}
              />
              {item.label}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

export function SummaryEditor({
  section,
  summary,
  onSectionChange,
  onSummaryChange,
}: {
  section: ResumeSection;
  summary: string;
  onSectionChange: (next: ResumeSection) => void;
  onSummaryChange: (text: string) => void;
}) {
  return (
    <div className="rounded-lg border p-3">
      <div className="flex items-center gap-3">
        <Checkbox
          checked={section.visible}
          onCheckedChange={(checked) => onSectionChange({ ...section, visible: checked === true })}
          aria-label="Show Summary section"
        />
        <Label className="text-sm font-medium">Summary</Label>
      </div>
      <textarea
        value={summary}
        onChange={(event) => onSummaryChange(event.target.value)}
        rows={3}
        placeholder="A short professional summary..."
        className="mt-2 w-full rounded-md border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
      />
    </div>
  );
}
