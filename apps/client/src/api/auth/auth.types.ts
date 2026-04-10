import { ENDPOINTS } from "@/config/endpoints";

export const LOGIN_PATH = ENDPOINTS.AUTH.LOGIN;

export type AuthCredentials = { email: string, password: string }

export const REQUIRED_CREDENTIALS = {
  email: { label: "Email", type: "email" },
  password: { label: "Password", type: "password" }
}
