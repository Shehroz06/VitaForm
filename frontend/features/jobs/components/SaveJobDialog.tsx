"use client";

import { useRouter } from "next/navigation";
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
import { useCreateJob } from "@/features/jobs/hooks/use-jobs";
import { ApiError } from "@/services/api-client";

const MIN_RAW_TEXT_LENGTH = 50;

export function SaveJobDialog() {
  const router = useRouter();
  const createJob = useCreateJob();
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [location, setLocation] = useState("");
  const [rawText, setRawText] = useState("");

  const handleOpenChange = (next: boolean) => {
    setOpen(next);
    if (next) {
      setTitle("");
      setCompanyName("");
      setLocation("");
      setRawText("");
    }
  };

  const isTextTooShort = rawText.trim().length < MIN_RAW_TEXT_LENGTH;

  const handleSave = () => {
    if (!title.trim() || isTextTooShort) return;
    createJob.mutate(
      {
        title: title.trim(),
        raw_text: rawText.trim(),
        company_name: companyName.trim() || null,
        location: location.trim() || null,
      },
      {
        onSuccess: (job) => {
          toast.success("Job saved and analyzed.");
          setOpen(false);
          router.push(`/jobs/${job.id}`);
        },
        onError: (error) => {
          toast.error(error instanceof ApiError ? error.message : "Failed to save job.");
        },
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button>Save a job</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Save & analyze a job description</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="job-title">Job title</Label>
              <Input
                id="job-title"
                placeholder="Backend Engineer"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="job-company">Company</Label>
              <Input
                id="job-company"
                placeholder="Acme Corp"
                value={companyName}
                onChange={(event) => setCompanyName(event.target.value)}
              />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="job-location">Location</Label>
            <Input
              id="job-location"
              placeholder="Remote"
              value={location}
              onChange={(event) => setLocation(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="job-raw-text">Job description</Label>
            <Textarea
              id="job-raw-text"
              rows={8}
              placeholder="Paste the job description here..."
              value={rawText}
              onChange={(event) => setRawText(event.target.value)}
            />
            {isTextTooShort && rawText.length > 0 && (
              <p className="text-xs text-muted-foreground">
                At least {MIN_RAW_TEXT_LENGTH} characters needed.
              </p>
            )}
          </div>
        </div>
        <DialogFooter>
          <Button onClick={handleSave} disabled={createJob.isPending || !title.trim() || isTextTooShort}>
            {createJob.isPending ? "Saving..." : "Save & analyze"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
