<!-- markdownlint-disable MD030 -->

# sapie-agentX

[![PyPI - License](https://img.shields.io/badge/license-MIT-orange)](https://opensource.org/licenses/MIT)

**sapie-agentX**는 [Langflow](https://langflow.org) 기반으로 개발된 강력한 AI 에이전트 플랫폼입니다.

Langflow의 모든 기능을 활용하면서, 다음과 같은 커스텀 기능이 추가되었습니다:
-  **자연어 기반 플로우 자동 생성** (NL to Flow)
-  **Langfuse 통합 트레이싱 시스템**
- **향상된 컴포넌트 검색 및 메타데이터 시스템**

## 프로젝트 소개

sapie-agentX는 [Langflow](https://langflow.org)의 강력한 비주얼 워크플로우 빌더를 기반으로 하면서, 엔터프라이즈급 AI 에이전트 개발에 필요한 추가 기능들을 제공합니다.


##  주요 기능

### Langflow 핵심 기능
- **비주얼 빌더 인터페이스**: 빠른 시작과 반복 개발
- **소스 코드 접근**: Python을 사용한 모든 컴포넌트 커스터마이징
- **인터랙티브 플레이그라운드**: 단계별 제어로 즉시 테스트 및 개선
- **멀티 에이전트 오케스트레이션**: 대화 관리 및 검색 기능
- **API로 배포** 또는 Python 앱용 JSON 내보내기
- **MCP 서버로 배포**: 플로우를 MCP 클라이언트용 도구로 전환
- **관찰성**: LangSmith, LangFuse 및 기타 통합
- **엔터프라이즈 준비**: 보안 및 확장성

### sapie-agentX 추가 기능

#### 자연어 기반 플로우 생성 (NL to Flow)
- GPT-4를 활용한 자연어 입력으로 플로우 자동 생성
- 컴포넌트 자동 선택 및 연결
- 키워드 기반 향상된 컴포넌트 검색 시스템
- 스마트 Fallback 전략으로 최적의 대안 제안

```
예: "PDF 파일을 읽고 질문에 답변하는 RAG 시스템 만들어줘"
→ FileComponent → TextSplitter → VectorStore → ChatModel 자동 생성
```

#### Langfuse 트레이싱 통합
- 실시간 플로우 실행 추적
- 컴포넌트별 입출력 모니터링
- 비용 및 성능 측정
- 커스텀 UI 패널로 즉시 확인

#### 향상된 컴포넌트 시스템
- VALID_EXTENSIONS 기반 자동 키워드 생성
- 점수 기반 컴포넌트 검색 알고리즘
- 향상된 메타데이터 관리

## 빠른 시작

### 사전 요구사항

- Python 3.10–3.13
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (권장 패키지 매니저)

### 설치 및 실행

#### 1. 저장소 클론

```shell
git clone <repository-url>
cd sapie-agentX
```

#### 2. 종속성 설치

```shell
# Backend
cd src/backend/base
uv pip install -e .

# Frontend (선택사항)
cd ../../../frontend
npm install
```

#### 3. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가:

```bash
# OpenAI API (NL to Flow 기능용)
OPENAI_API_KEY=sk-your-api-key-here

# Langfuse (트레이싱 기능용, 선택사항)
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

#### 4. 서버 실행

```shell
# 프로젝트 루트에서
make run

# 또는
langflow run
```

서버가 http://127.0.0.1:7860 에서 시작됩니다.



## 프로젝트 구조

```
sapie-agentX/
├── src/
│   ├── backend/
│   │   └── base/
│   │       └── langflow/
│   │           ├── api/v1/
│   │           │   ├── nl_flow.py          # NL to Flow API
│   │           │   └── langfuse.py         # Langfuse API
│   │           └── services/
│   │               ├── nl_flow/
│   │               │   ├── service.py      # NL to Flow 로직
│   │               │   └── component_metadata.py  # 컴포넌트 메타데이터
│   │               └── tracing/
│   │                   └── langfuse.py     # Langfuse 트레이서
│   └── frontend/
│       └── src/
│           ├── pages/FlowPage/components/
│           │   └── flowSidebarComponent/components/
│           │       ├── nlToFlowPanel.tsx   # NL to Flow UI
│           │       └── langfuseTracingPanel.tsx  # Langfuse UI
│           └── controllers/API/queries/
│               ├── flows/
│               │   └── use-post-nl-flow.ts
│               └── langfuse/
│                   └── use-get-langfuse-*.ts
└── document/
    ├── NL_TO_FLOW_COMPLETE_GUIDE.md
    └── LANGFUSE_TRACING_GUIDE.md
```
