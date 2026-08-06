"use client";

import { Sparkles } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useGenerateLinkedin } from "@/features/companion/hooks/use-companion";
import { ApiError } from "@/services/api-client";

export function GenerateLinkedinDialog() {
  const generateLinkedin = useGenerateLinkedin();
  const [open, setOpen] = useState(false);
  const [targetRole, setTargetRole] = useState("");

  const handleOpenChange = (next: boolean) => {
    setOpen(next);
    if (next) setTargetRole("");
  };

  const handleGenerate = () => {
    generateLinkedin.mutate(
      { target_role: targetRole.trim() || null },
      {
        onSuccess: () => {
          toast.success("LinkedIn content generated.");
          setOpen(false);
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
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button>
          <Sparkles className="size-4" /> Generate LinkedIn content
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Generate LinkedIn content</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="li-target-role">Target role (optional)</Label>
            <Input
              id="li-target-role"
              placeholder="Backend Engineer"
              value={targetRole}
              onChange={(event) => setTargetRole(event.target.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button onClick={handleGenerate} disabled={generateLinkedin.isPending}>
            {generateLinkedin.isPending ? "Generating..." : "Generate"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
