import type { NextConfig } from "next";

// Resolved at build/server time (same env var the API client itself reads),
// so the CSP always allows exactly the backend this build actually talks to.
const apiOrigin = new URL(process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1")
  .origin;

// 'unsafe-inline' on script-src is a deliberate, pragmatic gap: the Next.js
// App Router emits inline bootstrap/streaming scripts (e.g. the RSC
// `self.__next_f.push(...)` payload) with no built-in nonce wiring, so a
// strict script-src without it breaks hydration. This still blocks the
// things a CSP is most useful for here -- loading a remote attacker-hosted
// script, framing the app, and exfiltrating via fetch/XHR to an arbitrary
// origin (connect-src is locked to self + the API). style-src needs
// 'unsafe-inline' too: Radix UI primitives (Dialog/Popover/DropdownMenu)
// position themselves via inline `style` attributes set from JS.
//
// 'unsafe-eval' is dev-only: React's Fast Refresh uses eval() in
// development to reconstruct stack traces across module boundaries (a
// browser console warning confirmed this breaks hot reload without it).
// Production React never calls eval(), so it's deliberately left out of
// the policy actually shipped to users.
const isDev = process.env.NODE_ENV !== "production";
const contentSecurityPolicy = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' blob: data:",
  "font-src 'self' data:",
  `connect-src 'self' ${apiOrigin}`,
  "object-src 'none'",
  "base-uri 'self'",
  "frame-ancestors 'none'",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: contentSecurityPolicy },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
];

const nextConfig: NextConfig = {
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
