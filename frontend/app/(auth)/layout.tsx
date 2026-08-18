"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowLeft } from "lucide-react";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isRegister = pathname === "/register";

  return (
    <main className="relative flex flex-1 items-center justify-center px-4 py-12">
      <Link
        href={isRegister ? "/login" : "/"}
        className="absolute top-4 left-4 flex items-center gap-1.5 text-sm font-medium text-primary transition-colors hover:text-primary/70 sm:top-6 sm:left-6"
      >
        <ArrowLeft className="size-4" />
        {isRegister ? "Back to login" : "Back to home"}
      </Link>
      <div className="w-full max-w-sm">{children}</div>
    </main>
  );
}
