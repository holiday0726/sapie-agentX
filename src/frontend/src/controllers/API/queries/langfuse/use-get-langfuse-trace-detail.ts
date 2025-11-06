import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

interface TraceDetail {
  id: string;
  name: string | null;
  timestamp: string;
  input: Record<string, any> | null;
  output: Record<string, any> | null;
  total_cost: number | null;
  metadata: Record<string, any> | null;
  user_id: string | null;
  session_id: string | null;
}

interface UseGetLangfuseTraceDetailParams {
  traceId: string;
  enabled?: boolean;
}

export const useGetLangfuseTraceDetail = ({
  traceId,
  enabled = true,
}: UseGetLangfuseTraceDetailParams) => {
  const { query } = UseRequestProcessor();

  const getLangfuseTraceDetailFn = async (): Promise<TraceDetail> => {
    const response = await api.get<TraceDetail>(
      `${getURL("LANGFUSE")}/traces/${traceId}`
    );
    return response.data;
  };

  return query(["langfuse-trace-detail", traceId], getLangfuseTraceDetailFn, {
    enabled: enabled && !!traceId,
  });
};
