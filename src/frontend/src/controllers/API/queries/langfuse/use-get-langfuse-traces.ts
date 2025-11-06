import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

interface TraceItem {
  id: string;
  name: string | null;
  timestamp: string;
  input: Record<string, any> | null;
  output: Record<string, any> | null;
  total_cost: number | null;
  metadata: Record<string, any> | null;
}

interface TracesResponse {
  traces: TraceItem[];
  total: number;
  has_more: boolean;
}

interface UseGetLangfuseTracesParams {
  limit?: number;
  offset?: number;
  enabled?: boolean;
}

export const useGetLangfuseTraces = ({
  limit = 10,
  offset = 0,
  enabled = true,
}: UseGetLangfuseTracesParams = {}) => {
  const { query } = UseRequestProcessor();

  const getLangfuseTracesFn = async (): Promise<TracesResponse> => {
    const response = await api.get<TracesResponse>(
      `${getURL("LANGFUSE")}/traces`,
      {
        params: { limit, offset },
      }
    );
    return response.data;
  };

  return query(["langfuse-traces", limit, offset], getLangfuseTracesFn, {
    enabled,
  });
};
