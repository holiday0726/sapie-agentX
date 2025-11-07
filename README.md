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

## ⚡️ 빠른 시작

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

## 📚 상세 가이드

### 🤖 자연어 기반 플로우 생성

자연어 설명으로 플로우를 자동 생성하는 방법:

- **[NL to Flow 완전 가이드](./document/NL_TO_FLOW_COMPLETE_GUIDE.md)**
  - 빠른 시작 및 설정
  - 아키텍처 및 데이터 흐름
  - 백엔드 및 프론트엔드 구현 상세
  - 컴포넌트 검색 강화 (Keywords 시스템)
  - System Prompt Fallback 전략
  - 테스트 및 문제 해결

**주요 개선사항:**
- VALID_EXTENSIONS 기반 키워드 자동 생성 (예: PDF → "PDF loader", "PDF reader")
- 점수 기반 검색 알고리즘 (Exact match: 100점, Keywords: 40점 등)
- LLM Fallback 전략으로 대안 컴포넌트 자동 제안

### 📊 Langfuse 트레이싱

LLM 애플리케이션 실행 추적 및 모니터링:

- **[Langfuse 트레이싱 가이드](./document/LANGFUSE_TRACING_GUIDE.md)**
  - 환경 설정
  - Langflow 통합
  - 실시간 트레이스 모니터링
  - 비용 및 성능 추적
  - 커스텀 UI 패널 사용법

## 🏗️ 프로젝트 구조

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

## 🔧 개발

### 개발 환경 설정

개발 또는 소스에서 실행하는 경우 [DEVELOPMENT.md](./DEVELOPMENT.md)를 참조하세요.

### 주요 개발 사항

#### 백엔드
- **컴포넌트 검색 강화**: `component_metadata.py`에 VALID_EXTENSIONS 기반 키워드 시스템
- **점수 기반 검색**: `service.py`의 `_search_components` 개선
- **System Prompt 개선**: Fallback 전략 및 대안 제안 로직

#### 프론트엔드
- **NL to Flow Panel**: 자연어 입력 UI 및 플로우 변환 로직
- **Langfuse Panel**: 트레이스 목록, 상세 정보, JSON 렌더링

## 📦 배포

sapie-agentX는 완전히 오픈소스이며, 모든 주요 클라우드에 배포할 수 있습니다.

- Docker 배포는 [Langflow Docker 가이드](https://docs.langflow.org/deployment-docker) 참조
- 환경 변수 설정을 잊지 마세요 (OPENAI_API_KEY, LANGFUSE_*)

## 🧪 테스트

### NL to Flow 테스트

```bash
# 서버 실행
make run

# 브라우저에서 http://127.0.0.1:7860 접속
# 사이드바에서 "AI Flow Builder" 찾기
# 테스트 프롬프트 입력:
#   - "간단한 챗봇 만들어줘"
#   - "PDF 파일을 읽고 질문에 답변하는 RAG 시스템 만들어줘"
```

### Langfuse 트레이싱 테스트

```bash
# 환경 변수 설정 확인
echo $LANGFUSE_SECRET_KEY
echo $LANGFUSE_PUBLIC_KEY

# 플로우 실행 후 사이드바에서 "Langfuse Tracing" 패널 확인
```

## 🐛 문제 해결

### NL to Flow 관련
- **문제**: LLM이 플로우를 생성하지 않음
- **해결**: 
  - OPENAI_API_KEY 확인
  - 서버 재시작
  - 로그 확인 (`logs/langflow.log`)

### Langfuse 관련
- **문제**: "연결 안됨" 표시
- **해결**:
  - LANGFUSE_* 환경 변수 확인
  - API 키 유효성 확인
  - 네트워크 연결 확인

자세한 내용은 각 가이드의 "트러블슈팅" 섹션을 참조하세요.

## 📄 라이선스

MIT License - [LICENSE](./LICENSE) 참조

## 🙏 감사의 말

이 프로젝트는 [Langflow](https://github.com/langflow-ai/langflow)를 기반으로 합니다. Langflow 팀과 커뮤니티에 감사드립니다.

## 📞 문의

프로젝트에 대한 질문이나 제안이 있으시면 이슈를 열어주세요.

---

**Built with ❤️ on top of [Langflow](https://langflow.org)**
