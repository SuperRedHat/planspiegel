import { AxiosInstance } from "axios";

export const chat = (
  ApiClient: (methodName?: string) => Promise<AxiosInstance>
) => {
  return {
    getList: async () =>
      (await ApiClient("Get checkups")).get(`/checkups`),

    startCheckup: async (url: string) =>
      (await ApiClient("Start new checkup")).post(`/checkups`, { url }),

    getCheckup: async (checkup_id: string) =>
      (await ApiClient("Get chekup")).get(`/checkups/${checkup_id}`),

    getMessageHistory: async (checkup_id: string, check_id: string, chat_id: string) =>
      (await ApiClient("Get messages")).get(`/checkups/${checkup_id}/checks/${check_id}/chats/${chat_id}/messages`),

    getReportPdf: async (checkup_id: string): Promise<Blob> =>
      (await ApiClient("Get pdf report")).get(`/checkups/${checkup_id}/pdf_report`, { responseType: 'blob', headers: { 'Accept': 'application/pdf' } }),  };
};
