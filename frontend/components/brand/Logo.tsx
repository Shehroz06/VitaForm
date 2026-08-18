import { cn } from "@/lib/utils";

interface LogoMarkProps {
  className?: string;
}

/**
 * Abstract document + checkmark mark. Pure currentColor + one accent fill so
 * it reads correctly in both themes and at favicon scale without a raster
 * asset. Kept as a component (not just public/icon.svg) so it can be reused
 * inline wherever the wordmark needs a mark, e.g. the navbar.
 */
export function LogoMark({ className }: LogoMarkProps) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      className={cn("size-7", className)}
      aria-hidden="true"
    >
      <path
        d="M7 5.5C7 4.67157 7.67157 4 8.5 4H19L25 10V26.5C25 27.3284 24.3284 28 23.5 28H8.5C7.67157 28 7 27.3284 7 26.5V5.5Z"
        className="fill-primary"
      />
      <path d="M19 4L25 10H20.5C19.6716 10 19 9.32843 19 8.5V4Z" className="fill-primary-light" />
      <path
        d="M11.5 16.5L14.5 19.5L21 12"
        stroke="var(--color-background)"
        strokeWidth="2.1"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function Logo({ className, iconOnly = false }: LogoMarkProps & { iconOnly?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <LogoMark />
      {!iconOnly && (
        <span className="font-heading text-lg font-semibold tracking-tight text-foreground">
          VitaForm
        </span>
      )}
    </span>
  );
}
