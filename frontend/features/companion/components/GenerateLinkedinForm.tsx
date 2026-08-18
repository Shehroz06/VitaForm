"use client";

import { IdCard } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useGenerateLinkedin } from "@/features/companion/hooks/use-companion";
import { ApiError } from "@/services/api-client";

export function GenerateLinkedinForm() {
  const generateLinkedin = useGenerateLinkedin();
  const [targetRole, setTargetRole] = useState("");

  const handleGenerate = () => {
    generateLinkedin.mutate(
      { target_role: targetRole.trim() || null },
      {
        onSuccess: () => {
          toast.success("LinkedIn content generated.");
          setTargetRole("");
        },
        onError: (error) => {
          toast.error(
            error instanceof ApiError ? error.message : "Failed to generate LinkedIn content.",
          );
        },
      },
    );
  };

  return (
    <div className="flex flex-col gap-4 rounded-2xl bg-card p-5 ring-1 ring-foreground/10">
      <div className="flex items-center gap-2">
        <span className="flex size-8 items-center justify-center rounded-lg bg-accent text-accent-foreground">
          <IdCard className="size-4" />
        </span>
        <div>
          <h2 className="font-heading text-base font-medium text-foreground">
            Generate LinkedIn content
          </h2>
          <p className="text-sm text-muted-foreground">
            Draft a headline and About section from your real profile data.
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-1.5 sm:max-w-sm">
        <Label htmlFor="li-target-role">Target role (optional)</Label>
        <Input
          id="li-target-role"
          placeholder="Backend Engineer"
          value={targetRole}
          onChange={(event) => setTargetRole(event.target.value)}
        />
      </div>

      <Button onClick={handleGenerate} disabled={generateLinkedin.isPending} className="self-start">
        {generateLinkedin.isPending ? "Generating..." : "Generate with AI"}
      </Button>
    </div>
  );
}
