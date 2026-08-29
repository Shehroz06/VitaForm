"use client";

import { Palette } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ACCENT_OPTIONS, FONT_OPTIONS } from "@/features/resumes/templates/style-options";
import type { TemplateConfig, TemplateSpacing } from "@/features/resumes/templates/types";
import { cn } from "@/lib/utils";

export function TemplateCustomizer({
  config,
  onChange,
  onReset,
}: {
  config: TemplateConfig;
  onChange: (patch: Partial<TemplateConfig>) => void;
  onReset: () => void;
}) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5 border-transparent bg-transparent text-sm font-normal shadow-none hover:bg-muted"
        >
          <Palette className="size-4" />
          Customize
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="flex w-64 flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-muted-foreground">Accent color</span>
          <div className="flex flex-wrap gap-2">
            {ACCENT_OPTIONS.map((accent) => (
              <button
                key={accent.value}
                type="button"
                onClick={() => onChange({ accentColor: accent.value })}
                aria-label={accent.name}
                aria-pressed={config.accentColor === accent.value}
                className={cn(
                  "size-7 rounded-full ring-1 ring-foreground/10 transition-transform hover:scale-110",
                  config.accentColor === accent.value && "ring-2 ring-offset-2 ring-offset-popover",
                )}
                style={{ backgroundColor: accent.value }}
              />
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-muted-foreground">Font</span>
          <div className="grid grid-cols-2 gap-1.5">
            {FONT_OPTIONS.map((font) => (
              <button
                key={font.value}
                type="button"
                onClick={() => onChange({ fontFamily: font.value })}
                aria-pressed={config.fontFamily === font.value}
                className={cn(
                  "rounded-md px-2 py-1.5 text-xs ring-1 ring-foreground/10 transition-colors hover:bg-muted",
                  config.fontFamily === font.value && "bg-primary/10 ring-2 ring-primary",
                )}
              >
                {font.name}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-muted-foreground">Spacing</span>
          <Tabs
            value={config.spacing}
            onValueChange={(value) => onChange({ spacing: value as TemplateSpacing })}
          >
            <TabsList className="w-full">
              <TabsTrigger value="compact" className="flex-1">
                Compact
              </TabsTrigger>
              <TabsTrigger value="cozy" className="flex-1">
                Cozy
              </TabsTrigger>
              <TabsTrigger value="relaxed" className="flex-1">
                Relaxed
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <label className="flex items-center justify-between gap-2">
          <span className="flex flex-col">
            <span className="text-xs font-medium text-muted-foreground">Bold keywords</span>
            <span className="text-[11px] text-muted-foreground/80">
              Render **bold** markup in descriptions
            </span>
          </span>
          <Switch
            checked={config.boldMarkup ?? true}
            onCheckedChange={(checked) => onChange({ boldMarkup: checked })}
            aria-label="Bold keyword markup"
          />
        </label>

        <Button
          variant="ghost"
          size="sm"
          onClick={onReset}
          className="self-start px-0 text-xs text-muted-foreground hover:bg-transparent hover:underline"
        >
          Reset to template default
        </Button>
      </PopoverContent>
    </Popover>
  );
}
