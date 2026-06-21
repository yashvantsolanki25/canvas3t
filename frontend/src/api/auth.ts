import api from "./client";

export type User = {
  id: number;
  username: string;
  email?: string;
  created_at: string;
  updated_at: string;
};

export type AuthResponse = {
  token: string;
  user: User;
  message?: string;
};

export const registerUser = async (payload: {
  username: string;
  email?: string;
  password: string;
}): Promise<AuthResponse> => {
  // Use /api/auth/register — returns { token, user } in one shot,
  // same shape as loginUser so the store can handle both identically.
  const { data } = await api.post<AuthResponse>("/api/auth/register", payload);
  return data;
};

export const loginUser = async (payload: {
  username: string;
  password: string;
}): Promise<AuthResponse> => {
  const { data } = await api.post<AuthResponse>("/api/auth/login", payload);
  return data;
};

