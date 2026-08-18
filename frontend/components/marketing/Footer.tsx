import { Logo } from "@/components/brand/Logo";

export function Footer() {
  return (
    <footer className="border-t border-border py-10">
      <div className="mx-auto flex max-w-[1240px] flex-col items-center gap-4 px-4 sm:flex-row sm:justify-between sm:px-6">
        <Logo />
        <p className="text-xs text-muted-foreground">
          © {new Date().getFullYear()} VitaForm. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
