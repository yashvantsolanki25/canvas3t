import api from "./client";

export type User = {
  id: number;
  username: string;
  email?: string;
  created_at: string;
  updated_at: string;
};

export const registerUser = async (payload: {
  username: string;
  email?: string;
  password: string;
}) => {
  const { data } = await api.post<User>("/api/users", payload);
  return data;
};

export const loginUser = async (payload: { username: string; password: string }) => {
  const { data } = await api.post<{ token: string; user: User }>("/api/auth/login", payload);
  return data;
};

