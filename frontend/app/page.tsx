import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="text-3xl font-semibold tracking-tight">AI Career Operating System</h1>
      <p className="max-w-md text-muted-foreground">
        One profile. Infinite documents. Build in progress.
      </p>
      <div className="flex gap-3">
        <Button asChild>
          <Link href="/register">Get started</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/login">Log in</Link>
        </Button>
      </div>
    </main>
  );
}
