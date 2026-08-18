"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Paperclip, Pencil, Plus, Trash2, X } from "lucide-react";
import { useRef, useState } from "react";
import { useForm } from "react-hook-form";
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
import {
  useCertificationList,
  useCreateCertification,
  useDeleteCertification,
  useRemoveCertificationAttachment,
  useUpdateCertification,
  useUploadCertificationAttachment,
} from "@/features/profile/hooks/use-certifications";
import { type CertificationFormValues, certificationSchema } from "@/features/profile/schemas";
import type { Certification } from "@/features/profile/types";
import { ApiError } from "@/services/api-client";

const MAX_ATTACHMENT_SIZE_BYTES = 10 * 1024 * 1024;
const ALLOWED_ATTACHMENT_TYPES = new Set(["image/jpeg", "image/png", "application/pdf"]);

const emptyValues: CertificationFormValues = {
  name: "",
  issuing_organization: "",
  issue_date: "",
  expiration_date: "",
  credential_id: "",
  credential_url: "",
};

export function CertificationsSection() {
  const { data: items, isLoading, isError } = useCertificationList();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Certification | null>(null);

  const openCreate = () => {
    setEditing(null);
    setOpen(true);
  };
  const openEdit = (item: Certification) => {
    setEditing(item);
    setOpen(true);
  };

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Certifications</h2>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm" onClick={openCreate}>
              <Plus className="size-4" /> Add
            </Button>
          </DialogTrigger>
          <CertificationDialogContent editing={editing} onDone={() => setOpen(false)} />
        </Dialog>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading certifications...</p>}
      {isError && <p className="text-sm text-destructive">Failed to load certifications.</p>}
      {items && items.length === 0 && (
        <p className="text-sm text-muted-foreground">No certifications added yet.</p>
      )}

      <div className="flex flex-col gap-2">
        {items?.map((item) => (
          <CertificationCard key={item.id} item={item} onEdit={() => openEdit(item)} />
        ))}
      </div>
    </section>
  );
}

function CertificationCard({ item, onEdit }: { item: Certification; onEdit: () => void }) {
  const deleteCertification = useDeleteCertification();

  const handleDelete = () => {
    if (!window.confirm(`Delete "${item.name}"?`)) return;
    deleteCertification.mutate(item.id, { onError: () => toast.error("Failed to delete.") });
  };

  return (
    <div className="flex flex-col gap-2 rounded-xl bg-card p-3.5 ring-1 ring-foreground/10 transition-colors hover:bg-muted/40">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-medium">{item.name}</p>
          <p className="text-sm text-muted-foreground">{item.issuing_organization}</p>
          <p className="text-xs text-muted-foreground">
            {[item.issue_date, item.expiration_date && `expires ${item.expiration_date}`]
              .filter(Boolean)
              .join(" · ")}
          </p>
        </div>
        <div className="flex gap-1">
          <Button variant="ghost" size="icon" onClick={onEdit} aria-label="Edit">
            <Pencil className="size-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={handleDelete} aria-label="Delete">
            <Trash2 className="size-4" />
          </Button>
        </div>
      </div>
      <CertificationAttachment item={item} />
    </div>
  );
}

function CertificationAttachment({ item }: { item: Certification }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const uploadAttachment = useUploadCertificationAttachment();
  const removeAttachment = useRemoveCertificationAttachment();
  const isPending = uploadAttachment.isPending || removeAttachment.isPending;

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    if (!ALLOWED_ATTACHMENT_TYPES.has(file.type)) {
      toast.error("Attachment must be a JPG, PNG, or PDF file.");
      return;
    }
    if (file.size > MAX_ATTACHMENT_SIZE_BYTES) {
      toast.error("Attachment must be 10MB or smaller.");
      return;
    }

    uploadAttachment.mutate(
      { id: item.id, file },
      {
        onSuccess: () => toast.success("Attachment uploaded."),
        onError: (error) => {
          toast.error(error instanceof ApiError ? error.message : "Failed to upload attachment.");
        },
      },
    );
  };

  const handleRemove = () => {
    removeAttachment.mutate(item.id, {
      onSuccess: () => toast.success("Attachment removed."),
      onError: () => toast.error("Failed to remove attachment."),
    });
  };

  return (
    <div className="flex items-center gap-2 text-sm">
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,application/pdf"
        className="hidden"
        onChange={handleFileChange}
      />
      {item.file_id ? (
        <>
          <Paperclip className="size-4 text-muted-foreground" />
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/files/${item.file_id}`}
            target="_blank"
            rel="noreferrer"
            className="text-primary underline"
          >
            View attachment
          </a>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="size-6"
            disabled={isPending}
            onClick={handleRemove}
            aria-label="Remove attachment"
          >
            {removeAttachment.isPending ? (
              <Loader2 className="size-3 animate-spin" />
            ) : (
              <X className="size-3" />
            )}
          </Button>
        </>
      ) : (
        <Button
          type="button"
          variant="link"
          size="sm"
          className="h-auto p-0"
          disabled={isPending}
          onClick={() => inputRef.current?.click()}
        >
          {uploadAttachment.isPending ? (
            <Loader2 className="size-3 animate-spin" />
          ) : (
            <Paperclip className="size-3" />
          )}
          Attach credential file
        </Button>
      )}
    </div>
  );
}

function CertificationDialogContent({
  editing,
  onDone,
}: {
  editing: Certification | null;
  onDone: () => void;
}) {
  const createCertification = useCreateCertification();
  const updateCertification = useUpdateCertification();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CertificationFormValues>({
    resolver: zodResolver(certificationSchema),
    values: editing ? toFormValues(editing) : emptyValues,
  });
  const isPending = createCertification.isPending || updateCertification.isPending;

  const onSubmit = (values: CertificationFormValues) => {
    const payload = {
      ...values,
      issue_date: values.issue_date || null,
      expiration_date: values.expiration_date || null,
      credential_id: values.credential_id || null,
      credential_url: values.credential_url || null,
    };

    const mutation = editing
      ? updateCertification.mutateAsync({ id: editing.id, payload })
      : createCertification.mutateAsync(payload);

    mutation
      .then(() => {
        toast.success(editing ? "Certification updated." : "Certification added.");
        onDone();
      })
      .catch((error: unknown) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to save.");
      });
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{editing ? "Edit certification" : "Add certification"}</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="name">Name</Label>
          <Input id="name" {...register("name")} />
          {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="issuing_organization">Issuing organization</Label>
          <Input id="issuing_organization" {...register("issuing_organization")} />
          {errors.issuing_organization && (
            <p className="text-sm text-destructive">{errors.issuing_organization.message}</p>
          )}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="issue_date">Issue date</Label>
            <Input id="issue_date" type="date" {...register("issue_date")} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="expiration_date">Expiration date</Label>
            <Input id="expiration_date" type="date" {...register("expiration_date")} />
            {errors.expiration_date && (
              <p className="text-sm text-destructive">{errors.expiration_date.message}</p>
            )}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="credential_id">Credential ID</Label>
            <Input id="credential_id" {...register("credential_id")} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="credential_url">Credential URL</Label>
            <Input id="credential_url" placeholder="https://" {...register("credential_url")} />
            {errors.credential_url && (
              <p className="text-sm text-destructive">{errors.credential_url.message}</p>
            )}
          </div>
        </div>
        <DialogFooter>
          <Button type="submit" disabled={isPending}>
            {isPending ? "Saving..." : "Save"}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}

function toFormValues(item: Certification): CertificationFormValues {
  return {
    name: item.name,
    issuing_organization: item.issuing_organization,
    issue_date: item.issue_date ?? "",
    expiration_date: item.expiration_date ?? "",
    credential_id: item.credential_id ?? "",
    credential_url: item.credential_url ?? "",
  };
}
