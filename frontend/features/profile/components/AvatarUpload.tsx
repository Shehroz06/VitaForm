"use client";

import { Loader2, User, X } from "lucide-react";
import { useRef } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useRemoveAvatar, useUploadAvatar } from "@/features/profile/hooks/use-avatar";
import type { Profile } from "@/features/profile/types";
import { ApiError } from "@/services/api-client";

const MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024;
const ALLOWED_TYPES = new Set(["image/jpeg", "image/png", "image/webp", "image/gif"]);

export function AvatarUpload({ profile }: { profile: Profile }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const uploadAvatar = useUploadAvatar();
  const removeAvatar = useRemoveAvatar();
  const isPending = uploadAvatar.isPending || removeAvatar.isPending;

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    if (!ALLOWED_TYPES.has(file.type)) {
      toast.error("Avatar must be a JPG, PNG, WEBP, or GIF image.");
      return;
    }
    if (file.size > MAX_AVATAR_SIZE_BYTES) {
      toast.error("Avatar must be 5MB or smaller.");
      return;
    }

    uploadAvatar.mutate(file, {
      onSuccess: () => toast.success("Avatar updated."),
      onError: (error) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to upload avatar.");
      },
    });
  };

  const handleRemove = () => {
    removeAvatar.mutate(undefined, {
      onSuccess: () => toast.success("Avatar removed."),
      onError: (error) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to remove avatar.");
      },
    });
  };

  return (
    <div className="flex items-center gap-4">
      <div className="flex size-16 items-center justify-center overflow-hidden rounded-full border bg-muted">
        {profile.avatar_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={profile.avatar_url}
            alt="Avatar"
            className="size-full object-cover"
          />
        ) : (
          <User className="size-6 text-muted-foreground" />
        )}
      </div>
      <div className="flex flex-col gap-1.5">
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          className="hidden"
          onChange={handleFileChange}
        />
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={isPending}
            onClick={() => inputRef.current?.click()}
          >
            {uploadAvatar.isPending && <Loader2 className="size-4 animate-spin" />}
            {profile.avatar_url ? "Change photo" : "Upload photo"}
          </Button>
          {profile.avatar_url && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              disabled={isPending}
              onClick={handleRemove}
            >
              <X className="size-4" /> Remove
            </Button>
          )}
        </div>
        <p className="text-xs text-muted-foreground">JPG, PNG, WEBP, or GIF. Max 5MB.</p>
      </div>
    </div>
  );
}
