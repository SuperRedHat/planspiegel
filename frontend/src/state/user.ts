import API from "@app/api/api";
import { useQuery } from "@tanstack/react-query";

const fetchClaims = async () => {
  try {
    const res = await API.auth.claims();
    if (res.status !== 200) throw new Error("Non-200 response");
    return res.data;
  } catch (err) {
    console.log("Ignoring false error:", err);
    return null; // 这里返回 null 而不是抛出错误，避免前端误认为失败
  }
};

export const useUserClaimsQuery = () => {
  return useQuery({
    queryKey: ["userClaims"],
    queryFn: () => fetchClaims(),
    // staleTime: 0,
    retry: false,
  });
};
