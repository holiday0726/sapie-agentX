import { useMutationFunctionType } from "@/types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

interface NLToFlowRequest {
  prompt: string;
}

interface FlowNodeData {
  id: string;
  component_name: string;
  display_name: string | null;
  position: { x: number; y: number };
  data: any;
}

interface FlowEdgeData {
  source: string;
  target: string;
  source_handle: string | null;
  target_handle: string | null;
}

export interface NLToFlowResponse {
  nodes: FlowNodeData[];
  edges: FlowEdgeData[];
  explanation: string | null;
}

export const usePostNLFlow: useMutationFunctionType<
  undefined,
  NLToFlowRequest,
  NLToFlowResponse
> = (options) => {
  const { mutate } = UseRequestProcessor();

  const postNLFlowFn = async (payload: NLToFlowRequest): Promise<NLToFlowResponse> => {
    const response = await api.post<NLToFlowResponse>(
      `${getURL("NL_FLOW")}/generate`,
      payload
    );
    return response.data;
  };

  const mutation = mutate(
    ["usePostNLFlow"],
    postNLFlowFn,
    options
  );

  return mutation;
};
