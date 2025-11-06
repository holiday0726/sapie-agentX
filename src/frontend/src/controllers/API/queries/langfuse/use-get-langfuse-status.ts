import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

interface LangfuseStatus {
  connected: boolean;
  host: string | null;
  error: string | null;
}

export const useGetLangfuseStatus = () => {
  const { query } = UseRequestProcessor();

  const getLangfuseStatusFn = async (): Promise<LangfuseStatus> => {
    const response = await api.get<LangfuseStatus>(
      `${getURL("LANGFUSE")}/status`
    );
    return response.data;
  };

  return query(["langfuse-status"], getLangfuseStatusFn, {
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};
