# Langfuse 트레이싱 완벽 가이드

Langflow에서 Langfuse를 사용한 LLM 실행 추적(Tracing) 시스템의 전체 구조와 작동 방식을 설명합니다.

---

## 목차

1. [개요](#1-개요)
2. [환경 설정](#2-환경-설정)
3. [전체 아키텍처](#3-전체-아키텍처)
4. [데이터 흐름](#4-데이터-흐름)
5. [Backend 상세](#5-backend-상세)
6. [Frontend 상세](#6-frontend-상세)
7. [API 엔드포인트](#7-api-엔드포인트)
8. [사용 예제](#8-사용-예제)
9. [문제 해결](#9-문제-해결)

---

## 1. 개요

### Langfuse란?

Langfuse는 LLM 애플리케이션의 실행 과정을 추적하고 모니터링하는 오픈소스 플랫폼입니다.

### Langflow의 Langfuse 통합

Langflow는 플로우 실행 시 각 컴포넌트의:
- **입력/출력 데이터**
- **실행 시간**
- **비용(Cost)**
- **메타데이터**

를 자동으로 Langfuse에 기록하고, UI에서 실시간으로 확인할 수 있습니다.

### 주요 기능

- ✅ 플로우 실행 추적 (Trace)
- ✅ 컴포넌트별 Span 생성
- ✅ 실시간 트레이스 목록 조회
- ✅ 상세 트레이스 정보 (Input/Output/Metadata)
- ✅ 비용(Cost) 추적
- ✅ 실행 시간(Duration) 측정
- ✅ 연결 상태 자동 확인

---

## 2. 환경 설정

### 필수 환경 변수

Langfuse 트레이싱을 사용하려면 다음 환경 변수를 설정해야 합니다:

```bash
# Langfuse 인증 정보
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 환경 변수 설정 방법

#### 1. `.env` 파일 사용

```bash
# 프로젝트 루트에 .env 파일 생성
echo "LANGFUSE_SECRET_KEY=sk-lf-..." >> .env
echo "LANGFUSE_PUBLIC_KEY=pk-lf-..." >> .env
echo "LANGFUSE_HOST=https://cloud.langfuse.com" >> .env
```

#### 2. 시스템 환경 변수 설정

```bash
export LANGFUSE_SECRET_KEY=sk-lf-...
export LANGFUSE_PUBLIC_KEY=pk-lf-...
export LANGFUSE_HOST=https://cloud.langfuse.com
```

#### 3. Langflow 실행 시 지정

```bash
langflow run --env-file .env
```

### Langfuse 계정 생성

1. [https://cloud.langfuse.com](https://cloud.langfuse.com) 접속
2. 계정 생성 및 프로젝트 생성
3. Settings → API Keys에서 키 발급
4. Public Key와 Secret Key를 복사하여 환경 변수에 설정

---

## 3. 전체 아키텍처

### 시스템 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                         Langflow                                │
│                                                                 │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │   Frontend UI    │◄────────────►│  Backend API     │        │
│  │  (React Panel)   │   REST API   │  (FastAPI)       │        │
│  └──────────────────┘              └────────┬─────────┘        │
│                                              │                  │
│                                              ▼                  │
│                                    ┌──────────────────┐        │
│                                    │  Tracing Service │        │
│                                    │  (LangFuseTracer)│        │
│                                    └────────┬─────────┘        │
└─────────────────────────────────────────────┼──────────────────┘
                                              │
                                              ▼
                                    ┌──────────────────┐
                                    │    Langfuse      │
                                    │  Cloud/Self-Host │
                                    └──────────────────┘
```

### 주요 컴포넌트

1. **Frontend Panel** (`langfuseTracingPanel.tsx`)
   - 사이드바 UI 패널
   - 연결 상태 표시
   - 트레이스 목록 표시
   - 상세 정보 모달

2. **Backend API** (`api/v1/langfuse.py`)
   - `/langfuse/status`: 연결 상태 확인
   - `/langfuse/traces`: 트레이스 목록 조회
   - `/langfuse/traces/{trace_id}`: 상세 정보 조회

3. **Tracing Service** (`services/tracing/langfuse.py`)
   - 플로우 실행 시 자동 트레이싱
   - Span 생성 및 관리
   - Langfuse SDK 통합

---

## 4. 데이터 흐름

### 전체 플로우

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 사용자가 플로우 실행                                            │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. TracingService 시작                                           │
│    - Trace 생성 (Flow 단위)                                      │
│    - LangFuseTracer 초기화                                       │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. 각 컴포넌트 실행 시                                            │
│    - add_trace(): Span 생성 + Input 기록                        │
│    - 컴포넌트 실행                                                │
│    - end_trace(): Output 기록 + Span 종료                        │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Langfuse로 데이터 전송                                         │
│    - Trace, Span, Input/Output, Cost, Metadata                 │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Frontend에서 조회                                              │
│    - GET /langfuse/traces → 목록 표시                            │
│    - GET /langfuse/traces/{id} → 상세 정보 표시                 │
└─────────────────────────────────────────────────────────────────┘
```

### 트레이싱 라이프사이클

```python
# 1. 플로우 시작
TracingService.start_tracers(
    run_id=UUID,
    run_name="Flow Name",
    user_id="user123",
    session_id="session456"
)
  ↓
# 2. Trace 생성
LangFuseTracer.__init__()
  ↓
# 3. 컴포넌트 실행
for component in flow:
    LangFuseTracer.add_trace(
        trace_id=component.id,
        trace_name=component.name,
        inputs={...}
    )
    # 컴포넌트 실행
    result = component.execute()
    
    LangFuseTracer.end_trace(
        trace_id=component.id,
        outputs=result
    )
  ↓
# 4. 플로우 종료
LangFuseTracer.end(
    inputs=flow_inputs,
    outputs=flow_outputs
)
```

---

## 5. Backend 상세

### 5.1 Tracing Service

**파일**: `src/backend/base/langflow/services/tracing/langfuse.py`

#### LangFuseTracer 클래스

```python
class LangFuseTracer(BaseTracer):
    """Langfuse 트레이서 구현"""
    
    def __init__(self, trace_name, trace_type, project_name, 
                 trace_id, user_id=None, session_id=None):
        # 설정 로드
        config = self._get_config()  # 환경 변수에서 로드
        
        # Langfuse 클라이언트 초기화
        self._client = Langfuse(**config)
        
        # Trace 생성
        self.trace = self._client.trace(
            id=str(trace_id),
            name=flow_id,
            user_id=user_id,
            session_id=session_id
        )
```

#### 주요 메서드

##### `add_trace()` - Span 시작

```python
def add_trace(self, trace_id, trace_name, trace_type, 
              inputs, metadata=None, vertex=None):
    """
    컴포넌트 실행 시작 시 Span 생성
    
    Args:
        trace_id: 컴포넌트 ID
        trace_name: 컴포넌트 이름
        trace_type: 컴포넌트 타입 (e.g., "ChatModel", "Retriever")
        inputs: 입력 데이터
        metadata: 추가 메타데이터
    """
    start_time = datetime.now(tz=timezone.utc)
    
    # Span 생성
    span = self.trace.span(
        name=trace_name,
        input=inputs,
        metadata={
            "from_langflow_component": True,
            "component_id": trace_id,
            "trace_type": trace_type,
            **metadata
        },
        start_time=start_time
    )
    
    self.spans[trace_id] = span
```

##### `end_trace()` - Span 종료

```python
def end_trace(self, trace_id, trace_name, 
              outputs=None, error=None, logs=()):
    """
    컴포넌트 실행 완료 시 Span 업데이트
    
    Args:
        trace_id: 컴포넌트 ID
        outputs: 출력 데이터
        error: 에러 (있는 경우)
        logs: 로그 메시지
    """
    end_time = datetime.now(tz=timezone.utc)
    
    span = self.spans.pop(trace_id, None)
    if span:
        output = {
            **outputs,
            "error": str(error) if error else None,
            "logs": list(logs) if logs else None
        }
        span.update(output=output, end_time=end_time)
```

##### `end()` - Trace 종료

```python
def end(self, inputs, outputs, error=None, metadata=None):
    """
    전체 플로우 실행 완료 시 Trace 업데이트
    """
    self.trace.update(
        input=inputs,
        output=outputs,
        metadata=metadata
    )
```

### 5.2 API 엔드포인트

**파일**: `src/backend/base/langflow/api/v1/langfuse.py`

#### 1. 연결 상태 확인

```python
@router.get("/status", response_model=ConnectionStatusResponse)
async def get_connection_status():
    """
    Langfuse 연결 상태 확인
    
    Returns:
        {
            "connected": bool,
            "host": str,
            "error": str | None
        }
    """
    # 1. 환경 변수 확인
    config, error = _get_langfuse_config()
    if error:
        return ConnectionStatusResponse(connected=False, error=error)
    
    # 2. API 호출 테스트
    response = await client.get(
        f"{config['host']}/api/public/traces",
        headers={"Authorization": config["auth_header"]},
        params={"limit": 1},
        timeout=5.0
    )
    
    # 3. 상태 반환
    if response.status_code == 200:
        return ConnectionStatusResponse(connected=True, host=config["host"])
    else:
        return ConnectionStatusResponse(
            connected=False, 
            error=f"HTTP {response.status_code}"
        )
```

#### 2. 트레이스 목록 조회

```python
@router.get("/traces", response_model=TracesResponse)
async def get_traces(limit: int = 10, offset: int = 0):
    """
    Langfuse에서 트레이스 목록 조회
    
    Args:
        limit: 최대 반환 개수 (1-100)
        offset: 건너뛸 개수 (페이지네이션)
    
    Returns:
        {
            "traces": [
                {
                    "id": str,
                    "name": str,
                    "timestamp": str,
                    "total_cost": float,
                    "metadata": dict
                }
            ],
            "total": int,
            "has_more": bool
        }
    """
    page = (offset // limit) + 1
    
    response = await client.get(
        f"{config['host']}/api/public/traces",
        headers={"Authorization": config["auth_header"]},
        params={"page": page, "limit": limit}
    )
    
    data = response.json()
    traces = [
        TraceItem(
            id=trace["id"],
            name=trace.get("name"),
            timestamp=trace["timestamp"],
            total_cost=trace.get("totalCost"),
            metadata=trace.get("metadata")
        )
        for trace in data["data"]
    ]
    
    return TracesResponse(
        traces=traces,
        total=data["meta"]["totalItems"],
        has_more=page < data["meta"]["totalPages"]
    )
```

#### 3. 트레이스 상세 조회

```python
@router.get("/traces/{trace_id}", response_model=TraceDetailResponse)
async def get_trace_detail(trace_id: str):
    """
    특정 트레이스의 상세 정보 조회
    
    Returns:
        {
            "id": str,
            "name": str,
            "timestamp": str,
            "input": dict,
            "output": dict,
            "total_cost": float,
            "metadata": dict,
            "user_id": str,
            "session_id": str
        }
    """
    response = await client.get(
        f"{config['host']}/api/public/traces/{trace_id}",
        headers={"Authorization": config["auth_header"]}
    )
    
    trace = response.json()
    return TraceDetailResponse(
        id=trace["id"],
        name=trace.get("name"),
        timestamp=trace["timestamp"],
        input=trace.get("input"),
        output=trace.get("output"),
        total_cost=trace.get("totalCost"),
        metadata=trace.get("metadata"),
        user_id=trace.get("userId"),
        session_id=trace.get("sessionId")
    )
```

#### 인증 헤더 생성

```python
def _get_langfuse_config():
    """
    Langfuse 설정 로드 및 인증 헤더 생성
    """
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    host = os.getenv("LANGFUSE_HOST")
    
    if not all([secret_key, public_key, host]):
        return None, "Environment variables not configured"
    
    # Basic Auth 헤더 생성
    credentials = f"{public_key}:{secret_key}"
    encoded = base64.b64encode(credentials.encode()).decode()
    auth_header = f"Basic {encoded}"
    
    return {
        "host": host,
        "auth_header": auth_header
    }, None
```

---

## 6. Frontend 상세

### 6.1 UI 패널 컴포넌트

**파일**: `src/frontend/src/pages/FlowPage/components/flowSidebarComponent/components/langfuseTracingPanel.tsx`

#### 컴포넌트 구조

```typescript
export default function LangfuseTracingPanel() {
  // 1. 상태 관리
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
  
  // 2. API Queries
  const { data: statusData } = useGetLangfuseStatus();
  const { data: tracesData, refetch } = useGetLangfuseTraces({
    limit: 10,
    offset: 0,
    enabled: statusData?.connected === true
  });
  const { data: traceDetail } = useGetLangfuseTraceDetail({
    traceId: selectedTraceId || "",
    enabled: !!selectedTraceId
  });
  
  // 3. UI 렌더링
  return (
    <div>
      {/* 연결 상태 배지 */}
      <Badge variant={isConnected ? "default" : "destructive"}>
        {isConnected ? "연결됨" : "연결 안됨"}
      </Badge>
      
      {/* 트레이스 목록 */}
      {traces.map(trace => (
        <Card onClick={() => handleTraceClick(trace.id)}>
          <div>{trace.name}</div>
          <div>{formatTimestamp(trace.timestamp)}</div>
          <div>{formatCost(trace.total_cost)}</div>
        </Card>
      ))}
      
      {/* 상세 정보 모달 */}
      <Dialog open={!!selectedTraceId}>
        <Tabs defaultValue="input">
          <TabsContent value="input">
            {renderJsonValue(traceDetail.input)}
          </TabsContent>
          <TabsContent value="output">
            {renderJsonValue(traceDetail.output)}
          </TabsContent>
          <TabsContent value="metadata">
            {renderJsonValue(traceDetail.metadata)}
          </TabsContent>
        </Tabs>
      </Dialog>
    </div>
  );
}
```

#### 주요 기능

##### 1. 연결 상태 표시

```typescript
// 30초마다 자동 갱신
const { data: statusData } = useGetLangfuseStatus();

<Badge variant={isConnected ? "default" : "destructive"}>
  {isConnected ? "연결됨" : "연결 안됨"}
</Badge>
```

##### 2. 트레이스 목록

```typescript
{traces.map((trace) => (
  <Card 
    key={trace.id}
    onClick={() => handleTraceClick(trace.id)}
  >
    <div className="trace-name">{trace.name}</div>
    <div className="trace-time">
      {formatTimestamp(trace.timestamp)}
    </div>
    <div className="trace-cost">
      {formatCost(trace.total_cost)}
    </div>
  </Card>
))}
```

##### 3. 시간 포맷팅

```typescript
const formatTimestamp = (timestamp: string) => {
  const seconds = Math.floor((Date.now() - new Date(timestamp)) / 1000);
  
  if (seconds < 60) return `${seconds}초 전`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}분 전`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}시간 전`;
  const days = Math.floor(hours / 24);
  return `${days}일 전`;
};
```

##### 4. 비용 포맷팅

```typescript
const formatCost = (cost: number | null) => {
  if (cost === null) return "N/A";
  return `$${cost.toFixed(4)}`;
};
```

##### 5. JSON 렌더링

```typescript
const renderJsonValue = (value: any, depth: number = 0): React.ReactNode => {
  if (value === null) return <span>null</span>;
  if (typeof value === "boolean") return <span>{String(value)}</span>;
  if (typeof value === "number") return <span>{value}</span>;
  if (typeof value === "string") return <span>"{value}"</span>;
  
  if (Array.isArray(value)) {
    return (
      <div className="ml-4">
        {value.map((item, idx) => (
          <div key={idx}>
            <span>[{idx}]</span>
            {renderJsonValue(item, depth + 1)}
          </div>
        ))}
      </div>
    );
  }
  
  if (typeof value === "object") {
    return (
      <div className="ml-4">
        {Object.entries(value).map(([key, val]) => (
          <div key={key}>
            <span>{key}:</span>
            {renderJsonValue(val, depth + 1)}
          </div>
        ))}
      </div>
    );
  }
  
  return String(value);
};
```

##### 6. Duration 계산

```typescript
const calculateDuration = (obj: any): string | null => {
  if (!obj?.startTime || !obj?.endTime) return null;
  
  const start = new Date(obj.startTime).getTime();
  const end = new Date(obj.endTime).getTime();
  const duration = end - start;
  
  if (duration < 1000) {
    return `${duration}ms`;
  } else {
    return `${(duration / 1000).toFixed(2)}s`;
  }
};
```

### 6.2 API Query Hooks

#### 1. useGetLangfuseStatus

**파일**: `src/frontend/src/controllers/API/queries/langfuse/use-get-langfuse-status.ts`

```typescript
export const useGetLangfuseStatus = () => {
  const { query } = UseRequestProcessor();
  
  const getLangfuseStatusFn = async (): Promise<LangfuseStatus> => {
    const response = await api.get<LangfuseStatus>(
      `${getURL("LANGFUSE")}/status`
    );
    return response.data;
  };
  
  return query(["langfuse-status"], getLangfuseStatusFn, {
    refetchInterval: 30000, // 30초마다 자동 갱신
  });
};
```

#### 2. useGetLangfuseTraces

```typescript
interface GetTracesParams {
  limit: number;
  offset: number;
  enabled?: boolean;
}

export const useGetLangfuseTraces = ({
  limit,
  offset,
  enabled = true
}: GetTracesParams) => {
  const { query } = UseRequestProcessor();
  
  const getTracesFn = async (): Promise<TracesResponse> => {
    const response = await api.get<TracesResponse>(
      `${getURL("LANGFUSE")}/traces`,
      { params: { limit, offset } }
    );
    return response.data;
  };
  
  return query(
    ["langfuse-traces", limit, offset],
    getTracesFn,
    { enabled }
  );
};
```

#### 3. useGetLangfuseTraceDetail

```typescript
interface GetTraceDetailParams {
  traceId: string;
  enabled?: boolean;
}

export const useGetLangfuseTraceDetail = ({
  traceId,
  enabled = true
}: GetTraceDetailParams) => {
  const { query } = UseRequestProcessor();
  
  const getTraceDetailFn = async (): Promise<TraceDetailResponse> => {
    const response = await api.get<TraceDetailResponse>(
      `${getURL("LANGFUSE")}/traces/${traceId}`
    );
    return response.data;
  };
  
  return query(
    ["langfuse-trace-detail", traceId],
    getTraceDetailFn,
    { enabled }
  );
};
```

---

## 7. API 엔드포인트

### 엔드포인트 목록

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/v1/langfuse/status` | 연결 상태 확인 |
| GET | `/api/v1/langfuse/traces` | 트레이스 목록 조회 |
| GET | `/api/v1/langfuse/traces/{trace_id}` | 트레이스 상세 조회 |

### 1. GET /api/v1/langfuse/status

#### Request

```http
GET /api/v1/langfuse/status HTTP/1.1
Host: localhost:7860
```

#### Response

```json
{
  "connected": true,
  "host": "https://cloud.langfuse.com",
  "error": null
}
```

**연결 실패 시:**

```json
{
  "connected": false,
  "host": "https://cloud.langfuse.com",
  "error": "Invalid credentials. Check your Langfuse API keys."
}
```

### 2. GET /api/v1/langfuse/traces

#### Request

```http
GET /api/v1/langfuse/traces?limit=10&offset=0 HTTP/1.1
Host: localhost:7860
```

#### Query Parameters

- `limit` (int, optional): 최대 반환 개수 (기본값: 10, 범위: 1-100)
- `offset` (int, optional): 건너뛸 개수 (기본값: 0)

#### Response

```json
{
  "traces": [
    {
      "id": "trace-123abc",
      "name": "RAG Flow",
      "timestamp": "2025-11-07T09:30:15.123Z",
      "input": {
        "query": "What is Langflow?"
      },
      "output": {
        "answer": "Langflow is a visual framework..."
      },
      "total_cost": 0.0025,
      "metadata": {
        "time_elapsed": 2.45,
        "flow_id": "flow-456def"
      }
    }
  ],
  "total": 42,
  "has_more": true
}
```

### 3. GET /api/v1/langfuse/traces/{trace_id}

#### Request

```http
GET /api/v1/langfuse/traces/trace-123abc HTTP/1.1
Host: localhost:7860
```

#### Response

```json
{
  "id": "trace-123abc",
  "name": "RAG Flow",
  "timestamp": "2025-11-07T09:30:15.123Z",
  "input": {
    "query": "What is Langflow?",
    "chat_history": []
  },
  "output": {
    "answer": "Langflow is a visual framework...",
    "sources": [...]
  },
  "total_cost": 0.0025,
  "metadata": {
    "time_elapsed": 2.45,
    "flow_id": "flow-456def",
    "component_count": 5
  },
  "user_id": "user-789ghi",
  "session_id": "session-012jkl"
}
```

---

## 8. 사용 예제

### 예제 1: 기본 플로우 트레이싱

```python
# 플로우 생성
from langflow import Flow
from langflow.components import ChatInput, ChatOpenAI, ChatOutput

flow = Flow()
chat_input = ChatInput()
chat_model = ChatOpenAI(model="gpt-4")
chat_output = ChatOutput()

flow.add_edge(chat_input, chat_model)
flow.add_edge(chat_model, chat_output)

# 플로우 실행 (자동으로 Langfuse에 트레이싱됨)
result = flow.run(input="Hello!")

# Langfuse에서 확인 가능:
# - Trace ID: flow.run_id
# - Spans: chat_input, chat_model, chat_output
# - Input/Output: 각 컴포넌트의 입출력
# - Cost: OpenAI API 비용
```

### 예제 2: 메타데이터 추가

```python
# 커스텀 메타데이터 추가
result = flow.run(
    input="What is RAG?",
    metadata={
        "user_id": "user123",
        "session_id": "session456",
        "tags": ["production", "rag"]
    }
)
```

### 예제 3: Frontend에서 트레이스 조회

```typescript
// 1. 연결 상태 확인
const { data: status } = useGetLangfuseStatus();
console.log("Connected:", status.connected);

// 2. 최근 트레이스 조회
const { data: traces } = useGetLangfuseTraces({
  limit: 10,
  offset: 0,
  enabled: status?.connected
});

traces?.traces.forEach(trace => {
  console.log(`Trace: ${trace.name}`);
  console.log(`Cost: $${trace.total_cost}`);
  console.log(`Time: ${trace.metadata?.time_elapsed}s`);
});

// 3. 특정 트레이스 상세 정보
const { data: detail } = useGetLangfuseTraceDetail({
  traceId: "trace-123abc",
  enabled: true
});

console.log("Input:", detail?.input);
console.log("Output:", detail?.output);
```

### 예제 4: API 직접 호출

```bash
# 1. 연결 상태 확인
curl http://localhost:7860/api/v1/langfuse/status

# 2. 트레이스 목록 조회
curl "http://localhost:7860/api/v1/langfuse/traces?limit=10&offset=0"

# 3. 트레이스 상세 조회
curl http://localhost:7860/api/v1/langfuse/traces/trace-123abc
```

---

## 9. 문제 해결

### 문제 1: "연결 안됨" 상태

**증상:**
- UI 패널에 "연결 안됨" 배지 표시
- 트레이스 목록이 표시되지 않음

**해결 방법:**

1. 환경 변수 확인
   ```bash
   echo $LANGFUSE_SECRET_KEY
   echo $LANGFUSE_PUBLIC_KEY
   echo $LANGFUSE_HOST
   ```

2. API 키 유효성 확인
   - Langfuse 대시보드에서 키가 활성화되어 있는지 확인
   - 키가 올바른 프로젝트에 속해 있는지 확인

3. 네트워크 연결 확인
   ```bash
   curl https://cloud.langfuse.com/api/public/traces \
     -H "Authorization: Basic $(echo -n 'PUBLIC_KEY:SECRET_KEY' | base64)"
   ```

4. Langflow 재시작
   ```bash
   langflow run --env-file .env
   ```

### 문제 2: 트레이스가 기록되지 않음

**증상:**
- 플로우는 정상 실행되지만 Langfuse에 트레이스가 나타나지 않음

**해결 방법:**

1. Tracing Service 활성화 확인
   ```python
   from langflow.services.deps import get_service
   from langflow.services.schema import ServiceType
   
   tracing_service = get_service(ServiceType.TRACING_SERVICE)
   print("Deactivated:", tracing_service.deactivated)
   ```

2. 로그 확인
   ```bash
   # DEBUG 레벨로 실행
   langflow run --log-level debug
   
   # 로그에서 Langfuse 관련 메시지 확인
   # "Error setting up Langfuse tracer" 등의 에러 확인
   ```

3. Langfuse SDK 설치 확인
   ```bash
   pip install langfuse
   ```

### 문제 3: 비용(Cost)이 표시되지 않음

**증상:**
- 트레이스는 표시되지만 `total_cost`가 `null`

**원인:**
- Langfuse는 특정 LLM 제공자의 API 사용량을 기반으로 비용을 자동 계산
- 지원되지 않는 모델이거나 토큰 정보가 누락된 경우 비용이 계산되지 않음

**해결 방법:**
- OpenAI, Anthropic 등 지원되는 모델 사용
- 커스텀 비용 계산은 Langfuse 메타데이터에 수동으로 추가 가능

### 문제 4: API 401 Unauthorized

**증상:**
```json
{
  "connected": false,
  "error": "Invalid credentials. Check your Langfuse API keys."
}
```

**해결 방법:**

1. Public Key와 Secret Key 순서 확인
   ```bash
   # 올바른 형식
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   ```

2. Base64 인코딩 확인
   ```python
   import base64
   public = "pk-lf-..."
   secret = "sk-lf-..."
   credentials = f"{public}:{secret}"
   encoded = base64.b64encode(credentials.encode()).decode()
   print(f"Basic {encoded}")
   ```

3. 키 재발급
   - Langfuse 대시보드에서 새 키 발급
   - 환경 변수 업데이트 후 재시작

### 문제 5: 트레이스가 중복 생성됨

**증상:**
- 같은 플로우 실행이 여러 개의 트레이스로 나타남

**원인:**
- 플로우가 여러 번 실행되었거나
- TracingService가 여러 번 초기화됨

**해결 방법:**
- 정상 동작임 (각 실행마다 고유한 trace_id 생성)
- 같은 세션으로 묶으려면 `session_id` 사용

### 문제 6: JSON 렌더링 에러

**증상:**
- 트레이스 상세 모달에서 Input/Output이 표시되지 않음

**원인:**
- 순환 참조(circular reference)가 있는 객체
- 직렬화할 수 없는 타입 (예: function, class instance)

**해결 방법:**
- Backend에서 `serialize()` 함수 사용
- 순환 참조 제거

---

## 부록

### A. 데이터 스키마

#### TraceItem

```typescript
interface TraceItem {
  id: string;                      // 고유 ID
  name: string | null;             // Trace 이름 (Flow 이름)
  timestamp: string;               // ISO 8601 형식
  input: Record<string, any> | null;
  output: Record<string, any> | null;
  total_cost: number | null;       // USD 단위
  metadata: Record<string, any> | null;
}
```

#### TraceDetailResponse

```typescript
interface TraceDetailResponse extends TraceItem {
  user_id: string | null;          // 사용자 ID
  session_id: string | null;       // 세션 ID
}
```

#### ConnectionStatusResponse

```typescript
interface ConnectionStatusResponse {
  connected: boolean;              // 연결 상태
  host: string | null;             // Langfuse 호스트 URL
  error: string | null;            // 에러 메시지
}
```

### B. 환경 변수 레퍼런스

| 변수명 | 필수 | 설명 | 예시 |
|-------|------|------|------|
| `LANGFUSE_SECRET_KEY` | ✅ | Secret API Key | `sk-lf-...` |
| `LANGFUSE_PUBLIC_KEY` | ✅ | Public API Key | `pk-lf-...` |
| `LANGFUSE_HOST` | ✅ | Langfuse 서버 URL | `https://cloud.langfuse.com` |

### C. 관련 링크

- [Langfuse 공식 문서](https://langfuse.com/docs)
- [Langfuse Python SDK](https://github.com/langfuse/langfuse-python)
- [Langfuse Cloud](https://cloud.langfuse.com)
- [Langflow 공식 문서](https://docs.langflow.org)

---

**문서 버전:** 1.0  
**최종 수정일:** 2025-11-07  
**작성자:** Langflow Team

