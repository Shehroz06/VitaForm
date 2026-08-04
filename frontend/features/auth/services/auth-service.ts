import { apiClient } from "@/services/api-client";
import type {
  ForgotPasswordPayload,
  LoginPayload,
  RegisterPayload,
  ResetPasswordPayload,
  TokenResponse,
  User,
  VerifyEmailPayload,
} from "@/features/auth/types";

export const authService = {
  register: (payload: RegisterPayload) => apiClient.post<User>("/auth/register", payload),
  login: (payload: LoginPayload) => apiClient.post<TokenResponse>("/auth/login", payload),
  logout: (refreshToken: string) =>
    apiClient.post<{ message: string }>("/auth/logout", { refresh_token: refreshToken }),
  verifyEmail: (payload: VerifyEmailPayload) =>
    apiClient.post<User>("/auth/verify-email", payload),
  forgotPassword: (payload: ForgotPasswordPayload) =>
    apiClient.post<{ message: string }>("/auth/forgot-password", payload),
  resetPassword: (payload: ResetPasswordPayload) =>
    apiClient.post<{ message: string }>("/auth/reset-password", payload),
  getCurrentUser: () => apiClient.get<User>("/auth/me"),
};
