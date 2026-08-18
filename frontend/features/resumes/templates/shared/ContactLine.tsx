import { cn } from "@/lib/utils";

export function ContactLine({ items, centered }: { items: string[]; centered?: boolean }) {
  if (items.length === 0) return null;
  return (
    <p className={cn("text-[11px] text-neutral-400", centered && "text-center")}>
      {items.join("   ·   ")}
    </p>
  );
}
