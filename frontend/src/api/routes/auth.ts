import { ILoginData } from "@app/interfaces/user";
import { AxiosInstance } from "axios";

export const auth = (
  ApiClient: (methodName?: string) => Promise<AxiosInstance>
) => {
  return {
    claims: async () =>
      (await ApiClient("Check user claims")).get(`/auth/claims`),

    login: async (data: ILoginData) =>
      (await ApiClient("Login user")).post(`/auth/login`, data),

    register: async (data: ILoginData) =>
      (await ApiClient("Register user")).post(`/auth/register`, data),

    logout: async () => (await ApiClient("Logout")).post(`/auth/logout`),

    setCookie: async (token: string) =>
      (await ApiClient("Set auth cookie")).post(`/auth/google-set-cookie`, {
        token,
      }),
  };
};
