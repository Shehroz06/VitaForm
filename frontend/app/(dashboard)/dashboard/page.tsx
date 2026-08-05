"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useLogout } from "@/features/auth/hooks/use-auth";
import { useAuthStore } from "@/store/auth-store";

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user);
  const logout = useLogout();
  const router = useRouter();

  const handleLogout = () => {
    logout.mutate(undefined, {
      onSettled: () => router.push("/login"),
    });
  };

  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="text-2xl font-semibold">Welcome{user?.first_name ? `, ${user.first_name}` : ""}</h1>
      <p className="text-muted-foreground">{user?.email}</p>
      <div className="flex gap-3">
        <Button asChild>
          <Link href="/profile">Edit profile</Link>
        </Button>
        <Button asChild variant="secondary">
          <Link href="/resumes">Resumes</Link>
        </Button>
        <Button variant="outline" onClick={handleLogout} disabled={logout.isPending}>
          {logout.isPending ? "Logging out..." : "Log out"}
        </Button>
      </div>
    </main>
  );
}
