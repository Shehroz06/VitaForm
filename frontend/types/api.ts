export interface SuccessResponse<T> {
  success: true;
  message: string;
  data: T;
  meta: Record<string, unknown>;
}

export interface ErrorDetail {
  field?: string;
  message: string;
}

export interface ErrorResponse {
  success: false;
  message: string;
  errors: ErrorDetail[];
}

export type ApiResponse<T> = SuccessResponse<T> | ErrorResponse;
