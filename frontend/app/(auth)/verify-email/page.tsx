"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useVerifyEmail } from "@/features/auth/hooks/use-auth";
import { ApiError } from "@/services/api-client";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const verifyEmail = useVerifyEmail();
  const hasSubmitted = useRef(false);

  useEffect(() => {
    if (token && !hasSubmitted.current) {
      hasSubmitted.current = true;
      verifyEmail.mutate({ token });
    }
  }, [token, verifyEmail]);

  if (!token) {
    return (
      <>
        <CardTitle>Invalid link</CardTitle>
        <CardDescription>This verification link is missing or malformed.</CardDescription>
      </>
    );
  }

  if (verifyEmail.isPending || verifyEmail.isIdle) {
    return (
      <>
        <CardTitle>Verifying...</CardTitle>
        <CardDescription>Confirming your email address.</CardDescription>
      </>
    );
  }

  if (verifyEmail.isError) {
    const message =
      verifyEmail.error instanceof ApiError
        ? verifyEmail.error.message
        : "Failed to verify email.";
    return (
      <>
        <CardTitle>Verification failed</CardTitle>
        <CardDescription>{message}</CardDescription>
      </>
    );
  }

  return (
    <>
      <CardTitle>Email verified</CardTitle>
      <CardDescription>Your email has been verified. You can now log in.</CardDescription>
    </>
  );
}

export default function VerifyEmailPage() {
  return (
    <Card>
      <CardHeader>
        <Suspense fallback={<CardTitle>Loading...</CardTitle>}>
          <VerifyEmailContent />
        </Suspense>
      </CardHeader>
      <CardContent>
        <Link href="/login" className="text-sm underline">
          Back to login
        </Link>
      </CardContent>
    </Card>
  );
}
