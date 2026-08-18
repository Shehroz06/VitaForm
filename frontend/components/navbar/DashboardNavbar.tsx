"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Briefcase,
  FileText,
  LayoutDashboard,
  LayoutTemplate,
  LogOut,
  Menu,
  User,
} from "lucide-react";
import { Logo } from "@/components/brand/Logo";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { useLogout } from "@/features/auth/hooks/use-auth";
import { useAuthStore } from "@/store/auth-store";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/profile", label: "Profile", icon: User },
  { href: "/templates", label: "Templates", icon: LayoutTemplate },
  { href: "/resumes", label: "Resumes", icon: FileText },
  { href: "/applications", label: "Applications", icon: Briefcase, matchAlso: ["/jobs"] },
] as const;

function isActive(pathname: string, href: string, matchAlso?: readonly string[]) {
  if (href === "/dashboard") return pathname === href;
  return pathname.startsWith(href) || Boolean(matchAlso?.some((alt) => pathname.startsWith(alt)));
}

function initials(firstName?: string | null, lastName?: string | null, email?: string) {
  const first = firstName?.[0] ?? "";
  const last = lastName?.[0] ?? "";
  const combined = `${first}${last}`.toUpperCase();
  return combined || email?.[0]?.toUpperCase() || "U";
}

export function DashboardNavbar() {
  const pathname = usePathname();
  const user = useAuthStore((state) => state.user);
  const logout = useLogout();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = React.useState(false);

  const handleLogout = () => {
    logout.mutate(undefined, {
      onSettled: () => router.push("/login"),
    });
  };

  return (
    <header className="sticky top-0 z-40 border-b border-border/80 bg-background/85 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-[1400px] items-center gap-2 px-4 sm:px-6">
        <Link href="/dashboard" className="mr-2 shrink-0">
          <Logo />
        </Link>

        <nav className="hidden flex-1 items-center gap-1 lg:flex">
          {NAV_ITEMS.map(({ href, label, icon: Icon, ...rest }) => {
            const active = isActive(pathname, href, "matchAlso" in rest ? rest.matchAlso : undefined);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                  active && "bg-accent text-accent-foreground"
                )}
              >
                <Icon className="size-4" />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="ml-auto flex items-center gap-1.5">
          <ThemeToggle />

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                className="hidden items-center gap-2 rounded-full p-0.5 pr-2.5 transition-colors hover:bg-muted lg:flex"
                aria-label="Account menu"
              >
                <Avatar size="sm">
                  <AvatarFallback>{initials(user?.first_name, user?.last_name, user?.email)}</AvatarFallback>
                </Avatar>
                <span className="max-w-32 truncate text-sm font-medium">
                  {user?.first_name || user?.email}
                </span>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="min-w-56">
              <DropdownMenuLabel className="flex flex-col gap-0.5 px-2 py-1.5">
                <span className="text-sm font-medium text-foreground">
                  {user?.first_name ? `${user.first_name} ${user.last_name ?? ""}`.trim() : "Your account"}
                </span>
                <span className="truncate text-xs text-muted-foreground">{user?.email}</span>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link href="/profile">
                  <User className="size-4" />
                  Profile
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                variant="destructive"
                onClick={handleLogout}
                disabled={logout.isPending}
              >
                <LogOut className="size-4" />
                {logout.isPending ? "Logging out..." : "Log out"}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open menu">
                <Menu className="size-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-72">
              <SheetHeader>
                <SheetTitle>
                  <Logo />
                </SheetTitle>
              </SheetHeader>
              <div className="flex flex-col gap-1 px-2">
                {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
                  const active = isActive(pathname, href);
                  return (
                    <Link
                      key={href}
                      href={href}
                      onClick={() => setMobileOpen(false)}
                      className={cn(
                        "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                        active && "bg-accent text-accent-foreground"
                      )}
                    >
                      <Icon className="size-4" />
                      {label}
                    </Link>
                  );
                })}
              </div>
              <div className="mt-auto flex flex-col gap-2 border-t border-border p-4">
                <div className="flex items-center gap-2.5">
                  <Avatar size="sm">
                    <AvatarFallback>
                      {initials(user?.first_name, user?.last_name, user?.email)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-foreground">
                      {user?.first_name ? `${user.first_name} ${user.last_name ?? ""}`.trim() : "Your account"}
                    </p>
                    <p className="truncate text-xs text-muted-foreground">{user?.email}</p>
                  </div>
                </div>
                <Button
                  variant="outline"
                  className="justify-start gap-2"
                  onClick={handleLogout}
                  disabled={logout.isPending}
                >
                  <LogOut className="size-4" />
                  {logout.isPending ? "Logging out..." : "Log out"}
                </Button>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
