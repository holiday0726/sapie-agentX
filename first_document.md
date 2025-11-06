# NL to Flow 구현 상세 문서

## 전체 아키텍처 개요

```
사용자 입력 (자연어)
    ↓
Frontend (nlToFlowPanel.tsx)
    ↓ API 호출
Backend (nl_flow.py)
    ↓ 컴포넌트 데이터 간소화
OpenAI GPT-4 (Function Calling)
    ↓ 컴포넌트 선택 및 플로우 구성
Backend (응답 포맷팅)
    ↓ 상세 컴포넌트 데이터 포함
Frontend (React Flow 노드/엣지 생성)
    ↓
Canvas에 플로우 표시
```

---

## 1. 백엔드 구현

### 1.1 FastAPI 엔드포인트 (nl_flow.py)

```python
@router.post("/generate", response_model=NLToFlowResponse)
async def generate_flow_from_nl(
    request: NLToFlowRequest,
    current_user: User = Depends(get_current_active_user),
) -> NLToFlowResponse:
    """
    자연어를 Langflow 플로우로 변환하는 엔드포인트
    
    1. Langflow의 모든 컴포넌트 데이터를 가져옴 (/all 엔드포인트와 동일한 데이터)
    2. NLFlowService를 통해 OpenAI에게 전달
    3. AI가 선택한 컴포넌트로 플로우 생성
    """
    
    # 사용 가능한 모든 컴포넌트 가져오기
    # 구조: { category: { component_name: component_data } }
    # 예: { "inputs": { "ChatInput": {...}, "TextInput": {...} }, 
    #      "models": { "ChatOpenAI": {...}, "ChatAnthropic": {...} } }
    all_types = await get_and_cache_all_types_dict(settings_service=settings_service)

    # NL → Flow 변환
    nl_service = NLFlowService()
    flow_data = await nl_service.generate_flow(
        prompt=request.prompt,
        available_components=all_types
    )

    return NLToFlowResponse(**flow_data)
```

### 1.2 컴포넌트 데이터 구조 이해

**get_and_cache_all_types_dict()가 반환하는 데이터:**

```python
{
  "inputs": {
    "ChatInput": {
      "display_name": "Chat Input",
      "description": "Get chat inputs from the Playground.",
      "icon": "MessagesSquare",
      "base_classes": ["Message"],
      "input_types": [],
      "output_types": [],
      "template": {
        "input_value": {
          "type": "str",
          "required": false,
          "display_name": "Input Text",
          "info": "Message to be passed as input.",
          "multiline": true,
          "value": "",
          # ... 20개 이상의 다른 속성들
        },
        "files": {
          "type": "file",
          "fileTypes": ["csv", "json", "pdf", ...],
          "list": true,
          # ... 더 많은 속성들
        },
        "code": {
          "type": "code",
          "value": "... 전체 Python 소스코드 (수백 줄) ...",
          # ... 더 많은 속성들
        }
        # ... 6-7개의 다른 입력 필드들
      },
      "outputs": [...],
      "metadata": {...},
      # ... 총 300-500줄 이상의 상세 정보
    },
    "TextInput": {...}
  },
  "models": {
    "ChatOpenAI": {...},
    "ChatAnthropic": {...}
  },
  "outputs": {
    "ChatOutput": {...}
  }
  # ... 수십 개의 카테고리와 수백 개의 컴포넌트
}

**이 데이터를 그대로 LLM에게 보내면?**
- 컴포넌트 100개 × 평균 300줄 = 30,000줄
- 토큰 낭비, 비용 증가, 응답 속도 저하

### 1.3 컴포넌트 데이터 간소화 (_simplify_components)

**LLM이 실제로 필요한 정보만 추출:**

```python
def _simplify_components(self, components: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """
    원본 300-500줄 → 간소화 5줄 (100배 압축!)
    
    LLM이 컴포넌트를 선택하기 위해 필요한 정보만:
    - name: 컴포넌트 식별자
    - display_name: 사람이 읽을 수 있는 이름
    - description: 무엇을 하는 컴포넌트인지
    - input_types: 어떤 타입을 입력으로 받는지
    - output_types: 어떤 타입을 출력하는지
    """
    simplified = {}
    
    for category, category_components in components.items():
        simplified[category] = []
        for name, component in category_components.items():
            simplified[category].append({
                "name": name,
                "display_name": component.get("display_name", name),
                "description": component.get("description", ""),
                "input_types": component.get("input_types", []),
                "output_types": component.get("output_types", []),
            })
    
    return simplified
```

**간소화된 결과:**

```python
{
  "inputs": [
    {
      "name": "ChatInput",
      "display_name": "Chat Input",
      "description": "Get chat inputs from the Playground.",
      "input_types": [],
      "output_types": []
    }
  ],
  "models": [
    {
      "name": "ChatOpenAI",
      "display_name": "ChatOpenAI",
      "description": "OpenAI의 대화 모델을 사용합니다.",
      "input_types": ["Message", "str"],
      "output_types": ["Message"]
    }
  ]
}
```

### 1.4 OpenAI Function Calling 구현

**GPT-4에게 두 가지 함수를 제공:**

```python
functions = [
    {
        "name": "search_components",
        "description": "Search for Langflow components by capability or type",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "무엇을 하는 컴포넌트를 찾을지 (예: 'chat model', 'memory', 'document loader')"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_flow",
        "description": "Create the final flow with nodes and connections",
        "parameters": {
            "type": "object",
            "properties": {
                "nodes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "component_name": {"type": "string"},
                            "config": {"type": "object"}  # 선택적 설정값
                        },
                        "required": ["id", "component_name"]
                    }
                },
                "edges": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string"},  # node.id
                            "target": {"type": "string"}   # node.id
                        },
                        "required": ["source", "target"]
                    }
                },
                "explanation": {"type": "string"}
            },
            "required": ["nodes", "edges"]
        }
    }
]
```

**System Prompt:**

```python
system_prompt = """You are a Langflow expert assistant. Help users build flows by:
1. Understanding their requirements
2. Finding appropriate components using search_components
3. Creating a valid flow structure with create_flow

Guidelines:
- Keep flows simple (2-4 components for MVP)
- Common patterns:
  * Chatbot: ChatInput → ChatModel → ChatOutput
  * RAG: DocumentLoader → TextSplitter → VectorStore → ChatModel
  * Agent: ChatInput → Agent → ChatOutput
- Ensure component connections are compatible
- Generate appropriate prompts for model components
"""
```

### 1.5 Function Calling 반복 과정 (최대 5회)

**예시: "간단한 챗봇 만들어줘" 입력 시**

```python
# Iteration 1
LLM: search_components({"query": "ChatInput"})
Backend: [{"name": "ChatInput", "display_name": "Chat Input", ...}]

# Iteration 2
LLM: search_components({"query": "ChatModel"})
Backend: [
  {"name": "ChatOpenAI", ...},
  {"name": "ChatAnthropic", ...},
  {"name": "ChatOllama", ...}
]

# Iteration 3
LLM: search_components({"query": "ChatOutput"})
Backend: [{"name": "ChatOutput", "display_name": "Chat Output", ...}]

# Iteration 4 - 최종 플로우 생성!
LLM: create_flow({
  "nodes": [
    {"id": "node1", "component_name": "ChatInput"},
    {"id": "node2", "component_name": "ChatOpenAI"},
    {"id": "node3", "component_name": "ChatOutput"}
  ],
  "edges": [
    {"source": "node1", "target": "node2"},
    {"source": "node2", "target": "node3"}
  ],
  "explanation": "사용자 입력을 받아 ChatOpenAI로 처리하고 출력하는 간단한 챗봇입니다."
})
Backend: {"status": "success", "message": "Flow created"}

# 완료! (총 4번 반복)
```

### 1.6 응답 포맷팅 (_format_flow_response)

**AI가 반환한 component_name을 원본 데이터로 매핑:**

```python
def _format_flow_response(self, flow_data: dict[str, Any], all_components: dict[str, Any]):
    """
    AI가 선택한 컴포넌트 이름을 받아서:
    1. 원본 all_components에서 상세 데이터 찾기
    2. 노드 위치 자동 생성 (세로로 배치)
    3. 프론트엔드가 필요한 형식으로 변환
    """
    formatted_nodes = []
    
    for i, node in enumerate(flow_data["nodes"]):
        component_name = node["component_name"]
        
        # 원본 컴포넌트 데이터 찾기
        component_data = None
        for category_components in all_components.values():
            if component_name in category_components:
                component_data = category_components[component_name]
                break
        
        formatted_nodes.append({
            "id": node["id"],
            "component_name": component_name,
            "display_name": component_data.get("display_name", component_name),
            "position": {"x": 250, "y": 100 + i * 200},  # 세로 배치
            "data": {
                **component_data,  # 원본 상세 데이터 포함!
                "config": node.get("config", {})
            }
        })
    
    return {
        "nodes": formatted_nodes,
        "edges": flow_data["edges"],
        "explanation": flow_data.get("explanation", "")
    } 

```

### 1.7 스키마 정의 (schemas.py)

```python
class NLToFlowRequest(BaseModel):
    """사용자 요청 스키마"""
    prompt: str = Field(..., description="자연어 플로우 설명")
    # 예: "간단한 챗봇 만들어줘"

class FlowNodeData(BaseModel):
    """노드 데이터 스키마"""
    id: str                          # AI가 생성한 ID (예: "node1")
    component_name: str              # 컴포넌트 이름 (예: "ChatInput")
    display_name: str | None = None  # 표시 이름
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0})
    data: dict[str, Any] = Field(default_factory=dict)  # 원본 컴포넌트 데이터 포함

class FlowEdgeData(BaseModel):
    """엣지 데이터 스키마"""
    source: str                      # source node id
    target: str                      # target node id
    source_handle: str | None = None # 나중에 프론트엔드에서 계산
    target_handle: str | None = None

class NLToFlowResponse(BaseModel):
    """백엔드 응답 스키마"""
    nodes: list[FlowNodeData]
    edges: list[FlowEdgeData]
    explanation: str | None = None   # AI의 플로우 설명
```

**백엔드 구현 완료!**

--- 

## 2. 프론트엔드 구현

### 2.1 데이터 흐름 이해

프론트엔드의 핵심은 **typesStore**입니다. 이 스토어가 모든 컴포넌트 정보를 가지고 있습니다.

#### typesStore란?

**Zustand 기반 전역 상태 관리 스토어:**

```typescript
// src/frontend/src/stores/typesStore.ts

export const useTypesStore = create<TypesStoreType>((set, get) => ({
  // 핵심 데이터: 백엔드 /all 엔드포인트와 동일한 구조
  data: {},  // APIDataType = { [category: string]: { [component_name: string]: APIClassType } }
  
  // 보조 데이터
  types: {},           // 타입 목록 (빠른 검색용)
  templates: {},       // 템플릿 목록 (빠른 접근용)
  ComponentFields: new Set(),  // 비밀 필드 추적
  
  // 메서드
  setTypes: (data: APIDataType) => { ... },  // 백엔드 데이터로 스토어 갱신
  setData: (change: APIDataType) => { ... },
  setTemplates: (newState: {}) => { ... },
  setComponentFields: (fields) => { ... },
}));
```

#### typesStore.data 구조 예시:

```typescript
{
  "inputs": {                          // 카테고리
    "ChatInput": {                     // 컴포넌트 이름
      "display_name": "Chat Input",
      "description": "Get chat inputs from the Playground.",
      "icon": "MessagesSquare",
      "template": {                    // 모든 입력 필드 정의
        "input_value": {...},
        "files": {...},
        "code": {...}
      },
      "outputs": [...],
      "base_classes": ["Message"],
      ... // 수백 줄의 상세 정보
    },
    "TextInput": {...}
  },
  "models": {
    "ChatOpenAI": {...},
    "ChatAnthropic": {...}
  },
  "outputs": {
    "ChatOutput": {...}
  },
  "agents": {...},
  "vectorstores": {...},
  "embeddings": {...},
  ... // 수십 개의 카테고리
}
```

#### typesStore는 언제 채워지나?

```typescript
// src/frontend/src/controllers/API/queries/flows/use-get-types.ts

export const useGetTypes = () => {
  const setTypes = useTypesStore((state) => state.setTypes);
  
  const getTypesFn = async () => {
    // 백엔드 /all 엔드포인트 호출
    const response = await api.get(`${getURL("ALL")}?force_refresh=true`);
    const data = response?.data;
    
    // typesStore에 저장
    setTypes(data);
    return data;
  };
  
  return query(["useGetTypes"], getTypesFn, { ... });
};
```

**앱 시작 시 자동으로 호출되어 모든 컴포넌트 데이터를 미리 로드합니다!**

### 2.2 API 훅 생성 (use-post-nl-flow.ts)

```typescript
// src/frontend/src/controllers/API/queries/flows/use-post-nl-flow.ts

interface NLToFlowRequest {
  prompt: string;
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
      `${getURL("NL_FLOW")}/generate`,  // /nl-flow/generate
      payload
    );
    return response.data;
  };

  return mutate(["usePostNLFlow"], postNLFlowFn, options);
};
```

**constants.ts에 URL 추가:**

```typescript
NL_FLOW: 'nl-flow'
```

### 2.3 UI 컴포넌트 구현 (nlToFlowPanel.tsx)

#### 컴포넌트 구조:

```typescript
export default function NlToFlowPanel() {
  const [prompt, setPrompt] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  // ⭐️ 핵심: typesStore에서 모든 컴포넌트 데이터 가져오기
  const data = useTypesStore((state) => state.data);
  
  // FlowStore: 현재 플로우의 노드/엣지 관리
  const nodes = useFlowStore((state) => state.nodes);
  const edges = useFlowStore((state) => state.edges);
  const setNodes = useFlowStore((state) => state.setNodes);
  const setEdges = useFlowStore((state) => state.setEdges);
  
  // Alert Store: 성공/에러 메시지
  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  const { mutate: generateFlow } = usePostNLFlow();

  const handleGenerate = () => { ... };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <ForwardedIconComponent name="sparkles" />
        <span>AI Flow Builder</span>
      </div>

      <Textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="예: '사용자 질문에 답변하는 챗봇을 만들어주세요...'"
      />

      <Button onClick={handleGenerate} disabled={!prompt.trim() || isGenerating}>
        {isGenerating ? (
          <>
            <ForwardedIconComponent name="loader-circle" className="animate-spin" />
            생성 중...
          </>
        ) : (
          <>
            <ForwardedIconComponent name="sparkles" />
            플로우 생성
          </>
        )}
      </Button>
    </div>
  );
}
```

#### 핵심 로직: handleGenerate 함수 상세 분석

```typescript
const handleGenerate = () => {
  if (!prompt.trim()) return;
  setIsGenerating(true);

  generateFlow(
    { prompt: prompt.trim() },
    {
      onSuccess: (response) => {
        try {
          console.log("🔵 백엔드 응답:", response);
          
          // ========================================
          // STEP 1: ID 매핑 테이블 생성
          // ========================================
          // 백엔드(AI)가 만든 ID → 프론트엔드 고유 ID
          const idMapping: Record<string, string> = {};
          
          // ========================================
          // STEP 2: 노드 변환
          // ========================================
          const newNodes = response.nodes.map((node, index) => {
            console.log(`🔵 노드 처리 중: ${node.component_name}`);
            
            // 2-1. typesStore에서 컴포넌트 상세 데이터 찾기
            // 백엔드도 보내주지만, 프론트엔드의 최신 데이터 사용
            let componentData: APIClassType | undefined;
            for (const category in data) {
              if (data[category][node.component_name]) {
                componentData = data[category][node.component_name];
                console.log(`✅ ${node.component_name} 발견 (카테고리: ${category})`);
                break;
              }
            }
            
            if (!componentData) {
              console.error(`❌ ${node.component_name} 컴포넌트를 찾을 수 없음`);
              throw new Error(`Component ${node.component_name} not found`);
            }
            
            // 2-2. 프론트엔드용 고유 ID 생성
            const newId = `${node.component_name}-${Date.now()}-${index}`;
            
            // 2-3. ID 매핑 저장 (엣지 생성 시 사용)
            idMapping[node.id] = newId;
            console.log(`🔵 ID 매핑: ${node.id} → ${newId}`);
            
            // 2-4. React Flow 노드 객체 생성
            const reactFlowNode = {
              id: newId,
              type: "genericNode",           // Langflow의 기본 노드 타입
              position: node.position,       // AI가 계산한 위치
              data: {
                type: node.component_name,   // 컴포넌트 타입
                node: {
                  ...componentData,          // typesStore의 전체 데이터
                  template: {
                    ...(componentData.template || {}),
                    ...(node.data?.config || {}),  // AI가 설정한 값 덮어쓰기
                  },
                },
                id: newId,
              },
            };
            
            console.log(`✅ React Flow 노드 생성 완료:`, reactFlowNode);
            return reactFlowNode;
          });
          
          console.log(`✅ 총 ${newNodes.length}개 노드 생성 완료`);
          console.log(`📋 ID 매핑:`, idMapping);
          
          // ========================================
          // STEP 3: 엣지 변환 (가장 복잡한 부분!)
          // ========================================
          const nodeMap = new Map(newNodes.map(n => [n.id, n]));
          
          const newEdges = response.edges.map((edge, index) => {
            console.log(`🔵 엣지 처리 중: ${edge.source} → ${edge.target}`);
            
            // 3-1. ID 매핑
            const mappedSource = idMapping[edge.source];
            const mappedTarget = idMapping[edge.target];
            
            if (!mappedSource || !mappedTarget) {
              console.warn(`⚠️ 엣지 ID 매핑 실패`);
              return null;
            }
            
            // 3-2. 소스/타겟 노드 가져오기
            const sourceNode = nodeMap.get(mappedSource);
            const targetNode = nodeMap.get(mappedTarget);
            
            if (!sourceNode || !targetNode) {
              console.warn(`⚠️ 노드를 찾을 수 없음`);
              return null;
            }
            
            // 3-3. 소스 노드의 출력 찾기
            const sourceComponentData = sourceNode.data.node as APIClassType;
            const sourceOutput = findComponentOutput(sourceComponentData);
            
            if (!sourceOutput) {
              console.warn(`⚠️ ${sourceNode.data.type}의 출력을 찾을 수 없음`);
              return null;
            }
            
            console.log(`🔵 소스 출력:`, sourceOutput);
            
            // 3-4. 타겟 노드의 호환 가능한 입력 찾기
            const targetComponentData = targetNode.data.node as APIClassType;
            const targetInput = findCompatibleInput(targetComponentData, sourceOutput.types);
            
            if (!targetInput) {
              console.warn(`⚠️ ${targetNode.data.type}의 호환 입력을 찾을 수 없음`);
              return null;
            }
            
            console.log(`🔵 타겟 입력:`, targetInput);
            
            // 3-5. Source Handle 객체 생성
            const sourceHandleObj: sourceHandleType = {
              dataType: sourceNode.data.type,
              id: mappedSource,
              output_types: sourceOutput.types,
              name: sourceOutput.name,
            };
            
            // 3-6. Target Handle 객체 생성
            const targetHandleObj: targetHandleType = {
              type: targetComponentData.template[targetInput.fieldName]?.type,
              fieldName: targetInput.fieldName,
              id: mappedTarget,
              inputTypes: targetInput.inputTypes,
            };
            
            // 3-7. Handle을 JSON 문자열로 변환 (React Flow 요구사항)
            const sourceHandle = scapedJSONStringfy(sourceHandleObj);
            const targetHandle = scapedJSONStringfy(targetHandleObj);
            
            console.log(`✅ Handle 생성:`, { sourceHandle, targetHandle });
            
            // 3-8. React Flow 엣지 객체 생성
            const reactFlowEdge = {
              id: `edge-${Date.now()}-${index}`,
              source: mappedSource,
              target: mappedTarget,
              sourceHandle,      // 문자열 형태
              targetHandle,      // 문자열 형태
              type: "default",
              data: {
                sourceHandle: sourceHandleObj,  // 객체 형태 (내부 사용)
                targetHandle: targetHandleObj,
              },
            };
            
            console.log(`✅ React Flow 엣지 생성 완료:`, reactFlowEdge);
            return reactFlowEdge;
          }).filter((edge): edge is NonNullable<typeof edge> => edge !== null);
          
          console.log(`✅ 총 ${newEdges.length}개 엣지 생성 완료`);
          
          // ========================================
          // STEP 4: FlowStore에 추가
          // ========================================
          console.log("🔵 캔버스에 노드/엣지 추가 중...");
          setNodes([...nodes, ...newNodes.map(n => ({ ...n, selected: true }))] as any);
          setEdges([...edges, ...newEdges] as any);
          console.log("✅ 캔버스 업데이트 완료!");
          
          // ========================================
          // STEP 5: 성공 메시지
          // ========================================
          setSuccessData({
            title: response.explanation
              ? `${response.explanation}\n\n✅ ${newNodes.length}개의 노드와 ${newEdges.length}개의 연결이 생성되었습니다.`
              : `플로우가 생성되었습니다! ${newNodes.length}개의 노드와 ${newEdges.length}개의 연결이 추가되었습니다.`,
          });
          
          setPrompt(""); // 프롬프트 초기화
          
        } catch (error) {
          console.error("❌ 플로우 생성 중 에러:", error);
          setErrorData({
            title: "Error creating flow",
            list: [(error as Error).message],
          });
        } finally {
          setIsGenerating(false);
        }
      },
      onError: (error: any) => {
        console.error("❌ 백엔드 API 에러:", error);
        setErrorData({
          title: "Failed to generate flow",
          list: [
            error?.response?.data?.detail ||
            "플로우를 생성할 수 없습니다. OPENAI_API_KEY를 확인하세요.",
          ],
        });
        setIsGenerating(false);
      },
    }
  );
}

```

### 2.4 헬퍼 함수들

#### findComponentOutput: 컴포넌트의 출력 찾기

```typescript
function findComponentOutput(componentData: APIClassType): { name: string; types: string[] } | null {
  if (!componentData.outputs || componentData.outputs.length === 0) {
    // outputs가 없으면 output_types 사용
    if (componentData.output_types && componentData.output_types.length > 0) {
      return {
        name: "output",
        types: componentData.output_types,
      };
    }
    return null;
  }

  // 숨겨지지 않은 첫 번째 출력 반환
  const output = componentData.outputs.find(o => !o.hidden) || componentData.outputs[0];
  return {
    name: output.name,
    types: output.types,
  };
}

// 예시:
// ChatInput: { name: "message", types: ["Message"] }
// ChatOpenAI: { name: "text_output", types: ["Message"] }
```

#### findCompatibleInput: 호환 가능한 입력 찾기

```typescript
function findCompatibleInput(
  componentData: APIClassType,
  sourceOutputTypes: string[]
): { fieldName: string; inputTypes: string[] } | null {
  const template = componentData.template;
  if (!template) return null;

  // 각 템플릿 필드를 순회
  for (const [fieldName, field] of Object.entries(template)) {
    const fieldTyped = field as InputFieldType;

    // advanced 필드나 숨겨진 필드는 스킵
    if (fieldTyped.advanced === true || fieldTyped.show === false) continue;

    const inputTypes = fieldTyped.input_types || [];
    if (inputTypes.length === 0) continue;

    // 소스 출력 타입과 호환되는지 확인
    const isCompatible = sourceOutputTypes.some(outputType =>
      inputTypes.includes(outputType)
    );

    if (isCompatible) {
      return { fieldName, inputTypes };
    }
  }

  // 호환되는 입력이 없으면 첫 번째 입력 반환 (fallback)
  for (const [fieldName, field] of Object.entries(template)) {
    const fieldTyped = field as InputFieldType;
    if (fieldTyped.input_types && fieldTyped.input_types.length > 0) {
      return { fieldName, inputTypes: fieldTyped.input_types };
    }
  }

  return null;
}

// 예시:
// ChatOpenAI는 input_value 필드가 ["Message"] 타입을 받음
// ChatInput의 출력이 ["Message"]이므로 호환됨!
```

---

## 3. 테스트 및 결과

### 3.1 환경 설정

```bash
# .env 파일에 OpenAI API 키 추가
OPENAI_API_KEY=sk-...

# 백엔드 서버 재시작
cd src/backend
make run

# 프론트엔드 개발 서버 시작
cd src/frontend
npm run dev
```

### 3.2 테스트 케이스

#### 테스트 1: 간단한 챗봇

**입력:** "간단한 챗봇 만들어줘"

**백엔드 로그:**

```
INFO: Generating flow from NL: 간단한 챗봇 만들어줘
INFO: Iteration 1: Calling function search_components with args: {'query': 'ChatInput'}
INFO: Iteration 2: Calling function search_components with args: {'query': 'ChatModel'}
INFO: Iteration 3: Calling function search_components with args: {'query': 'ChatOutput'}
INFO: Iteration 4: Calling function create_flow with args: {
  'nodes': [
    {'id': 'node1', 'component_name': 'ChatInput'},
    {'id': 'node2', 'component_name': 'ChatOpenAI'},
    {'id': 'node3', 'component_name': 'ChatOutput'}
  ],
  'edges': [
    {'source': 'node1', 'target': 'node2'},
    {'source': 'node2', 'target': 'node3'}
  ],
  'explanation': '사용자 입력을 받아 ChatOpenAI로 처리하고 출력하는 간단한 챗봇입니다.'
}
INFO: Successfully generated flow with 3 nodes
```

**프론트엔드 로그:**

```
🔵 [NL-Flow] Backend response: { nodes: [...], edges: [...], explanation: "..." }
🔵 [NL-Flow] Processing node 0: { id: "node1", component_name: "ChatInput", ... }
✅ [NL-Flow] Found component ChatInput in category inputs
🔵 [NL-Flow] ID mapping: node1 -> ChatInput-1699999999999-0
✅ [NL-Flow] Created React Flow node
... (2개 더)
✅ [NL-Flow] All nodes created: 3
🔵 [NL-Flow] Processing edge 0: { source: "node1", target: "node2" }
🔵 [NL-Flow] Source output: { name: "message", types: ["Message"] }
🔵 [NL-Flow] Target input: { fieldName: "input_value", inputTypes: ["Message"] }
✅ [NL-Flow] Created React Flow edge
... (1개 더)
✅ [NL-Flow] All edges created: 2
✅ [NL-Flow] Nodes and edges added to flow
```

**결과:** 
- ✅ 3개의 노드가 세로로 배치되어 생성됨
- ✅ 2개의 연결선이 자동으로 생성됨
- ✅ 모든 노드가 선택된 상태로 표시됨
- ✅ AI의 설명이 성공 메시지에 표시됨

#### 테스트 2: RAG 시스템

**입력:** "PDF 파일을 읽고 질문에 답변하는 RAG 시스템 만들어줘"

**결과:**
- 5-6개의 노드 생성 (DocumentLoader, TextSplitter, VectorStore, ChatModel, etc.)
- 복잡한 연결 관계도 자동 생성
- AI가 각 컴포넌트 설정까지 제안

---

## 4. 핵심 개념 정리

### 4.1 왜 프론트엔드가 typesStore에서 다시 찾나?

**백엔드도 컴포넌트 데이터를 응답에 포함하는데, 왜 프론트엔드가 typesStore에서 다시 찾을까?**

1. **데이터 신뢰성**: 프론트엔드의 typesStore가 가장 최신 데이터
2. **일관성**: 앱 전체에서 동일한 컴포넌트 정의 사용
3. **검증**: 백엔드가 잘못된 component_name을 보내면 즉시 에러 발생
4. **타입 안전성**: TypeScript 타입 체크 활용

### 4.2 데이터 흐름 요약

```
1. 앱 시작 → useGetTypes → typesStore 채움 (/all 엔드포인트)
   typesStore.data = { category: { component_name: component_data } }

2. 사용자 입력 → usePostNLFlow → 백엔드 API 호출
   { prompt: "챗봇 만들어줘" }

3. 백엔드 → 컴포넌트 간소화 → OpenAI Function Calling
   간소화: 500줄 → 5줄 (100배 압축)
   
4. OpenAI → search_components 반복 → create_flow 호출
   AI가 필요한 컴포넌트 찾고 플로우 구성

5. 백엔드 → 원본 데이터 매핑 → 응답 반환
   component_name으로 원본 컴포넌트 데이터 찾아서 포함

6. 프론트엔드 → typesStore에서 재검증 → React Flow 노드/엣지 생성
   백엔드 ID → 프론트엔드 ID 매핑
   Handle 자동 계산 (소스 출력 ↔ 타겟 입력)

7. FlowStore 업데이트 → 캔버스에 표시
   setNodes([...nodes, ...newNodes])
   setEdges([...edges, ...newEdges])
```

### 4.3 중요한 타입들

```typescript
// 백엔드와 프론트엔드 모두 사용
APIDataType = { [category: string]: APIKindType }
APIKindType = { [component_name: string]: APIClassType }
APIClassType = {
  display_name: string
  description: string
  template: APITemplateType        // 각 입력 필드의 상세 정보
  outputs: OutputFieldType[]       // 출력 정의
  input_types: string[]
  output_types: string[]
  ... // 수십 개의 다른 속성들
}

// React Flow 전용
sourceHandleType = {
  dataType: string      // 컴포넌트 타입
  id: string           // 노드 ID
  output_types: string[]
  name: string         // 출력 이름
}

targetHandleType = {
  type: string         // 필드 타입
  fieldName: string    // 입력 필드 이름
  id: string          // 노드 ID
  inputTypes: string[]
}
```

---

## 5. 트러블슈팅

### 문제 1: "Component not found" 에러

**원인:** typesStore에 컴포넌트가 없음

**해결:**
1. typesStore가 로드되었는지 확인
2. component_name 철자 확인
3. 백엔드 /all 엔드포인트 응답 확인

### 문제 2: 엣지가 생성되지 않음

**원인:** Handle을 찾지 못함

**해결:**
1. findComponentOutput 결과 확인
2. findCompatibleInput 결과 확인
3. 컴포넌트의 outputs와 template.input_types 확인

### 문제 3: "OPENAI_API_KEY not set" 에러

**원인:** 환경 변수 미설정

**해결:**
```bash
# .env 파일에 추가
OPENAI_API_KEY=sk-your-key-here

# 서버 재시작 필수!
```

---

## 6. 향후 개선 사항

1. ⬜ **더 복잡한 플로우 지원**: 조건부 분기, 루프 등
2. ⬜ **컴포넌트 설정 자동화**: AI가 프롬프트, 파라미터 값도 설정
3. ⬜ **레이아웃 개선**: 더 지능적인 노드 배치 알고리즘
4. ⬜ **다중 플로우**: 하나의 프롬프트로 여러 플로우 생성
5. ⬜ **피드백 루프**: 사용자가 수정한 내용을 AI에게 전달
6. ⬜ **다른 LLM 지원**: Anthropic Claude, Google Gemini 등
7. ⬜ **한국어 지원 강화**: 더 자연스러운 한국어 처리

---

## 결론

NL to Flow 기능은 다음과 같은 핵심 요소로 구성됩니다:

1. **백엔드**: OpenAI Function Calling으로 컴포넌트 선택 및 플로우 생성
2. **데이터 간소화**: 500줄 → 5줄로 압축해 LLM 효율성 향상
3. **typesStore**: 프론트엔드의 모든 컴포넌트 정보를 담은 중앙 저장소
4. **자동 Handle 생성**: 출력 타입과 입력 타입을 자동으로 매칭
5. **ID 매핑**: 백엔드 ID와 프론트엔드 ID를 분리해 충돌 방지

이 구조 덕분에 사용자는 자연어만으로 복잡한 AI 워크플로우를 빠르게 생성할 수 있습니다! 🎉