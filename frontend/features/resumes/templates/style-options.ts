import type { TemplateFontFamily } from "@/features/resumes/templates/types";

// Colors have no bearing on ATS parsing (the parser only reads text) --
// this list is purely a human-reader aesthetic choice, so it deliberately
// sticks to professional, readable-contrast tones and avoids neon/pastel.
// Shared between the builder's TemplateCustomizer and the pre-generation
// template/color picker so there's exactly one real palette, not two.
export const ACCENT_OPTIONS = [
  { name: "Charcoal", value: "#1a1a1a" },
  { name: "Slate", value: "#4a5563" },
  { name: "Navy", value: "#2c4a6e" },
  { name: "Steel Blue", value: "#3b6690" },
  { name: "Teal", value: "#1f6f6f" },
  { name: "Emerald", value: "#2f6f56" },
  { name: "Forest", value: "#33622f" },
  { name: "Burgundy", value: "#6b2b3a" },
  { name: "Wine", value: "#7a2e4d" },
  { name: "Wood Brown", value: "#8b5e3c" },
  { name: "Purple", value: "#5b4a80" },
  { name: "Black", value: "#000000" },
] as const;

export const FONT_OPTIONS: { name: string; value: TemplateFontFamily }[] = [
  { name: "Arial", value: "arial" },
  { name: "Calibri", value: "calibri" },
  { name: "Times New Roman", value: "times" },
  { name: "Georgia", value: "georgia" },
];
