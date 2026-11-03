import { apiRequest } from "./client";

export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
}

export function registerUser(payload: RegisterRequest): Promise<User> {
  return apiRequest<User>("/api/v1/auth/register", {
    method: "POST",
    jsonBody: payload,
  });
}

export function loginUser(payload: LoginRequest): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    jsonBody: payload,
  });
}

export function getCurrentUser(
  token: string,
  onUnauthorized?: () => void,
): Promise<User> {
  return apiRequest<User>("/api/v1/auth/me", {
    token,
    onUnauthorized,
  });
}
