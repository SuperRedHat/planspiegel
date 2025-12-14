import { ToastErrorTemplate } from "@app/components/Containers/ToastErrorTemplate";
import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from "axios";
import { toast } from "react-toastify";
import { auth } from "./routes/auth";
import { chat } from "./routes/chat";

const ApiClient = async (methodName = ""): Promise<AxiosInstance> => {
  const config: AxiosRequestConfig = {
    baseURL: import.meta.env.VITE_API_URL,
    withCredentials: true,
  };

  const a = axios.create(config);

  // a.interceptors.response.use(
  //   (response) => response,
  //   (error: AxiosError) => {
  //     if (error.response?.status === 401) {
  //       // toast.error('Unathorized');
  //     } else if (error.response?.status === 403) {
  //       toast.error('Forbidden');
  //     } else {
  //       toast.error(ToastErrorTemplate(methodName, error));
  //     }
  //     return Promise.reject(error);
  //   }
  // );

  a.interceptors.response.use(
    (response) => {
      // FastAPI 的 StreamingResponse 可能会导致 Axios 误报错误
      if (response.status === 200 || response.status === 201) {
        return response;
      }
      return Promise.reject(response);
    },
    (error: AxiosError) => {
      if (error.response?.status === 401) {
        // toast.error('Unauthorized');
      } else if (error.response?.status === 403) {
        toast.error('Forbidden');
      } else if (error.response?.status === 200) {
        console.warn("Ignoring false error: API returned 200 but Axios still caught an error.");
        return error.response;
      } else {
        toast.error(ToastErrorTemplate(methodName, error));
      }
      return Promise.reject(error);
    }
  );
  

  return a;
};

const API = {
  auth: auth(ApiClient),
  chat: chat(ApiClient),
};

export default API;
