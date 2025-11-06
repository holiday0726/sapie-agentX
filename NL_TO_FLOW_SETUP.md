# Natural Language to Flow - Setup Guide

## 개요
자연어 입력을 통해 Langflow 플로우를 자동으로 생성하는 기능입니다. OpenAI GPT-4의 Function Calling을 활용합니다.

## 설정 방법

### 1. OpenAI API 키 설정

`.env` 파일에 다음을 추가하세요:

```bash
# Natural Language to Flow - OpenAI API Key
OPENAI_API_KEY=sk-your-api-key-here
```

또는 환경 변수로 설정:

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

### 2. openai 패키지 설치

백엔드에 openai 패키지가 필요합니다:

```bash
cd src/backend/base
pip install openai
```

### 3. 서버 재시작

변경사항을 적용하기 위해 Langflow 서버를 재시작하세요:

```bash
# 개발 환경
langflow run

# 또는 프로덕션 환경
# 적절한 프로덕션 명령어 사용
```

## 사용 방법

### 사이드바에서

1. 플로우 편집 페이지의 왼쪽 사이드바에서 "AI Flow Builder" 섹션을 찾습니다
2. 텍스트 입력창에 플로우 설명을 입력합니다
   - 예: "Create a simple chatbot with memory"
   - 예: "Build a document Q&A system"
3. "플로우 생성" 버튼을 클릭합니다
4. 생성된 플로우가 캔버스에 자동으로 추가됩니다

### 예제 프롬프트

```
✅ "Create a chatbot with memory"
→ ChatInput → ChatModel → ChatOutput + Memory

✅ "Build a document Q&A system"
→ DocumentLoader → TextSplitter → VectorStore → ChatModel

✅ "Make a sentiment analysis flow"
→ TextInput → SentimentAnalysis → TextOutput

✅ "Create a text summarization pipeline"
→ TextInput → Summarizer → TextOutput
```

## API 엔드포인트

백엔드에 다음 엔드포인트가 추가되었습니다:

```
POST /api/v1/nl-flow/generate
Content-Type: application/json

{
  "prompt": "Create a simple chatbot"
}
```

**응답:**

```json
{
  "nodes": [
    {
      "component_name": "ChatInput",
      "display_name": "Chat Input",
      "position": { "x": 250, "y": 100 },
      "data": { ... }
    },
    ...
  ],
  "edges": [
    {
      "source": "ChatInput-...",
      "target": "ChatModel-...",
      "source_handle": null,
      "target_handle": null
    },
    ...
  ],
  "explanation": "This flow creates a simple chatbot..."
}
```

## 구현 세부사항

### 백엔드

**파일:**
- `src/backend/base/langflow/api/v1/nl_flow.py` - FastAPI 엔드포인트
- `src/backend/base/langflow/services/nl_flow/service.py` - LLM Function Calling 로직
- `src/backend/base/langflow/api/v1/schemas.py` - 요청/응답 스키마

**주요 기능:**
- OpenAI GPT-4 Function Calling
- 컴포넌트 검색 함수
- Flow 구조 생성 및 검증
- 타입 호환성 체크

### 프론트엔드

**파일:**
- `src/frontend/src/pages/FlowPage/components/flowSidebarComponent/components/nlToFlowPanel.tsx` - UI 컴포넌트
- `src/frontend/src/controllers/API/queries/flows/use-post-nl-flow.ts` - API 훅

**주요 기능:**
- 자연어 입력 UI
- API 호출 및 에러 처리
- 응답 데이터를 React Flow 형식으로 변환
- 캔버스에 노드/엣지 추가

## 제한사항 (MVP)

현재 MVP 버전의 제한사항:

1. **컴포넌트 수**: 2-4개 컴포넌트로 제한된 간단한 플로우
2. **복잡한 연결**: 복잡한 조건부 경로는 미지원
3. **커스텀 컴포넌트**: 기본 컴포넌트만 지원 (커스텀 컴포넌트는 다음 버전에서)
4. **프롬프트 최적화**: 더 복잡한 프롬프트 생성은 추후 개선 예정
5. **자동 연결**: 엣지 자동 연결 기능은 개발 중 (현재는 노드만 생성되며 수동 연결 필요)

---

## 🔥 개발일기: AI Flow Builder 구현기

처절한 디버깅과 깨달음의 기록...

---

### 📅 Day 1: "자연어로 플로우를 만들겠어!"

**오전 10:00 - 야심찬 시작**

오늘은 자연어로 Langflow 플로우를 자동 생성하는 기능을 만들기로 했다.
"간단한 챗봇 만들어줘" 라고 입력하면 → ChatInput, ChatModel, ChatOutput이 자동으로 생성되고 연결까지!

계획:
1. 백엔드: OpenAI Function Calling으로 자연어 → 컴포넌트 변환
2. 프론트엔드: 사이드바에 입력창 만들고, 생성된 플로우를 캔버스에 추가

간단할 줄 알았지... 🤔

---

**오후 2:00 - 백엔드 구현 시작**

먼저 백엔드부터 만들자. FastAPI 엔드포인트와 OpenAI Function Calling 로직.

`nl_flow.py` 파일 생성:
```python
@router.post("/generate", response_model=NLToFlowResponse)
async def generate_flow_from_nl(
    request: NLToFlowRequest,
    current_user: User = Depends(get_current_active_user),
) -> NLToFlowResponse:
    # 사용 가능한 모든 컴포넌트 가져오기
    all_types = await get_and_cache_all_types_dict(settings_service=settings_service)

    # NL → Flow 변환
    nl_service = NLFlowService()
    flow_data = await nl_service.generate_flow(
        prompt=request.prompt,
        available_components=all_types
    )

    return NLToFlowResponse(**flow_data)
```

핵심은 `NLFlowService`다. OpenAI GPT-4에게 두 가지 함수를 제공:

1. **search_components**: "ChatModel 찾아줘" 하면 관련 컴포넌트 검색
2. **create_flow**: 최종적으로 노드와 엣지를 생성

```python
functions = [
    {
        "name": "search_components",
        "description": "Search for Langflow components by capability or type",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            }
        }
    },
    {
        "name": "create_flow",
        "description": "Create the final flow with nodes and connections",
        "parameters": {
            "type": "object",
            "properties": {
                "nodes": {"type": "array", ...},
                "edges": {"type": "array", ...},
                "explanation": {"type": "string"}
            }
        }
    }
]
```

GPT-4가 이 함수들을 사용해서 스스로 컴포넌트를 찾고, 플로우를 구성한다!

**Function Calling 반복 과정**:
```
Iteration 1: LLM이 search_components("ChatInput") 호출
Iteration 2: LLM이 search_components("ChatModel") 호출
Iteration 3: LLM이 search_components("ChatOutput") 호출
Iteration 4: LLM이 create_flow([ChatInput, ChatModel, ChatOutput]) 호출
```

오 이거 작동하네? 로그 보니까 제대로 함수 호출하고 있어!

---

**오후 4:00 - 스키마 정의**

응답 형식을 정의해야지. `schemas.py`에 추가:

```python
class NLToFlowRequest(BaseModel):
    prompt: str = Field(..., description="자연어 플로우 설명")

class FlowNodeData(BaseModel):
    id: str
    component_name: str
    display_name: str | None = None
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0})
    data: dict[str, Any] = Field(default_factory=dict)

class FlowEdgeData(BaseModel):
    source: str
    target: str
    source_handle: str | None = None
    target_handle: str | None = None

class NLToFlowResponse(BaseModel):
    nodes: list[FlowNodeData]
    edges: list[FlowEdgeData]
    explanation: str | None = None
```

백엔드는 이제 끝! 이제 프론트로...

---

**오후 5:30 - 프론트엔드: API 훅 만들기**

백엔드 API를 호출할 훅이 필요하다. `use-post-nl-flow.ts` 생성:

```typescript
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
      `${getURL("NL_FLOW")}/generate`,
      payload
    );
    return response.data;
  };

  return mutate(["usePostNLFlow"], postNLFlowFn, options);
};
```

`constants.ts`에 URL도 추가:
```typescript
NL_FLOW: 'nl-flow'
```

---

**오후 7:00 - UI 컴포넌트 구현**

사이드바에 AI Flow Builder 패널을 만들자. `nlToFlowPanel.tsx`:

```typescript
export default function NlToFlowPanel() {
  const [prompt, setPrompt] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  const data = useTypesStore((state) => state.data);
  const paste = useFlowStore((state) => state.paste);
  const { mutate: generateFlow } = usePostNLFlow();

  const handleGenerate = () => {
    if (!prompt.trim()) return;
    setIsGenerating(true);

    generateFlow(
      { prompt: prompt.trim() },
      {
        onSuccess: (response) => {
          // 백엔드 응답을 React Flow 형식으로 변환
          const nodes = response.nodes.map((node, index) => {
            // 컴포넌트 데이터 찾기
            let componentData: APIClassType | undefined;
            for (const category in data) {
              if (data[category][node.component_name]) {
                componentData = data[category][node.component_name];
                break;
              }
            }

            return {
              id: `${node.component_name}-${Date.now()}-${index}`,
              type: "genericNode",
              position: node.position,
              data: {
                type: node.component_name,
                node: componentData,
                id: newId,
              },
            };
          });

          // 일단 노드만 추가 (edges는 나중에...)
          paste({ nodes, edges: [] }, { x: 100, y: 100 });

          setSuccessData({
            title: "노드가 생성되었습니다. 수동으로 연결해주세요."
          });
        },
        onError: (error) => {
          setErrorData({
            title: "플로우 생성 실패",
            list: [error?.response?.data?.detail || "에러 발생"]
          });
        }
      }
    );
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <ForwardedIconComponent name="sparkles" />
        <span>AI Flow Builder</span>
      </div>

      <Textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="예: 간단한 챗봇 만들어줘"
      />

      <Button onClick={handleGenerate} disabled={isGenerating}>
        {isGenerating ? "생성 중..." : "플로우 생성"}
      </Button>
    </div>
  );
}
```

---

**오후 8:00 - 첫 테스트**

`.env` 파일에 OpenAI API 키 추가:
```bash
OPENAI_API_KEY=sk-...
```

서버 재시작하고... 테스트!

"간단한 챗봇 만들어줘" 입력 → 생성 버튼 클릭

**결과**:
```
❌ OPENAI_API_KEY environment variable not set
```

뭐야? 분명 .env에 넣었는데? 😱

아... 서버 실행 중에 .env 수정했구나. 서버 재시작!

다시 시도 → **성공!** 🎉

백엔드 로그:
```
Iteration 1: Calling function search_components with args: {'query': 'ChatInput'}
Iteration 2: Calling function search_components with args: {'query': 'ChatModel'}
Iteration 3: Calling function search_components with args: {'query': 'ChatOutput'}
Iteration 4: Calling function create_flow with args: {...}
```

프론트엔드에서 3개 노드가 캔버스에 생성됨!

✅ **Day 1 결과**: 노드 생성은 성공! 하지만 연결은 수동으로 해야 함.

MVP는 완성했다. 하지만... 자동으로 연결까지 되면 더 좋지 않을까? 🤔

---

### 📅 Day 2: "자동 연결을 구현하자!"

**오전 9:00 - 엣지 자동 생성 시도**

어제는 노드만 만들었으니, 오늘은 엣지를 자동으로 연결해보자!

백엔드는 이미 edges를 반환하고 있어:
```json
{
  "edges": [
    {"source": "chat_input", "target": "chat_model"},
    {"source": "chat_model", "target": "chat_output"}
  ]
}
```

이걸 그대로 `paste()`에 넘기면 되겠지?

```typescript
// edges도 같이 전달
paste({ nodes, edges }, { x: 100, y: 100 });
```

테스트 → 💥 **에러!**

```
TypeError: Cannot read properties of null (reading 'replace')
    at scapeJSONParse (reactflowUtils.ts:1074)
    at flowStore.ts:509
```

뭐지 이거...? 😨

---

**오전 10:30 - 에러 추적 시작**

`flowStore.ts:509` 코드를 봤다:
```typescript
const sourceHandleObject: sourceHandleType = scapeJSONParse(
  edge.sourceHandle!,  // ← 여기서 터짐
);
```

아... `sourceHandle`이 `null`이구나. `scapeJSONParse()` 함수가 null에서 `.replace()`를 호출하려다 죽은 거야.

그런데 `scapeJSONParse`가 뭔데? 코드를 봤다:

```typescript
export function scapedJSONStringfy(json: object): string {
  return customStringify(json).replace(/"/g, "œ");  // " → œ 변환
}

export function scapeJSONParse(json: string): any {
  const parsed = json.replace(/œ/g, '"');  // œ → " 변환
  return JSON.parse(parsed);
}
```

오... Langflow는 특수한 인코딩 방식을 쓰네?!
- JSON 문자열의 따옴표(`"`)를 특수 문자(`œ`)로 치환
- React Flow의 문자열 이스케이핑 문제를 회피하기 위한 트릭인 것 같아

그럼 우리도 `sourceHandle`과 `targetHandle`을 이 형식으로 만들어야 한다는 거잖아?

근데... 이게 어떤 형식이어야 하는지 모르겠는데? 😵

---

**오후 12:00 - Handle 구조 파악**

`types/flow/index.ts` 파일을 뒤져서 타입 정의를 찾았다:

```typescript
// 출력 쪽 (오른쪽 포트)
export type sourceHandleType = {
  baseClasses?: string[];
  dataType: string;           // 필수!
  id: string;                 // 필수! 노드 ID
  output_types: string[];     // 필수!
  conditionalPath?: string | null;
  name: string;               // 필수! 출력 필드 이름
};

// 입력 쪽 (왼쪽 포트)
export type targetHandleType = {
  inputTypes?: string[];
  output_types?: string[];
  type: string;               // 필수!
  fieldName: string;          // 필수! 입력 필드 이름
  name?: string;
  id: string;                 // 필수! 노드 ID
  proxy?: { field: string; id: string };
};
```

오케이, 이제 뭘 넣어야 하는지 알겠어. 그런데...

- `dataType`은 뭘 넣지?
- `output_types`는 어디서 가져오지?
- `name`은? `fieldName`은?

컴포넌트 데이터를 보면 알 수 있을까? 😰

---

**오후 2:00 - 컴포넌트 메타데이터 분석**

`APIClassType` 구조를 파헤쳤다:

```typescript
type APIClassType = {
  outputs?: Array<OutputFieldType>;  // 출력 정의!
  template: APITemplateType;         // 입력 정의!
  output_types?: Array<string>;
  display_name: string;
  // ...
};

type OutputFieldType = {
  name: string;         // 출력 필드 이름
  types: Array<string>; // 출력 타입들
  display_name: string;
  hidden?: boolean;
};

// template은 Dictionary<string, InputFieldType>
type InputFieldType = {
  input_types?: Array<string>;  // 입력이 받을 수 있는 타입들!
  type: string;
  show?: boolean;
  advanced?: boolean;
};
```

아하! 이제 보이기 시작해!

**ChatInput** 컴포넌트를 예로 들면:
- `outputs[0].name = "message"`
- `outputs[0].types = ["Message"]`

**ChatModel** 컴포넌트는:
- `template`에 여러 입력 필드가 있는데
- 그 중 `input_types`에 `["Message"]`가 있는 필드를 찾으면 됨!

타입이 일치하는 출력→입력을 연결하면 되는 거야! 💡

---

**오후 4:00 - Helper 함수 작성**

컴포넌트에서 출력/입력을 찾는 함수들을 만들었다:

```typescript
// 출력 찾기
function findComponentOutput(componentData: APIClassType) {
  if (!componentData.outputs || componentData.outputs.length === 0) {
    // Fallback: output_types 사용
    if (componentData.output_types) {
      return { name: "output", types: componentData.output_types };
    }
    return null;
  }

  // 첫 번째 non-hidden 출력
  const output = componentData.outputs.find(o => !o.hidden)
    || componentData.outputs[0];

  return { name: output.name, types: output.types };
}

// 호환되는 입력 찾기
function findCompatibleInput(componentData: APIClassType, sourceOutputTypes: string[]) {
  const template = componentData.template;
  if (!template) return null;

  // 타입 호환되는 입력 필드 찾기
  for (const [fieldName, field] of Object.entries(template)) {
    const fieldTyped = field as InputFieldType;

    // advanced/hidden 필드 제외
    if (fieldTyped.advanced || fieldTyped.show === false) continue;

    const inputTypes = fieldTyped.input_types || [];
    if (inputTypes.length === 0) continue;

    // 교집합 확인!
    const isCompatible = sourceOutputTypes.some(outputType =>
      inputTypes.includes(outputType)
    );

    if (isCompatible) {
      return { fieldName, inputTypes };
    }
  }

  // Fallback: 첫 번째 입력
  for (const [fieldName, field] of Object.entries(template)) {
    if (field.input_types?.length > 0) {
      return { fieldName, inputTypes: field.input_types };
    }
  }

  return null;
}
```

좋아, 이제 각 엣지마다 이 함수들을 써서 Handle 객체를 만들면 돼!

---

**오후 6:00 - Edge 생성 로직 구현**

`nlToFlowPanel.tsx`의 edge 처리 부분을 대폭 수정:

```typescript
// ID 매핑 생성 (백엔드 ID → 프론트 ID)
const idMapping: Record<string, string> = {};

const newNodes = response.nodes.map((node, index) => {
  const newId = `${node.component_name}-${Date.now()}-${index}`;
  idMapping[node.id] = newId;  // "chat_input" → "ChatInput-1762..."

  // ... 노드 생성
});

// 노드 맵 생성 (빠른 조회용)
const nodeMap = new Map(newNodes.map(n => [n.id, n]));

// Edge 생성!
const newEdges = response.edges.map((edge, index) => {
  const mappedSource = idMapping[edge.source];
  const mappedTarget = idMapping[edge.target];

  const sourceNode = nodeMap.get(mappedSource);
  const targetNode = nodeMap.get(mappedTarget);

  // 1. 소스 출력 찾기
  const sourceOutput = findComponentOutput(sourceNode.data.node);
  if (!sourceOutput) return null;

  // 2. 타겟 호환 입력 찾기
  const targetInput = findCompatibleInput(
    targetNode.data.node,
    sourceOutput.types
  );
  if (!targetInput) return null;

  // 3. sourceHandle 객체 생성
  const sourceHandleObj: sourceHandleType = {
    dataType: sourceNode.data.node.display_name,
    id: mappedSource,
    output_types: sourceOutput.types,
    name: sourceOutput.name,
  };

  // 4. targetHandle 객체 생성
  const targetHandleObj: targetHandleType = {
    type: targetNode.data.node.display_name,
    fieldName: targetInput.fieldName,
    id: mappedTarget,
    inputTypes: targetInput.inputTypes,
  };

  // 5. scapedJSONStringfy로 인코딩!
  const sourceHandle = scapedJSONStringfy(sourceHandleObj);
  const targetHandle = scapedJSONStringfy(targetHandleObj);

  console.log("Generated handles:", { sourceHandle, targetHandle });

  return {
    id: `edge-${Date.now()}-${index}`,
    source: mappedSource,
    target: mappedTarget,
    sourceHandle,  // œ로 인코딩된 JSON 문자열
    targetHandle,  // œ로 인코딩된 JSON 문자열
    type: "default",
    data: {
      sourceHandle: sourceHandleObj,
      targetHandle: targetHandleObj,
    },
  };
}).filter(edge => edge !== null);
```

완벽해! 이제 테스트해보자!

---

**오후 7:00 - 테스트... 그리고 실망**

"간단한 챗봇 만들어줘" 다시 입력!

콘솔 로그:
```javascript
🔵 Generated handles: {
  sourceHandle: '{œdataTypeœ:œChat Inputœ,œidœ:œChatInput-1762...œ,œnameœ:œmessageœ,œoutput_typesœ:[œMessageœ]}',
  targetHandle: '{œfieldNameœ:œendpointœ,œidœ:œBaiduQianfan...œ,œinputTypesœ:[œMessageœ],œtypeœ:œQianfanœ}'
}
```

오! Handle 생성은 완벽해! 😍

근데... **노드는 생성됐는데 엣지가 안 보여**. 😱

왜지? 왜지?!?!?!

디버깅 모드로 `paste()` 함수를 추적해봤다...

---

**오후 9:00 - 범인을 찾았다!**

`flowStore.ts`의 `paste()` 함수를 자세히 봤더니...

```typescript
paste: (selection, position) => {
  const idsMap = {};

  selection.nodes.forEach((node: AllNodeType) => {
    const newId = getNodeId(node.data.type);  // ⚠️ 새 ID 또 생성!
    idsMap[node.id] = newId;  // 우리 ID → paste의 새 ID
    // ...
  });

  selection.edges.forEach((edge: EdgeType) => {
    const source = idsMap[edge.source];  // ⚠️ 조회
    const target = idsMap[edge.target];  // ⚠️ undefined!
    // ...
  });
}
```

**문제 발견!**

1. 우리가 이미 고유 ID를 만듦: `ChatInput-1762393207203-0`
2. Edge의 source/target에 이 ID 사용
3. `paste()`가 **또 다른 새 ID를 생성**: `ChatInput-abc123`
4. `idsMap`은 `paste()`가 만든 ID 기준으로 매핑
5. 근데 Edge의 source/target은 우리가 만든 ID...
6. `idsMap`에서 찾으면 → **undefined!** 😭

ID가 3단계로 변환되면서 참조가 꼬인 거야:
- 백엔드 ID (`chat_input`)
- 우리 프론트 ID (`ChatInput-1762...`)
- paste()의 최종 ID (`ChatInput-abc...`)

멘붕...

---

### 📅 Day 3: "paste()를 포기하다"

**오전 10:00 - 새로운 접근**

`paste()` 함수가 ID를 재생성하는 게 문제라면... paste를 쓰지 말자!

직접 `setNodes()`와 `setEdges()`로 store를 업데이트하면 되잖아?

```typescript
const nodes = useFlowStore((state) => state.nodes);
const edges = useFlowStore((state) => state.edges);
const setNodes = useFlowStore((state) => state.setNodes);
const setEdges = useFlowStore((state) => state.setEdges);

// ...

// 직접 추가!
setNodes([...nodes, ...newNodes.map(n => ({ ...n, selected: true }))]);
setEdges([...edges, ...newEdges]);
```

이렇게 하면 우리가 만든 ID가 그대로 유지될 거야!

---

**오전 11:00 - 테스트... 또 실패**

다시 테스트!

```
✅ 노드 3개 생성됨
✅ Handle 생성 로그 정상
✅ setEdges 호출됨
❌ 캔버스에 엣지 안 보임
```

뭐야... 왜...? 😩

콘솔에 TypeScript 에러가 떠 있어:
```
[TypeScript] 'string' 형식은 '"default"' 형식에 할당할 수 없습니다.
```

아... `type: "default"` 부분 때문인가?

---

**오후 12:00 - 현재 상태**

3일째 디버깅 중...

**작동하는 것**:
- ✅ 자연어 입력 UI
- ✅ GPT-4 Function Calling
- ✅ 노드 생성 및 배치
- ✅ Handle 객체 생성 (형식 완벽)
- ✅ 타입 호환성 체크

**작동 안 하는 것**:
- ❌ 엣지가 캔버스에 표시 안 됨

로그를 보면 모든 게 정상인데, 왜 화면에 안 그려지는 걸까?

---

**오후 2:00 - 임시 해결책**

일단 MVP로 릴리즈하기로 결정.

노드는 자동 생성되고, 사용자가 드래그로 연결하면 되니까... 😅

나중에 시간 날 때 다시 도전해봐야지.

**다음 시도할 것들**:
1. TypeScript 타입 에러 수정 (`type: "default" as const`)
2. React Flow의 edge validation 로직 확인
3. `onConnect()` 함수 직접 호출 시도
4. Langflow의 다른 edge 생성 코드 참고

---

### 🤔 회고 및 배운 것들

#### Langflow의 Handle 시스템은 복잡하다

1. **특수 인코딩**:
   - JSON에서 `"`를 `œ`로 치환
   - React Flow의 이스케이핑 문제 회피
   - `scapedJSONStringfy()` / `scapeJSONParse()` 함수 쌍

2. **양방향 참조**:
   - Handle 객체가 노드 ID를 포함
   - Source와 Target 양쪽에서 참조 가능

3. **타입 시스템**:
   - `output_types` ∩ `input_types` 체크
   - 동적 타입 호환성 검증

#### ID 관리는 어렵다

3단계 ID 변환이 문제의 근원:
1. 백엔드: LLM이 생성 (`chat_input`)
2. 프론트: 고유 ID 생성 (`ChatInput-1762...`)
3. paste(): 또 다른 ID 생성 (`ChatInput-abc...`)

해결책: paste() 우회, 직접 store 업데이트

#### 타입 호환성 알고리즘

```typescript
// 간단하지만 효과적
const isCompatible = sourceOutput.types.some(outputType =>
  targetInput.inputTypes.includes(outputType)
);
```

교집합만 확인하면 끝!

---

### 📊 최종 상태

**구현 완료**:
- ✅ 자연어 → 노드 자동 생성
- ✅ OpenAI Function Calling 통합
- ✅ 컴포넌트 검색 및 선택
- ✅ Handle 객체 생성 로직
- ✅ 타입 호환성 체크

**미완성** (TODO):
- ❌ 자동 엣지 연결 (노드만 생성, 수동 연결)

**임시 워크어라운드**:
```
사용자가 생성된 노드를 드래그해서 수동으로 연결
```

**언젠가 해결할 것들**:
1. TypeScript 타입 에러 해결
2. Edge가 store에 추가되지만 렌더링 안 되는 이유 파악
3. React Flow 내부 validation 로직 분석
4. 대안적 edge 추가 방법 시도

---

그래도... 노드 자동 생성은 성공했으니 반은 성공이지! 🎉

다음에 다시 도전해보자... 💪

---

## 트러블슈팅

### "OPENAI_API_KEY not set" 오류

```bash
# .env 파일 확인
cat .env | grep OPENAI_API_KEY

# 환경변수 확인
echo $OPENAI_API_KEY

# 서버 재시작 필요
```

### "Component not found" 오류

- 컴포넌트 타입 캐시를 새로고침하세요
- 사이드바에서 컴포넌트 목록이 제대로 로드되었는지 확인하세요

### "Failed to generate flow" 오류

- OpenAI API 키가 유효한지 확인
- OpenAI API 사용량 제한 확인
- 네트워크 연결 확인
- 백엔드 로그 확인: `tail -f logs/langflow.log`

## 향후 개선 사항

### Phase 2 (예정)
- [ ] 더 복잡한 플로우 지원 (5-10개 컴포넌트)
- [ ] 커스텀 컴포넌트 자동 인식
- [ ] 프롬프트 자동 생성 품질 개선
- [ ] 타입 호환성 검증 강화

### Phase 3 (예정)
- [ ] 다중 LLM 지원 (Claude, Gemini)
- [ ] Flow 수정 및 개선 제안
- [ ] 사용자 피드백 루프
- [ ] A/B 테스트 및 메트릭

## 문의

문제가 발생하거나 개선 제안이 있으시면 이슈를 생성해주세요.
