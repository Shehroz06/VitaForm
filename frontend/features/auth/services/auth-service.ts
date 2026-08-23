import { apiClient } from "@/services/api-client";
import type {
  AccessTokenResponse,
  ForgotPasswordPayload,
  LoginPayload,
  RegisterPayload,
  ResetPasswordPayload,
  UpdateMePayload,
  User,
  VerifyEmailPayload,
} from "@/features/auth/types";

export const authService = {
  register: (payload: RegisterPayload) => apiClient.post<User>("/auth/register", payload),
  login: (payload: LoginPayload) => apiClient.post<AccessTokenResponse>("/auth/login", payload),
  // No refresh token to send -- the server reads it from the HttpOnly
  // cookie the browser attaches automatically.
  logout: () => apiClient.post<{ message: string }>("/auth/logout"),
  verifyEmail: (payload: VerifyEmailPayload) =>
    apiClient.post<User>("/auth/verify-email", payload),
  forgotPassword: (payload: ForgotPasswordPayload) =>
    apiClient.post<{ message: string }>("/auth/forgot-password", payload),
  resetPassword: (payload: ResetPasswordPayload) =>
    apiClient.post<{ message: string }>("/auth/reset-password", payload),
  getCurrentUser: () => apiClient.get<User>("/auth/me"),
  updateMe: (payload: UpdateMePayload) => apiClient.patch<User>("/auth/me", payload),
};
