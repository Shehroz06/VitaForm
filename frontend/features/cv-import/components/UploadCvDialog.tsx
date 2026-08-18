"use client";

import { Upload } from "lucide-react";
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
import { useUploadCv } from "@/features/cv-import/hooks/use-cv-import";
import { ApiError } from "@/services/api-client";

export function UploadCvDialog({
  triggerLabel = "Import data",
  description = "Upload a PDF of your existing resume. We'll extract what we can find and let you review everything before anything is added to your profile — nothing is invented and nothing is saved automatically.",
}: {
  triggerLabel?: string;
  description?: string;
} = {}) {
  const router = useRouter();
  const uploadCv = useUploadCv();
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  const handleOpenChange = (next: boolean) => {
    setOpen(next);
    if (next) setFile(null);
  };

  const handleUpload = () => {
    if (!file) return;
    uploadCv.mutate(file, {
      onSuccess: (session) => {
        toast.success("Resume parsed. Review the proposed data before confirming.");
        setOpen(false);
        router.push(`/cv-import/${session.id}`);
      },
      onError: (error) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to parse resume.");
      },
    });
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button>
          <Upload className="size-4" /> {triggerLabel}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Import your resume</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">{description}</p>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="cv-file">PDF file</Label>
            <Input
              id="cv-file"
              type="file"
              accept="application/pdf"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button onClick={handleUpload} disabled={uploadCv.isPending || !file}>
            {uploadCv.isPending ? "Parsing..." : "Upload & parse"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
