import { Info } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

export function CompletionBar({
  percentage,
  infoContent,
}: {
  percentage: number;
  infoContent?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className="flex items-center gap-1 font-medium">
          Profile completion
          {infoContent && percentage < 100 && (
            <Popover>
              <PopoverTrigger asChild>
                <button
                  type="button"
                  aria-label="What counts toward 100%"
                  className="flex size-4 items-center justify-center rounded-full text-muted-foreground transition-colors hover:text-foreground"
                >
                  <Info className="size-3.5" />
                </button>
              </PopoverTrigger>
              <PopoverContent align="start" className="w-64">
                {infoContent}
              </PopoverContent>
            </Popover>
          )}
        </span>
        <span className="text-muted-foreground">{percentage}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-all"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
