"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AvatarUpload } from "@/features/profile/components/AvatarUpload";
import { useUpdateProfile } from "@/features/profile/hooks/use-profile";
import { type ProfileBasicsFormValues, profileBasicsSchema } from "@/features/profile/schemas";
import type { Profile } from "@/features/profile/types";
import { useUpdateMe } from "@/features/auth/hooks/use-auth";
import type { User } from "@/features/auth/types";
import { ApiError } from "@/services/api-client";

export function ProfileBasicsForm({ profile, user }: { profile: Profile; user: User }) {
  const updateProfile = useUpdateProfile();
  const updateMe = useUpdateMe();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<ProfileBasicsFormValues>({
    resolver: zodResolver(profileBasicsSchema),
    defaultValues: toFormValues(profile, user),
  });

  useEffect(() => {
    reset(toFormValues(profile, user));
  }, [profile, user, reset]);

  const onSubmit = (values: ProfileBasicsFormValues) => {
    const { first_name, last_name, ...profileValues } = values;
    const profilePayload = Object.fromEntries(
      Object.entries(profileValues).map(([key, value]) => [key, value === "" ? null : value]),
    );

    Promise.all([
      updateMe.mutateAsync({
        first_name: first_name || null,
        last_name: last_name || null,
      }),
      updateProfile.mutateAsync(profilePayload),
    ])
      .then(() => toast.success("Profile updated."))
      .catch((error: unknown) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to update profile.");
      });
  };

  const isPending = updateProfile.isPending || updateMe.isPending;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <AvatarUpload profile={profile} />

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="first_name">First name</Label>
          <Input id="first_name" {...register("first_name")} />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="last_name">Last name</Label>
          <Input id="last_name" {...register("last_name")} />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="email">Email</Label>
          <Input id="email" value={user.email} disabled readOnly />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="phone">Phone</Label>
          <Input id="phone" {...register("phone")} />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="location">Location</Label>
          <Input id="location" placeholder="Remote" {...register("location")} />
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

      <Button type="submit" disabled={!isDirty || isPending} className="self-start">
        {isPending ? "Saving..." : "Save changes"}
      </Button>
    </form>
  );
}

function toFormValues(profile: Profile, user: User): ProfileBasicsFormValues {
  return {
    first_name: user.first_name ?? "",
    last_name: user.last_name ?? "",
    phone: profile.phone ?? "",
    location: profile.location ?? "",
    website_url: profile.website_url ?? "",
    github_url: profile.github_url ?? "",
    linkedin_url: profile.linkedin_url ?? "",
  };
}
