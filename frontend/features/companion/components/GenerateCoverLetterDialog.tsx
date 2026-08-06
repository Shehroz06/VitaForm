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
import { Textarea } from "@/components/ui/textarea";
import { useGenerateCoverLetter } from "@/features/companion/hooks/use-companion";
import { ApiError } from "@/services/api-client";

export function GenerateCoverLetterDialog() {
  const generateCoverLetter = useGenerateCoverLetter();
  const [open, setOpen] = useState(false);
  const [companyName, setCompanyName] = useState("");
  const [roleTitle, setRoleTitle] = useState("");
  const [hiringManager, setHiringManager] = useState("");
  const [jobDescriptionText, setJobDescriptionText] = useState("");

  const handleOpenChange = (next: boolean) => {
    setOpen(next);
    if (next) {
      setCompanyName("");
      setRoleTitle("");
      setHiringManager("");
      setJobDescriptionText("");
    }
  };

  const handleGenerate = () => {
    if (!companyName.trim() || !roleTitle.trim()) return;
    generateCoverLetter.mutate(
      {
        company_name: companyName.trim(),
        role_title: roleTitle.trim(),
        hiring_manager: hiringManager.trim() || null,
        job_description_text: jobDescriptionText.trim() || null,
      },
      {
        onSuccess: () => {
          toast.success("Cover letter generated.");
          setOpen(false);
        },
        onError: (error) => {
          toast.error(
            error instanceof ApiError ? error.message : "Failed to generate cover letter.",
          );
        },
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button>
          <Sparkles className="size-4" /> Generate cover letter
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Generate a cover letter</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="cl-company">Company</Label>
              <Input
                id="cl-company"
                placeholder="Acme Corp"
                value={companyName}
                onChange={(event) => setCompanyName(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="cl-role">Role</Label>
              <Input
                id="cl-role"
                placeholder="Backend Engineer"
                value={roleTitle}
                onChange={(event) => setRoleTitle(event.target.value)}
              />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="cl-hiring-manager">Hiring manager (optional)</Label>
            <Input
              id="cl-hiring-manager"
              placeholder="Jane Doe"
              value={hiringManager}
              onChange={(event) => setHiringManager(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="cl-job-description">Job description (optional)</Label>
            <Textarea
              id="cl-job-description"
              rows={6}
              placeholder="Paste the job description to tailor the letter..."
              value={jobDescriptionText}
              onChange={(event) => setJobDescriptionText(event.target.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button
            onClick={handleGenerate}
            disabled={generateCoverLetter.isPending || !companyName.trim() || !roleTitle.trim()}
          >
            {generateCoverLetter.isPending ? "Generating..." : "Generate"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
