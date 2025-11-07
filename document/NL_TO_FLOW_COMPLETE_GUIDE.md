# Natural Language to Flow - 완전한 가이드

Langflow에서 자연어 입력을 통해 플로우를 자동 생성하는 기능의 종합 문서입니다.

---

## 📚 목차

1. [개요](#개요)
2. [빠른 시작](#빠른-시작)
3. [아키텍처](#아키텍처)
4. [데이터 타입 및 스키마](#데이터-타입-및-스키마)
5. [백엔드 구현](#백엔드-구현)
6. [프론트엔드 구현](#프론트엔드-구현)
7. [테스트](#테스트)
8. [트러블슈팅](#트러블슈팅)
9. [개발 노트](#개발-노트)
10. [향후 계획](#향후-계획)

---

## 개요

### 기능 설명

사용자가 자연어로 원하는 플로우를 설명하면, AI(GPT-4)가 자동으로 적절한 컴포넌트를 선택하고 연결하여 플로우를 생성합니다.

**예시:**
- 입력: "간단한 챗봇 만들어줘"
- 결과: ChatInput → ChatOpenAI → ChatOutput 플로우 자동 생성

### 핵심 기술

- **OpenAI GPT-4 Function Calling**: AI가 컴포넌트를 검색하고 플로우 구조 생성
- **컴포넌트 간소화**: 500줄의 상세 데이터를 5줄로 압축하여 LLM에 전달
- **타입 기반 연결**: 출력/입력 타입을 자동으로 매칭하여 연결

### 전체 데이터 흐름

```
사용자 입력 (자연어)
    ↓
Frontend (nlToFlowPanel.tsx)
    ↓ POST /api/v1/nl-flow/generate
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

## 빠른 시작

### 1. 환경 설정

#### OpenAI API 키 설정

`.env` 파일에 다음을 추가:

```bash
OPENAI_API_KEY=sk-your-api-key-here
```

또는 환경 변수로 설정:

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

#### 패키지 설치

```bash
cd src/backend/base
pip install openai
```

#### 서버 재시작

```bash
# 개발 환경
langflow run

# 또는
make run
```

### 2. 사용 방법

1. 플로우 편집 페이지의 왼쪽 사이드바에서 **"AI Flow Builder"** 섹션을 찾습니다
2. 텍스트 입력창에 플로우 설명을 입력합니다
3. **"플로우 생성"** 버튼을 클릭합니다
4. 생성된 플로우가 캔버스에 자동으로 추가됩니다

### 3. 예제 프롬프트

```
✅ "간단한 챗봇 만들어줘"
→ ChatInput → ChatOpenAI → ChatOutput

✅ "PDF 파일을 읽고 질문에 답변하는 RAG 시스템 만들어줘"
→ DocumentLoader → TextSplitter → VectorStore → ChatModel

✅ "Create a chatbot with memory"
→ ChatInput → ChatModel → ChatOutput + Memory

✅ "Build a document Q&A system"
→ DocumentLoader → TextSplitter → VectorStore → ChatModel
```

---

## 아키텍처

### 컴포넌트 구조

```
┌─────────────────────────────────────────────────────────────────┐
│ User Input                                                      │
│ "Create a simple chatbot with memory"                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Frontend (nlToFlowPanel.tsx)                                    │
│ POST /api/v1/nl-flow/generate                                   │
│ { "prompt": "Create a simple chatbot..." }                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Backend (nl_flow.py)                                            │
│ 1. Get all components via get_and_cache_all_types_dict()       │
│ 2. Call NLFlowService.generate_flow()                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ NLFlowService (service.py)                                      │
│ 1. Simplify components for LLM context                         │
│ 2. Call OpenAI GPT-4 with function definitions                 │
│ 3. LLM uses search_components and create_flow functions        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ OpenAI GPT-4 Function Calling                                   │
│ Returns:                                                        │
│ {                                                               │
│   "nodes": [                                                    │
│     {"id": "node-1", "component_name": "ChatInput", ...},      │
│     {"id": "node-2", "component_name": "ChatModel", ...}       │
│   ],                                                            │
│   "edges": [{"source": "node-1", "target": "node-2"}],        │
│   "explanation": "..."                                          │
│ }                                                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Backend Response Formatting (service.py)                        │
│ 1. Generate node positions (vertical layout)                   │
│ 2. Lookup full component data for each node                    │
│ 3. Return FlowNodeData[] and FlowEdgeData[]                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Frontend Response Processing (nlToFlowPanel.tsx)                │
│ 1. Create ID mapping: Backend ID → Frontend ID                 │
│ 2. Convert nodes to React Flow format                          │
│ 3. Generate edge handles (sourceHandle, targetHandle)          │
│ 4. Add to Flow Store                                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ React Flow Canvas                                               │
│ ┌─────────────┐        ┌──────────────┐                        │
│ │ Chat Input  │───────▶│ Chat Model   │                        │
│ └─────────────┘        └──────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

### 주요 파일 구조

#### 백엔드

- `src/backend/base/langflow/api/v1/nl_flow.py` - FastAPI 엔드포인트
- `src/backend/base/langflow/services/nl_flow/service.py` - LLM Function Calling 로직
- `src/backend/base/langflow/api/v1/schemas.py` - 요청/응답 스키마

#### 프론트엔드

- `src/frontend/src/pages/FlowPage/components/flowSidebarComponent/components/nlToFlowPanel.tsx` - UI 및 변환 로직
- `src/frontend/src/controllers/API/queries/flows/use-post-nl-flow.ts` - API 호출
- `src/frontend/src/types/api/index.ts` - API 타입 정의
- `src/frontend/src/types/flow/index.ts` - Flow 타입 정의

---

## 데이터 타입 및 스키마

### API 요청/응답

#### Request (Python)

```python
# src/backend/base/langflow/api/v1/schemas.py

class NLToFlowRequest(BaseModel):
    """Request schema for natural language to flow generation."""
    prompt: str = Field(..., description="Natural language description of the flow to create")
```

#### Request (TypeScript)

```typescript
// src/frontend/src/controllers/API/queries/flows/use-post-nl-flow.ts

interface NLToFlowRequest {
  prompt: string;  // 자연어 플로우 설명
}
```

#### Response (Python)

```python
class FlowNodeData(BaseModel):
    """Schema for a flow node in the generated flow."""
    id: str = Field(..., description="Unique ID for the node")
    component_name: str = Field(..., description="Name of the component to use")
    display_name: str | None = Field(None, description="Display name for the node")
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0})
    data: dict[str, Any] = Field(default_factory=dict, description="Node configuration data")

class FlowEdgeData(BaseModel):
    """Schema for a flow edge in the generated flow."""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    source_handle: str | None = Field(None, description="Source handle/output field")
    target_handle: str | None = Field(None, description="Target handle/input field")

class NLToFlowResponse(BaseModel):
    """Response schema for natural language to flow generation."""
    nodes: list[FlowNodeData] = Field(default_factory=list)
    edges: list[FlowEdgeData] = Field(default_factory=list)
    explanation: str | None = Field(None, description="Explanation of the generated flow")
```

#### Response (TypeScript)

```typescript
interface FlowNodeData {
  id: string;                           // Backend에서 생성한 ID
  component_name: string;               // "ChatInput", "ChatModel" 등
  display_name: string | null;          // 표시 이름
  position: { x: number; y: number };   // 노드 위치
  data: any;                            // 전체 컴포넌트 데이터 (APIClassType)
}

interface FlowEdgeData {
  source: string;                       // Source 노드 ID
  target: string;                       // Target 노드 ID
  source_handle: string | null;         // 아직 처리 안됨 (null)
  target_handle: string | null;         // 아직 처리 안됨 (null)
}

export interface NLToFlowResponse {
  nodes: FlowNodeData[];
  edges: FlowEdgeData[];
  explanation: string | null;
}
```

### 컴포넌트 메타데이터 타입

#### APIClassType (컴포넌트 메타데이터)

```typescript
// src/frontend/src/types/api/index.ts

export type APIClassType = {
  base_classes?: Array<string>;
  description: string;
  template: APITemplateType;          // 입력 필드 정의
  display_name: string;
  icon?: string;
  input_types?: Array<string>;        // 허용되는 입력 타입들
  output_types?: Array<string>;       // 생성하는 출력 타입들
  outputs?: Array<OutputFieldType>;   // 출력 필드 정의
  documentation: string;
  // ... 기타 속성들
};
```

#### InputFieldType (입력 필드 정의)

```typescript
export type InputFieldType = {
  type: string;                       // "str", "int", "Message" 등
  required: boolean;
  placeholder?: string;
  show: boolean;                      // false면 숨김
  advanced?: boolean;                 // true면 고급 옵션
  input_types?: Array<string>;        // 허용되는 입력 타입들
  display_name?: string;
  name?: string;
  // ... 기타 속성들
};
```

#### OutputFieldType (출력 필드 정의)

```typescript
export type OutputFieldType = {
  types: Array<string>;               // 출력 타입들 ["Message", "Text"]
  selected?: string;                  // 선택된 타입
  name: string;                       // 출력 이름
  display_name: string;
  hidden?: boolean;                   // 숨김 여부
  // ... 기타 속성들
};
```

### React Flow 타입

#### 노드 타입

```typescript
// src/frontend/src/types/flow/index.ts

export type GenericNodeType = Node<NodeDataType, "genericNode">;

export type NodeDataType = {
  showNode?: boolean;
  type: string;           // 컴포넌트 이름 (예: "ChatInput")
  node: APIClassType;     // 전체 컴포넌트 메타데이터
  id: string;             // Frontend에서 생성한 고유 ID
  output_types?: string[];
  selected_output_type?: string;
  buildStatus?: BuildStatus;
  selected_output?: string;
};
```

#### 엣지 타입

```typescript
export type EdgeType = Edge<EdgeDataType, "default">;

export type EdgeDataType = {
  sourceHandle: sourceHandleType;
  targetHandle: targetHandleType;
};

// 출력 핸들 (오른쪽)
export type sourceHandleType = {
  baseClasses?: string[];
  dataType: string;           // 컴포넌트 타입 (data.type)
  id: string;                 // 노드 ID
  output_types: string[];     // ["Message", "Text" 등]
  conditionalPath?: string | null;
  name: string;               // 출력 필드 이름
};

// 입력 핸들 (왼쪽)
export type targetHandleType = {
  inputTypes?: string[];      // 허용되는 입력 타입들
  output_types?: string[];
  type: string;               // 템플릿 필드 타입
  fieldName: string;          // 입력 필드 이름
  name?: string;
  id: string;                 // 노드 ID
  proxy?: { field: string; id: string };
};
```

---

## 백엔드 구현

### FastAPI 엔드포인트

```python
# src/backend/base/langflow/api/v1/nl_flow.py

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
    all_types = await get_and_cache_all_types_dict(settings_service=settings_service)

    # NL → Flow 변환
    nl_service = NLFlowService()
    flow_data = await nl_service.generate_flow(
        prompt=request.prompt,
        available_components=all_types
    )

    return NLToFlowResponse(**flow_data)
```

### 컴포넌트 데이터 구조

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
          # ... 20개 이상의 다른 속성들
        },
        # ... 6-7개의 다른 입력 필드들
      },
      "outputs": [...],
      "metadata": {...},
      # ... 총 300-500줄 이상의 상세 정보
    }
  },
  "models": {
    "ChatOpenAI": {...},
    "ChatAnthropic": {...}
  }
  # ... 수십 개의 카테고리와 수백 개의 컴포넌트
}
```

**문제점:** 컴포넌트 100개 × 평균 300줄 = 30,000줄
- 토큰 낭비, 비용 증가, 응답 속도 저하

### 컴포넌트 데이터 간소화

**LLM이 실제로 필요한 정보만 추출 (100배 압축!):**

```python
# src/backend/base/langflow/services/nl_flow/service.py

def _simplify_components(self, components: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """
    원본 300-500줄 → 간소화 5줄
    
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

### OpenAI Function Calling

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

### Function Calling 반복 과정

**예시: "간단한 챗봇 만들어줘" 입력 시 (최대 5회 반복)**

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

### 응답 포맷팅

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

---

## 프론트엔드 구현

### typesStore 이해하기

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
  // ...
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
    }
  },
  "models": {
    "ChatOpenAI": {...}
  },
  // ... 수십 개의 카테고리
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

### API 훅 생성

```typescript
// src/frontend/src/controllers/API/queries/flows/use-post-nl-flow.ts

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

### UI 컴포넌트

```typescript
// src/frontend/src/pages/FlowPage/components/flowSidebarComponent/components/nlToFlowPanel.tsx

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

  const handleGenerate = () => { /* ... */ };

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

### 핵심 로직: handleGenerate 함수

```typescript
const handleGenerate = () => {
  if (!prompt.trim()) return;
  setIsGenerating(true);

  generateFlow(
    { prompt: prompt.trim() },
    {
      onSuccess: (response) => {
        try {
          // STEP 1: ID 매핑 테이블 생성 (백엔드 ID → 프론트엔드 ID)
          const idMapping: Record<string, string> = {};
          
          // STEP 2: 노드 변환
          const newNodes = response.nodes.map((node, index) => {
            // 2-1. typesStore에서 컴포넌트 상세 데이터 찾기
            let componentData: APIClassType | undefined;
            for (const category in data) {
              if (data[category][node.component_name]) {
                componentData = data[category][node.component_name];
                break;
              }
            }
            
            if (!componentData) {
              throw new Error(`Component ${node.component_name} not found`);
            }
            
            // 2-2. 프론트엔드용 고유 ID 생성
            const newId = `${node.component_name}-${Date.now()}-${index}`;
            
            // 2-3. ID 매핑 저장 (엣지 생성 시 사용)
            idMapping[node.id] = newId;
            
            // 2-4. React Flow 노드 객체 생성
            return {
              id: newId,
              type: "genericNode",
              position: node.position,
              data: {
                type: node.component_name,
                node: {
                  ...componentData,
                  template: {
                    ...(componentData.template || {}),
                    ...(node.data?.config || {}),
                  },
                },
                id: newId,
              },
            };
          });
          
          // STEP 3: 엣지 변환
          const nodeMap = new Map(newNodes.map(n => [n.id, n]));
          
          const newEdges = response.edges.map((edge, index) => {
            // 3-1. ID 매핑
            const mappedSource = idMapping[edge.source];
            const mappedTarget = idMapping[edge.target];
            
            if (!mappedSource || !mappedTarget) return null;
            
            // 3-2. 소스/타겟 노드 가져오기
            const sourceNode = nodeMap.get(mappedSource);
            const targetNode = nodeMap.get(mappedTarget);
            
            if (!sourceNode || !targetNode) return null;
            
            // 3-3. 소스 노드의 출력 찾기
            const sourceComponentData = sourceNode.data.node as APIClassType;
            const sourceOutput = findComponentOutput(sourceComponentData);
            
            if (!sourceOutput) return null;
            
            // 3-4. 타겟 노드의 호환 가능한 입력 찾기
            const targetComponentData = targetNode.data.node as APIClassType;
            const targetInput = findCompatibleInput(targetComponentData, sourceOutput.types);
            
            if (!targetInput) return null;
            
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
            
            // 3-8. React Flow 엣지 객체 생성
            return {
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
          }).filter((edge): edge is NonNullable<typeof edge> => edge !== null);
          
          // STEP 4: FlowStore에 추가
          setNodes([...nodes, ...newNodes.map(n => ({ ...n, selected: true }))] as any);
          setEdges([...edges, ...newEdges] as any);
          
          // STEP 5: 성공 메시지
          setSuccessData({
            title: response.explanation
              ? `${response.explanation}\n\n✅ ${newNodes.length}개의 노드와 ${newEdges.length}개의 연결이 생성되었습니다.`
              : `플로우가 생성되었습니다! ${newNodes.length}개의 노드와 ${newEdges.length}개의 연결이 추가되었습니다.`,
          });
          
          setPrompt("");
          
        } catch (error) {
          setErrorData({
            title: "Error creating flow",
            list: [(error as Error).message],
          });
        } finally {
          setIsGenerating(false);
        }
      },
      onError: (error: any) => {
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
};
```

### Helper 함수들

#### findComponentOutput: 컴포넌트의 출력 찾기

```typescript
/**
 * 컴포넌트의 첫 번째 출력을 찾는 함수
 */
function findComponentOutput(componentData: APIClassType): { name: string; types: string[] } | null {
  if (!componentData.outputs || componentData.outputs.length === 0) {
    // Fallback: output_types 사용
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
/**
 * 컴포넌트에서 호환 가능한 입력 필드를 찾는 함수
 */
function findCompatibleInput(
  componentData: APIClassType,
  sourceOutputTypes: string[]
): { fieldName: string; inputTypes: string[] } | null {
  const template = componentData.template;
  if (!template) return null;

  // 호환 가능한 입력 필드 찾기
  for (const [fieldName, field] of Object.entries(template)) {
    const fieldTyped = field as InputFieldType;

    // advanced 또는 hidden 필드는 스킵
    if (fieldTyped.advanced === true || fieldTyped.show === false) continue;

    const inputTypes = fieldTyped.input_types || [];
    if (inputTypes.length === 0) continue;

    // 타입 호환성 체크
    const isCompatible = sourceOutputTypes.some(outputType =>
      inputTypes.includes(outputType)
    );

    if (isCompatible) {
      return { fieldName, inputTypes };
    }
  }

  // Fallback: 첫 번째 사용 가능한 입력 필드
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

## 테스트

### 테스트 케이스 1: 간단한 챗봇

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

### 테스트 케이스 2: RAG 시스템

**입력:** "PDF 파일을 읽고 질문에 답변하는 RAG 시스템 만들어줘"

**결과:**
- 5-6개의 노드 생성 (DocumentLoader, TextSplitter, VectorStore, ChatModel, etc.)
- 복잡한 연결 관계도 자동 생성
- AI가 각 컴포넌트 설정까지 제안

---

## 트러블슈팅

### 문제 0: LLM이 `create_flow`를 호출하지 않고 설명만 제공하는 문제

**증상:**
- LLM이 컴포넌트를 검색하지만 플로우를 생성하지 않음
- 5회 반복 후 "Failed to generate flow - LLM did not call create_flow function" 에러 발생
- 특히 "PDF 파일을 읽고 질문에 답변하는 RAG 시스템" 같은 요청에서 자주 발생

**원인:**
1. **컴포넌트 검색 실패**: PDF 관련 검색어("PDF loader", "PDF reader")로 FileComponent를 찾지 못함
2. **Fallback 전략 부재**: 정확한 컴포넌트를 못 찾으면 LLM이 포기하고 설명만 제공
3. **키워드 매칭 부족**: VALID_EXTENSIONS 정보가 검색에 활용되지 않음

**해결 (2025-11-07 적용됨):**

#### 1. System Prompt 개선
- Fallback 전략 명시: "정확한 컴포넌트를 못 찾으면 대안 사용"
- 구체적인 대안 제시: "PDF → 'File' 또는 'Read File' 컴포넌트 사용"
- 강력한 지시: "ALWAYS call create_flow, 설명만 하지 말 것"

```python
# src/backend/base/langflow/services/nl_flow/service.py:116-122
IMPORTANT - Fallback Strategy:
- If you cannot find the exact component after 2-3 searches, use the closest alternative
- For PDF/document files, use 'File' or 'Read File' component (supports PDF, DOCX, etc.)
- ALWAYS call create_flow function after finding components, even with alternatives
- Do NOT explain why something cannot be done - find creative workarounds
```

#### 2. 컴포넌트 검색 강화 - Keywords 시스템

**_simplify_components 개선:**
```python
# src/backend/base/langflow/services/nl_flow/service.py:183-241

def _simplify_components(self, components):
    # VALID_EXTENSIONS 기반 키워드 자동 생성
    valid_extensions = component.get("VALID_EXTENSIONS", [])
    keywords = []

    if "pdf" in ext_lower:
        keywords.extend(["PDF", "PDF loader", "PDF reader", "PDF parser", "document loader"])

    # 컴포넌트 이름/타입 기반 키워드 추가
    if "split" in component_name_lower:
        keywords.extend(["text splitter", "chunk", "chunking"])
```

**_search_components 개선:**
```python
# src/backend/base/langflow/services/nl_flow/service.py:243-288

def _search_components(self, query, components):
    # 점수 기반 검색으로 개선
    - Exact name match: +100점
    - Display name match: +50점
    - Keywords match: +40점
    - Partial keyword match: +35점
    - Name substring: +30점
    - Description match: +20점

    # 점수 순으로 정렬하여 반환
```

**효과:**
- "PDF loader" 검색 → FileComponent가 keywords: ["PDF", "PDF loader", ...] 로 매칭됨
- "text splitter" 검색 → RecursiveCharacterTextSplitter 등이 자동 매칭
- 더 이상 빈 결과([]) 반환 없음

#### 3. 검증 및 결과

**변경 전:**
```bash
# 로그
2025-11-07 09:05:22 | INFO | Iteration 5: Calling function search_components with args: {'query': 'text splitter'}
2025-11-07 09:05:22 | ERROR | No flow created. Last message: {...}
2025-11-07 09:05:22 | ERROR | Error in generate_flow: Failed to generate flow
```

**변경 후 (예상):**
```bash
# 로그
Iteration 1: search_components("PDF loader")
  → Found: FileComponent (score: 75 from keywords)
Iteration 2: search_components("text splitter")
  → Found: RecursiveCharacterTextSplitter (score: 85)
Iteration 3: create_flow({
  nodes: [FileComponent, TextSplitter, VectorStore, ChatModel],
  edges: [...]
})
  → Success!
```

#### 4. 테스트 방법

```bash
# 서버 재시작
make run

# 프론트엔드에서 테스트
"PDF 파일을 읽고 질문에 답변하는 RAG 시스템 만들어줘"
→ 이제 FileComponent를 찾아서 플로우를 생성해야 함
```

**주의사항:**
- OpenAI API 키가 설정되어 있어야 함
- 서버 재시작 필수 (코드 변경 반영)

### 문제 1: "OPENAI_API_KEY not set" 에러

**원인:** 환경 변수 미설정

**해결:**

```bash
# .env 파일 확인
cat .env | grep OPENAI_API_KEY

# 환경변수 확인
echo $OPENAI_API_KEY

# .env 파일에 추가
OPENAI_API_KEY=sk-your-key-here

# 서버 재시작 필수!
```

### 문제 2: "Component not found" 에러

**원인:** typesStore에 컴포넌트가 없음

**해결:**
1. typesStore가 로드되었는지 확인
2. component_name 철자 확인
3. 백엔드 /all 엔드포인트 응답 확인
4. 페이지 새로고침

### 문제 3: 엣지가 생성되지 않음

**원인:** Handle을 찾지 못함

**해결:**
1. findComponentOutput 결과 확인
2. findCompatibleInput 결과 확인
3. 컴포넌트의 outputs와 template.input_types 확인
4. 콘솔 로그 확인

### 문제 4: "Failed to generate flow" 에러

**원인:** API 호출 실패

**해결:**
- OpenAI API 키가 유효한지 확인
- OpenAI API 사용량 제한 확인
- 네트워크 연결 확인
- 백엔드 로그 확인: `tail -f logs/langflow.log`

---

## 개발 노트

### 주요 기술적 도전과 해결

#### 1. Langflow의 Handle 시스템

**문제:** React Flow의 handle 시스템이 복잡함

**해결:**
- JSON 객체를 특수 인코딩 (`"` → `œ`)하여 문자열로 변환
- `scapedJSONStringfy()` / `scapeJSONParse()` 함수 쌍 사용
- React Flow의 이스케이핑 문제 회피

```typescript
// 특수 인코딩 예시
const handle = {
  dataType: "ChatInput",
  id: "node-123",
  output_types: ["Message"]
};

// 인코딩: {œdataTypeœ:œChatInputœ,œidœ:œnode-123œ,œoutput_typesœ:[œMessageœ]}
const encoded = scapedJSONStringfy(handle);
```

#### 2. ID 관리

**문제:** 3단계 ID 변환으로 인한 참조 손실

```
백엔드 ID (chat_input)
    ↓
프론트 ID (ChatInput-1762...)
    ↓
paste() ID (ChatInput-abc...)  ← 여기서 참조가 깨짐
```

**해결:** `paste()` 우회, 직접 store 업데이트

```typescript
// paste() 사용 ❌
paste({ nodes, edges }, { x: 100, y: 100 });

// 직접 store 업데이트 ✅
setNodes([...nodes, ...newNodes]);
setEdges([...edges, ...newEdges]);
```

#### 3. 타입 호환성 체크

**문제:** 어떤 출력과 입력을 연결해야 하는지 자동으로 판단

**해결:** 교집합 체크 알고리즘

```typescript
// 간단하지만 효과적
const isCompatible = sourceOutput.types.some(outputType =>
  targetInput.inputTypes.includes(outputType)
);
```

#### 4. 컴포넌트 데이터 간소화

**문제:** 30,000줄의 컴포넌트 데이터를 LLM에 전달하면 토큰 낭비

**해결:** 100배 압축 (500줄 → 5줄)

```python
# LLM이 필요한 정보만 추출
{
  "name": "ChatInput",
  "display_name": "Chat Input",
  "description": "...",
  "input_types": [],
  "output_types": ["Message"]
}
```

### 왜 프론트엔드가 typesStore에서 다시 찾나?

백엔드도 컴포넌트 데이터를 응답에 포함하는데, 왜 프론트엔드가 typesStore에서 다시 찾을까?

**이유:**
1. **데이터 신뢰성**: 프론트엔드의 typesStore가 가장 최신 데이터
2. **일관성**: 앱 전체에서 동일한 컴포넌트 정의 사용
3. **검증**: 백엔드가 잘못된 component_name을 보내면 즉시 에러 발생
4. **타입 안전성**: TypeScript 타입 체크 활용

### 데이터 흐름 요약

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

---

## 향후 계획

### 현재 제한사항 (MVP)

1. **컴포넌트 수**: 2-4개 컴포넌트로 제한된 간단한 플로우
2. **복잡한 연결**: 복잡한 조건부 경로는 미지원
3. **커스텀 컴포넌트**: 기본 컴포넌트만 지원

### Phase 2 (계획)

- [ ] 더 복잡한 플로우 지원 (5-10개 컴포넌트)
- [ ] 컴포넌트 설정 자동화: AI가 프롬프트, 파라미터 값도 설정
- [ ] 레이아웃 개선: 더 지능적인 노드 배치 알고리즘
- [ ] 커스텀 컴포넌트 자동 인식
- [ ] 프롬프트 자동 생성 품질 개선
- [ ] 타입 호환성 검증 강화

### Phase 3 (계획)

- [ ] 다중 플로우: 하나의 프롬프트로 여러 플로우 생성
- [ ] 다중 LLM 지원 (Claude, Gemini)
- [ ] Flow 수정 및 개선 제안
- [ ] 피드백 루프: 사용자가 수정한 내용을 AI에게 전달
- [ ] 한국어 지원 강화: 더 자연스러운 한국어 처리
- [ ] A/B 테스트 및 메트릭

---

## API 레퍼런스

### 엔드포인트

```
POST /api/v1/nl-flow/generate
Content-Type: application/json
Authorization: Bearer <token>

Request Body:
{
  "prompt": "Create a simple chatbot"
}

Response:
{
  "nodes": [
    {
      "id": "ChatInput-1234567890",
      "component_name": "ChatInput",
      "display_name": "Chat Input",
      "position": { "x": 250, "y": 100 },
      "data": { ... }
    }
  ],
  "edges": [
    {
      "source": "ChatInput-1234567890",
      "target": "ChatModel-1234567891",
      "source_handle": null,
      "target_handle": null
    }
  ],
  "explanation": "This flow creates a simple chatbot..."
}
```

---

## 버전 정보

- **작성일**: 2025-11-06
- **Langflow 버전**: 최신
- **작성자**: Claude Code Assistant

---

## 결론

NL to Flow 기능은 다음과 같은 핵심 요소로 구성됩니다:

1. **백엔드**: OpenAI Function Calling으로 컴포넌트 선택 및 플로우 생성
2. **데이터 간소화**: 500줄 → 5줄로 압축해 LLM 효율성 향상
3. **typesStore**: 프론트엔드의 모든 컴포넌트 정보를 담은 중앙 저장소
4. **자동 Handle 생성**: 출력 타입과 입력 타입을 자동으로 매칭
5. **ID 매핑**: 백엔드 ID와 프론트엔드 ID를 분리해 충돌 방지

이 구조 덕분에 사용자는 자연어만으로 복잡한 AI 워크플로우를 빠르게 생성할 수 있습니다! 🎉

