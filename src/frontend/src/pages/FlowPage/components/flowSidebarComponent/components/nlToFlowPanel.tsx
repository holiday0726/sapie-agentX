import { useState } from "react";
import ForwardedIconComponent from "@/components/common/genericIconComponent";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  SidebarGroup,
  SidebarGroupContent,
} from "@/components/ui/sidebar";
import { usePostNLFlow } from "@/controllers/API/queries/flows/use-post-nl-flow";
import { useTypesStore } from "@/stores/typesStore";
import useFlowStore from "@/stores/flowStore";
import useAlertStore from "@/stores/alertStore";
import type { APIClassType, InputFieldType } from "@/types/api";
import { scapedJSONStringfy } from "@/utils/reactflowUtils";
import type { sourceHandleType, targetHandleType } from "@/types/flow";

// Helper function to find the first output from a component
function findComponentOutput(componentData: APIClassType): { name: string; types: string[] } | null {
  if (!componentData.outputs || componentData.outputs.length === 0) {
    // Fallback to output_types if no outputs array
    if (componentData.output_types && componentData.output_types.length > 0) {
      return {
        name: "output",
        types: componentData.output_types,
      };
    }
    return null;
  }

  // Get first non-hidden output
  const output = componentData.outputs.find(o => !o.hidden) || componentData.outputs[0];
  return {
    name: output.name,
    types: output.types,
  };
}

// Helper function to find compatible input field from component template
function findCompatibleInput(
  componentData: APIClassType,
  sourceOutputTypes: string[]
): { fieldName: string; inputTypes: string[] } | null {
  const template = componentData.template;
  if (!template) return null;

  // Find first input field that accepts the source output types
  for (const [fieldName, field] of Object.entries(template)) {
    const fieldTyped = field as InputFieldType;

    // Skip if not an input field or if it's advanced/hidden
    if (fieldTyped.advanced === true || fieldTyped.show === false) continue;

    const inputTypes = fieldTyped.input_types || [];
    if (inputTypes.length === 0) continue;

    // Check if any source output type is compatible with this input
    const isCompatible = sourceOutputTypes.some(outputType =>
      inputTypes.includes(outputType)
    );

    if (isCompatible) {
      return { fieldName, inputTypes };
    }
  }

  // No compatible input found - return first available input as fallback
  for (const [fieldName, field] of Object.entries(template)) {
    const fieldTyped = field as InputFieldType;
    if (fieldTyped.input_types && fieldTyped.input_types.length > 0) {
      return { fieldName, inputTypes: fieldTyped.input_types };
    }
  }

  return null;
}

export default function NlToFlowPanel() {
  const [prompt, setPrompt] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  const data = useTypesStore((state) => state.data);
  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);
  const nodes = useFlowStore((state) => state.nodes);
  const edges = useFlowStore((state) => state.edges);
  const setNodes = useFlowStore((state) => state.setNodes);
  const setEdges = useFlowStore((state) => state.setEdges);

  const { mutate: generateFlow } = usePostNLFlow();

  const handleGenerate = () => {
    if (!prompt.trim()) return;

    setIsGenerating(true);

    generateFlow(
      { prompt: prompt.trim() },
      {
        onSuccess: (response) => {
          try {
            console.log("🔵 [NL-Flow] Backend response:", response);

            // Create ID mapping: backend ID -> frontend ID
            const idMapping: Record<string, string> = {};

            // Convert backend response to React Flow format
            const newNodes = response.nodes.map((node, index) => {
              console.log(`🔵 [NL-Flow] Processing node ${index}:`, node);

              // Find component in types store
              let componentData: APIClassType | undefined;
              for (const category in data) {
                if (data[category][node.component_name]) {
                  componentData = data[category][node.component_name];
                  console.log(`🔵 [NL-Flow] Found component ${node.component_name} in category ${category}`);
                  break;
                }
              }

              if (!componentData) {
                console.error(`❌ [NL-Flow] Component ${node.component_name} not found`);
                throw new Error(`Component ${node.component_name} not found`);
              }

              const nodeConfig = node.data?.config || {};

              // Generate new unique ID for frontend
              const newId = `${node.component_name}-${Date.now()}-${index}`;

              // Map backend ID (from LLM) to frontend ID
              idMapping[node.id] = newId;
              console.log(`🔵 [NL-Flow] ID mapping: ${node.id} -> ${newId}`);

              const reactFlowNode = {
                id: newId,
                type: "genericNode",
                position: node.position,
                data: {
                  type: node.component_name,
                  node: {
                    ...componentData,
                    template: {
                      ...(componentData.template || {}),
                      ...(nodeConfig || {}),
                    },
                  },
                  id: newId,
                },
              };

              console.log(`🔵 [NL-Flow] Created React Flow node:`, reactFlowNode);
              return reactFlowNode;
            });

            console.log("🔵 [NL-Flow] All nodes created:", newNodes.length);
            console.log("🔵 [NL-Flow] ID mapping:", idMapping);

            // Create node lookup for edge processing
            const nodeMap = new Map(newNodes.map(n => [n.id, n]));

            // Map edge source/target to new IDs and generate proper handles
            const newEdges = response.edges.map((edge, index) => {
              console.log(`🔵 [NL-Flow] Processing edge ${index}:`, edge);

              const mappedSource = idMapping[edge.source];
              const mappedTarget = idMapping[edge.target];

              console.log(`🔵 [NL-Flow] Edge mapping: ${edge.source} -> ${mappedSource}, ${edge.target} -> ${mappedTarget}`);

              if (!mappedSource || !mappedTarget) {
                console.warn(`⚠️ [NL-Flow] Invalid edge - missing source or target`);
                return null;
              }

              // Get source and target nodes
              const sourceNode = nodeMap.get(mappedSource);
              const targetNode = nodeMap.get(mappedTarget);

              if (!sourceNode || !targetNode) {
                console.warn(`⚠️ [NL-Flow] Node not found for edge`);
                return null;
              }

              // Find output from source component
              const sourceComponentData = sourceNode.data.node as APIClassType;
              const sourceOutput = findComponentOutput(sourceComponentData);

              if (!sourceOutput) {
                console.warn(`⚠️ [NL-Flow] No output found for source ${sourceNode.data.type}`);
                return null;
              }

              console.log(`🔵 [NL-Flow] Source output:`, sourceOutput);

              // Find compatible input in target component
              const targetComponentData = targetNode.data.node as APIClassType;
              const targetInput = findCompatibleInput(targetComponentData, sourceOutput.types);

              if (!targetInput) {
                console.warn(`⚠️ [NL-Flow] No compatible input found for target ${targetNode.data.type}`);
                return null;
              }

              console.log(`🔵 [NL-Flow] Target input:`, targetInput);

              // Create sourceHandle object matching cleanEdges expectations
              const sourceHandleObj: sourceHandleType = {
                dataType: sourceNode.data.type,  // Use data.type directly, not display_name
                id: mappedSource,
                output_types: sourceOutput.types,
                name: sourceOutput.name,
              };

              // Create targetHandle object matching cleanEdges expectations
              const targetHandleObj: targetHandleType = {
                type: targetComponentData.template[targetInput.fieldName]?.type,  // Use template field type
                fieldName: targetInput.fieldName,
                id: mappedTarget,
                inputTypes: targetInput.inputTypes,
              };

              // Format handles using scapedJSONStringfy
              const sourceHandle = scapedJSONStringfy(sourceHandleObj);
              const targetHandle = scapedJSONStringfy(targetHandleObj);

              console.log(`🔵 [NL-Flow] Generated handles:`, {
                sourceHandle,
                targetHandle,
              });

              const reactFlowEdge = {
                id: `edge-${Date.now()}-${index}`,
                source: mappedSource,
                target: mappedTarget,
                sourceHandle,
                targetHandle,
                type: "default",
                data: {
                  sourceHandle: sourceHandleObj,
                  targetHandle: targetHandleObj,
                },
              };

              console.log(`🔵 [NL-Flow] Created React Flow edge:`, reactFlowEdge);
              return reactFlowEdge;
            }).filter((edge): edge is NonNullable<typeof edge> => edge !== null);

            console.log("🔵 [NL-Flow] All edges created:", newEdges.length);
            console.log("🔵 [NL-Flow] Nodes:", newNodes);
            console.log("🔵 [NL-Flow] Edges:", newEdges);

            // Add nodes and edges directly to store
            // Note: We don't use paste() because it generates new IDs which breaks our edge references
            console.log("🔵 [NL-Flow] Adding nodes and edges to flow...");
            setNodes([...nodes, ...newNodes.map(n => ({ ...n, selected: true }))] as any);
            setEdges([...edges, ...newEdges] as any);
            console.log("✅ [NL-Flow] Nodes and edges added to flow");

            setSuccessData({
              title: response.explanation
                ? `${response.explanation}\n\n✅ ${newNodes.length}개의 노드와 ${newEdges.length}개의 연결이 생성되었습니다.`
                : `플로우가 생성되었습니다! ${newNodes.length}개의 노드와 ${newEdges.length}개의 연결이 추가되었습니다.`,
            });

            setPrompt(""); // Clear prompt after success
          } catch (error) {
            console.error("❌ [NL-Flow] Error processing flow response:", error);
            console.error("❌ [NL-Flow] Error stack:", (error as Error).stack);
            setErrorData({
              title: "Error creating flow",
              list: [(error as Error).message],
            });
          } finally {
            setIsGenerating(false);
          }
        },
        onError: (error: any) => {
          console.error("❌ [NL-Flow] Error generating flow:", error);
          setErrorData({
            title: "Failed to generate flow",
            list: [
              error?.response?.data?.detail ||
              "Could not generate flow. Please check if OPENAI_API_KEY is set and try again.",
            ],
          });
          setIsGenerating(false);
        },
      }
    );
  };

  return (
    <div className="flex flex-col h-full">
      <SidebarGroup>
        <SidebarGroupContent>
          <div className="flex flex-col gap-4 px-3 py-4">
            {/* Title and Description */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <ForwardedIconComponent name="sparkles" className="h-4 w-4" />
                <span>AI Flow Builder</span>
              </div>
              <div className="text-xs text-muted-foreground">
                자연어를 플로우로 생성합니다.
              </div>
            </div>

            {/* Input Area */}
            <div className="flex flex-col gap-2">
              <label className="text-xs font-medium">
                플로우 설명
              </label>
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="예: '사용자 질문에 답변하는 챗봇을 만들어주세요...'"
                className="min-h-[120px] resize-none text-sm"
                disabled={isGenerating}
              />
            </div>

            {/* Generate Button */}
            <Button
              onClick={handleGenerate}
              disabled={!prompt.trim() || isGenerating}
              className="w-full"
            >
              {isGenerating ? (
                <>
                  <ForwardedIconComponent
                    name="loader-circle"
                    className="h-4 w-4 mr-2 animate-spin"
                  />
                  생성 중...
                </>
              ) : (
                <>
                  <ForwardedIconComponent
                    name="sparkles"
                    className="h-4 w-4 mr-2"
                  />
                  플로우 생성
                </>
              )}
            </Button>
          </div>
        </SidebarGroupContent>
      </SidebarGroup>
    </div>
  );
}

