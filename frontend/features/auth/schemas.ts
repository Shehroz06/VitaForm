import { z } from "zod";

const password = z
  .string()
  .min(8, "Password must be at least 8 characters long.")
  .regex(/[A-Za-z]/, "Password must contain at least one letter.")
  .regex(/\d/, "Password must contain at least one digit.");

export const registerSchema = z.object({
  email: z.email("Enter a valid email address."),
  password,
  first_name: z.string().max(100).optional(),
  last_name: z.string().max(100).optional(),
});

export const loginSchema = z.object({
  email: z.email("Enter a valid email address."),
  password: z.string().min(1, "Password is required."),
});

export const forgotPasswordSchema = z.object({
  email: z.email("Enter a valid email address."),
});

export const resetPasswordSchema = z.object({
  new_password: password,
});

export type RegisterFormValues = z.infer<typeof registerSchema>;
export type LoginFormValues = z.infer<typeof loginSchema>;
export type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;
export type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>;
