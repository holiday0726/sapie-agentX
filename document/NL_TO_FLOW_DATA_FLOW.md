# Natural Language to Flow - Data Flow Documentation

이 문서는 자연어를 Langflow 플로우로 변환하는 과정의 데이터 흐름과 타입 정의를 설명합니다.

## 전체 데이터 흐름

```
User Input (자연어)
    ↓
Frontend (nlToFlowPanel.tsx)
    ↓
API Request (POST /api/v1/nl-flow/generate)
    ↓
Backend (nl_flow.py + service.py)
    ↓ LLM Function Calling
OpenAI GPT-4
    ↓ 
Backend Response
    ↓
Frontend Processing
    ↓
React Flow 노드/엣지 생성
```

---

## 1. Frontend → Backend: API 요청

### TypeScript 타입 정의

**Request Type**
```typescript
// src/frontend/src/controllers/API/queries/flows/use-post-nl-flow.ts

interface NLToFlowRequest {
  prompt: string;  // 자연어 플로우 설명
}
```

**예제 Request Body**
```json
{
  "prompt": "Create a simple chatbot with memory"
}
```

---

## 2. Backend Processing

### Python 스키마 정의

**Request Schema (Pydantic)**
```python
# src/backend/base/langflow/api/v1/schemas.py

class NLToFlowRequest(BaseModel):
    """Request schema for natural language to flow generation."""

    prompt: str = Field(..., description="Natural language description of the flow to create")
```

### 사용 가능한 컴포넌트 조회

Backend는 요청을 받으면 먼저 사용 가능한 모든 Langflow 컴포넌트를 조회합니다:

```python
# src/backend/base/langflow/api/v1/nl_flow.py

# Get all available components
settings_service = get_settings_service()
all_types = await get_and_cache_all_types_dict(settings_service=settings_service)

# all_types 구조:
# {
#   "category_name": {
#     "component_name": {
#       "display_name": "...",
#       "description": "...",
#       "template": {...},
#       "input_types": [...],
#       "output_types": [...],
#       ...
#     },
#     ...
#   },
#   ...
# }
```

**컴포넌트 데이터 출처**: `langflow.interface.components.get_and_cache_all_types_dict()`
- Langflow의 모든 등록된 컴포넌트 메타데이터를 반환
- 카테고리별로 그룹화됨 (예: "agents", "models", "inputs", "outputs")

### LLM Function Calling

Backend는 OpenAI GPT-4를 사용하여 자연어를 플로우로 변환합니다:

```python
# src/backend/base/langflow/services/nl_flow/service.py

# LLM에 제공되는 함수들:
functions = [
    {
        "name": "search_components",
        "description": "Search for Langflow components by capability or type",
        "parameters": {
            "query": {"type": "string"}
        }
    },
    {
        "name": "create_flow",
        "description": "Create the final flow with nodes and connections",
        "parameters": {
            "nodes": [...],
            "edges": [...],
            "explanation": "..."
        }
    }
]
```

**LLM이 반환하는 create_flow 함수 인자**:
```python
{
    "nodes": [
        {
            "id": "node-1",  # LLM이 생성한 임시 ID
            "component_name": "ChatInput",
            "config": {}  # 옵셔널 설정
        },
        {
            "id": "node-2",
            "component_name": "ChatModel",
            "config": {
                "prompt": "You are a helpful assistant"
            }
        }
    ],
    "edges": [
        {
            "source": "node-1",
            "target": "node-2"
        }
    ],
    "explanation": "This creates a simple chatbot..."
}
```

---

## 3. Backend → Frontend: API 응답

### Python 응답 스키마

```python
# src/backend/base/langflow/api/v1/schemas.py

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

### TypeScript 응답 타입

```typescript
// src/frontend/src/controllers/API/queries/flows/use-post-nl-flow.ts

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

### 예제 Response Body

```json
{
  "nodes": [
    {
      "id": "ChatInput-1234567890",
      "component_name": "ChatInput",
      "display_name": "Chat Input",
      "position": { "x": 250, "y": 100 },
      "data": {
        "description": "Captures user input...",
        "display_name": "Chat Input",
        "template": { ... },
        "output_types": ["Message"],
        "outputs": [
          {
            "name": "message",
            "types": ["Message"],
            "display_name": "Message"
          }
        ],
        "config": {}
      }
    },
    {
      "id": "ChatModel-1234567891",
      "component_name": "ChatModel",
      "display_name": "Chat Model",
      "position": { "x": 250, "y": 300 },
      "data": {
        "description": "Language model...",
        "display_name": "Chat Model",
        "template": { ... },
        "input_types": ["Message"],
        "output_types": ["Message"],
        "config": {
          "prompt": "You are a helpful assistant"
        }
      }
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

## 4. Frontend Processing: React Flow 변환

### React Flow 노드 타입

Frontend는 Backend 응답을 React Flow가 이해할 수 있는 형태로 변환합니다.

```typescript
// src/frontend/src/types/flow/index.ts

// React Flow 노드 타입
export type GenericNodeType = Node<NodeDataType, "genericNode">;
export type NoteNodeType = Node<NoteDataType, "noteNode">;
export type AllNodeType = GenericNodeType | NoteNodeType;

// 노드 데이터 타입
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

### React Flow 엣지 타입

```typescript
// src/frontend/src/types/flow/index.ts

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

### 변환 프로세스 (nlToFlowPanel.tsx)

```typescript
// 1. ID 매핑 생성 (Backend ID → Frontend ID)
const idMapping: Record<string, string> = {};

// 2. 노드 변환
const newNodes = response.nodes.map((node, index) => {
  // Frontend용 새 ID 생성
  const newId = `${node.component_name}-${Date.now()}-${index}`;
  idMapping[node.id] = newId;

  // React Flow 노드 형태로 변환
  return {
    id: newId,
    type: "genericNode",  // 항상 "genericNode"
    position: node.position,
    data: {
      type: node.component_name,     // "ChatInput", "ChatModel" 등
      node: {
        ...componentData,            // TypesStore에서 조회한 전체 메타데이터
        template: {
          ...(componentData.template || {}),
          ...(nodeConfig || {}),     // Backend config 병합
        },
      },
      id: newId,
    },
  };
});

// 3. 엣지 변환 및 핸들 생성
const newEdges = response.edges.map((edge) => {
  const mappedSource = idMapping[edge.source];
  const mappedTarget = idMapping[edge.target];

  // Source 노드의 출력 찾기
  const sourceOutput = findComponentOutput(sourceComponentData);
  // → { name: "message", types: ["Message"] }

  // Target 노드의 호환 가능한 입력 찾기
  const targetInput = findCompatibleInput(targetComponentData, sourceOutput.types);
  // → { fieldName: "input_value", inputTypes: ["Message", "Text"] }

  // sourceHandle 생성
  const sourceHandleObj: sourceHandleType = {
    dataType: sourceNode.data.type,  // "ChatInput"
    id: mappedSource,
    output_types: sourceOutput.types,
    name: sourceOutput.name,
  };

  // targetHandle 생성
  const targetHandleObj: targetHandleType = {
    type: targetComponentData.template[targetInput.fieldName]?.type,
    fieldName: targetInput.fieldName,
    id: mappedTarget,
    inputTypes: targetInput.inputTypes,
  };

  // 핸들을 JSON 문자열로 인코딩 (React Flow의 handle ID로 사용)
  const sourceHandle = scapedJSONStringfy(sourceHandleObj);
  const targetHandle = scapedJSONStringfy(targetHandleObj);

  return {
    id: `edge-${Date.now()}-${index}`,
    source: mappedSource,
    target: mappedTarget,
    sourceHandle,      // JSON 문자열
    targetHandle,      // JSON 문자열
    type: "default",
    data: {
      sourceHandle: sourceHandleObj,  // 원본 객체
      targetHandle: targetHandleObj,  // 원본 객체
    },
  };
});

// 4. Flow Store에 추가
setNodes([...nodes, ...newNodes.map(n => ({ ...n, selected: true }))] as any);
setEdges([...edges, ...newEdges] as any);
```

---

## 5. 핵심 Helper 함수

### findComponentOutput

```typescript
/**
 * 컴포넌트의 첫 번째 출력을 찾는 함수
 *
 * @param componentData - APIClassType (컴포넌트 메타데이터)
 * @returns { name: string, types: string[] } | null
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
```

### findCompatibleInput

```typescript
/**
 * 컴포넌트에서 호환 가능한 입력 필드를 찾는 함수
 *
 * @param componentData - APIClassType (컴포넌트 메타데이터)
 * @param sourceOutputTypes - 소스 출력 타입들
 * @returns { fieldName: string, inputTypes: string[] } | null
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
```

---

## 6. 타입 정의 요약

### APIClassType (컴포넌트 메타데이터)

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

### InputFieldType (입력 필드 정의)

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

### OutputFieldType (출력 필드 정의)

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

---

## 7. 데이터 흐름 다이어그램

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

---

## 8. 주요 제약사항 및 주의사항

### Backend

1. **컴포넌트 조회**: `get_and_cache_all_types_dict()`로 모든 컴포넌트를 조회해야 함
2. **LLM 의존성**: OpenAI API 키 필요 (`OPENAI_API_KEY` 환경변수)
3. **Function Calling**: GPT-4-turbo 이상 모델 필요
4. **핸들 생성 안함**: Backend는 source_handle/target_handle을 생성하지 않음 (null)

### Frontend

1. **ID 재생성**: Backend ID → Frontend ID 매핑 필수
2. **TypesStore 의존**: 컴포넌트 메타데이터를 TypesStore에서 조회
3. **핸들 생성**: 출력/입력 호환성 체크 후 핸들 생성
4. **타입 단언**: React Flow 타입 호환을 위해 `as any` 사용
5. **JSON 인코딩**: 핸들 객체를 JSON 문자열로 인코딩하여 handle ID로 사용

---

## 9. 확장 가능성

### 백엔드 개선

- [ ] 더 정교한 컴포넌트 검색 (임베딩 기반 검색)
- [ ] 노드 위치 자동 최적화 (레이아웃 알고리즘)
- [ ] Edge 핸들 자동 생성
- [ ] 다양한 LLM 지원 (Claude, Gemini 등)

### 프론트엔드 개선

- [ ] 생성 진행 상황 표시 (스트리밍)
- [ ] 생성된 플로우 미리보기
- [ ] 사용자 피드백 및 재생성
- [ ] 예제 프롬프트 제공
- [ ] 플로우 템플릿 저장

---

## 10. 참고 파일

### Backend
- `src/backend/base/langflow/api/v1/nl_flow.py` - API 엔드포인트
- `src/backend/base/langflow/services/nl_flow/service.py` - LLM Function Calling 로직
- `src/backend/base/langflow/api/v1/schemas.py` - 요청/응답 스키마
- `src/backend/base/langflow/interface/components/__init__.py` - 컴포넌트 조회

### Frontend
- `src/frontend/src/pages/FlowPage/components/flowSidebarComponent/components/nlToFlowPanel.tsx` - UI 및 변환 로직
- `src/frontend/src/controllers/API/queries/flows/use-post-nl-flow.ts` - API 호출
- `src/frontend/src/types/api/index.ts` - API 타입 정의
- `src/frontend/src/types/flow/index.ts` - Flow 타입 정의
- `src/frontend/src/utils/reactflowUtils.ts` - scapedJSONStringfy 함수

---

## 버전 정보

- **작성일**: 2025-11-06
- **Langflow 버전**: 최신
- **작성자**: Claude Code Assistant
