"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { AvatarUpload } from "@/features/profile/components/AvatarUpload";
import { useUpdateProfile } from "@/features/profile/hooks/use-profile";
import { type ProfileBasicsFormValues, profileBasicsSchema } from "@/features/profile/schemas";
import type { Profile } from "@/features/profile/types";
import { ApiError } from "@/services/api-client";

export function ProfileBasicsForm({ profile }: { profile: Profile }) {
  const updateProfile = useUpdateProfile();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<ProfileBasicsFormValues>({
    resolver: zodResolver(profileBasicsSchema),
    defaultValues: toFormValues(profile),
  });

  useEffect(() => {
    reset(toFormValues(profile));
  }, [profile, reset]);

  const onSubmit = (values: ProfileBasicsFormValues) => {
    const payload = Object.fromEntries(
      Object.entries(values).map(([key, value]) => [key, value === "" ? null : value]),
    );
    updateProfile.mutate(payload, {
      onSuccess: () => toast.success("Profile updated."),
      onError: (error) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to update profile.");
      },
    });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <AvatarUpload profile={profile} />
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="headline">Headline</Label>
          <Input id="headline" placeholder="Software Engineer" {...register("headline")} />
          {errors.headline && (
            <p className="text-sm text-destructive">{errors.headline.message}</p>
          )}
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="location">Location</Label>
          <Input id="location" placeholder="Remote" {...register("location")} />
        </div>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="bio">Bio</Label>
        <Textarea id="bio" rows={3} {...register("bio")} />
        {errors.bio && <p className="text-sm text-destructive">{errors.bio.message}</p>}
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="phone">Phone</Label>
          <Input id="phone" {...register("phone")} />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="website_url">Website</Label>
          <Input id="website_url" placeholder="https://" {...register("website_url")} />
          {errors.website_url && (
            <p className="text-sm text-destructive">{errors.website_url.message}</p>
          )}
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="github_url">GitHub</Label>
          <Input id="github_url" placeholder="https://github.com/…" {...register("github_url")} />
          {errors.github_url && (
            <p className="text-sm text-destructive">{errors.github_url.message}</p>
          )}
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="linkedin_url">LinkedIn</Label>
          <Input
            id="linkedin_url"
            placeholder="https://linkedin.com/in/…"
            {...register("linkedin_url")}
          />
          {errors.linkedin_url && (
            <p className="text-sm text-destructive">{errors.linkedin_url.message}</p>
          )}
        </div>
      </div>
      <Button type="submit" disabled={!isDirty || updateProfile.isPending} className="self-start">
        {updateProfile.isPending ? "Saving..." : "Save changes"}
      </Button>
    </form>
  );
}

function toFormValues(profile: Profile): ProfileBasicsFormValues {
  return {
    headline: profile.headline ?? "",
    bio: profile.bio ?? "",
    phone: profile.phone ?? "",
    location: profile.location ?? "",
    website_url: profile.website_url ?? "",
    github_url: profile.github_url ?? "",
    linkedin_url: profile.linkedin_url ?? "",
  };
}
