# CLAUDE.md - 통합 미용의료 AI 상담 플랫폼

## 프로젝트 개요

외국인 대상 미용의료 클리닉을 위한 멀티 메신저 통합 AI 상담 플랫폼.
6개 메신저 통합, 3레이어 AI 자동 답변, 자동 번역, QR 결제, CRM 자동화.

- 기획서: `medical-messenger-mvp.md`
- 구현 플랜: `plan/` 디렉토리 참조

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | Python 3.12 + FastAPI |
| Frontend | Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui |
| DB | PostgreSQL 16 (pgvector) + SQLAlchemy 2.0 + Alembic |
| Cache | Redis |
| AI | Claude + Azure OpenAI + Gemini / LangChain (Agent/RAG) / LangSmith |
| Vector DB | pgvector (MVP) → Azure AI Search (고도화) |
| Queue | Celery + RabbitMQ |
| Infra | Azure (Container Apps, DB for PostgreSQL, Cache for Redis, Blob Storage) |
| State | Zustand (Frontend) |

## 핵심 개발 원칙

### 1. Think First, Code Later

코드를 작성하기 전에 반드시 먼저 생각한다:
- **무엇을 만들 것인가**: 요구사항을 정확히 이해했는지 확인
- **어떻게 검증할 것인가**: 테스트/검증 방법을 먼저 설계
- **기존 코드에 미치는 영향**: 사이드 이펙트 파악
- **가장 작은 변경 범위**: 필요한 부분만 정확히 수정

### 2. TDD (Test-Driven Development)

모든 기능 구현은 TDD를 따른다:

```
1. RED:   실패하는 테스트를 먼저 작성
2. GREEN: 테스트를 통과하는 최소한의 코드 작성
3. REFACTOR: 코드를 정리하되 테스트는 계속 통과
```

- 테스트 없이 프로덕션 코드를 작성하지 않는다
- 테스트가 명세(specification) 역할을 한다
- 테스트 파일 위치: `backend/tests/`, `frontend/src/__tests__/`

### 3. 최소 변경 원칙

- 정확히 필요한 부분만 수정한다
- "이왕 고치는 김에" 식의 확장을 하지 않는다
- 하나의 PR에 하나의 관심사만 담는다
- 리팩터링은 기능 변경과 분리한다

### 4. 기존 컨벤션 준수

코드를 수정할 때 반드시 기존 코드의 패턴을 먼저 파악하고 따른다:
- 네이밍 컨벤션 (변수, 함수, 클래스, 파일)
- import 순서와 스타일
- 에러 처리 패턴
- 코드 구조 (서비스 레이어, 레포지토리 패턴 등)
- 기존 코드와 일관된 추상화 수준 유지

## 개발 워크플로우

### Git Branch 전략

```
main                          ← 프로덕션 (보호된 브랜치)
├── develop                   ← 개발 통합 브랜치
│   ├── feature/phase0-setup     ← Phase 0: 기반 구축
│   ├── feature/phase1-telegram  ← Phase 1: Telegram 연동
│   ├── feature/phase1-meta      ← Phase 1: Meta 연동
│   ├── feature/phase2-ai-engine ← Phase 2: AI 엔진
│   ├── fix/telegram-webhook     ← 버그 수정
│   └── refactor/message-service ← 리팩터링
```

**브랜치 규칙:**
- 주요 작업마다 반드시 별도 브랜치 생성
- 브랜치명: `{type}/{description}` (feature/, fix/, refactor/, docs/)
- 작업 완료 시 develop에 PR 생성
- main 직접 push 금지

### 커밋 규칙

```
feat: 새 기능 추가
fix: 버그 수정
test: 테스트 추가/수정
refactor: 리팩터링 (기능 변경 없음)
docs: 문서 추가/수정
chore: 설정, 의존성 등 잡일
```

**커밋 습관:**
- 작은 단위로 자주 커밋 (하나의 논리적 변경 = 하나의 커밋)
- 커밋 메시지는 "왜" 변경했는지를 담는다
- 작업 중간중간 push하여 작업 유실 방지
- 테스트가 통과하는 상태에서만 커밋

### 작업 사이클

```
1. 이슈/작업 확인
2. 브랜치 생성: git checkout -b feature/xxx
3. 검증 방법 설계 (테스트 시나리오 작성)
4. 테스트 작성 (RED)
5. 구현 (GREEN)
6. 리팩터링 (REFACTOR)
7. 커밋 + push
8. (필요시) 문서 업데이트
9. PR 생성
```

## 코딩 컨벤션

### Backend (Python)

```python
# 네이밍
class ClinicService:       # 클래스: PascalCase
def create_booking():      # 함수: snake_case
clinic_id: UUID            # 변수: snake_case
MAX_RETRY = 3              # 상수: UPPER_SNAKE_CASE

# import 순서
import stdlib              # 1. 표준 라이브러리
import third_party         # 2. 서드파티
from app.core import ...   # 3. 프로젝트 내부

# 타입 힌트 필수
async def get_clinic(self, clinic_id: UUID) -> Clinic:

# Docstring: 복잡한 함수만 (자명한 건 생략)
async def calculate_sales_performance(self, clinic_id: UUID) -> float:
    """세일즈 퍼포먼스 점수 계산 (100점 만점).

    분당 마진(40점) + 난이도(30점) + 클리닉 선호(30점)
    """
```

### Frontend (TypeScript)

```typescript
// 네이밍
const ConversationList: React.FC = ...   // 컴포넌트: PascalCase
function useWebSocket() { ... }          // 훅: camelCase (use 접두사)
const clinicId: string = ...             // 변수: camelCase
const API_BASE_URL = ...                 // 상수: UPPER_SNAKE_CASE

// 파일명
ConversationList.tsx                     // 컴포넌트: PascalCase
useWebSocket.ts                          // 훅: camelCase
api-client.ts                            // 유틸: kebab-case
conversation-store.ts                    // 스토어: kebab-case
```

## 테스트 전략

### Backend

```
tests/
├── conftest.py               # 공통 fixture (DB 세션, 테스트 클리닉 등)
├── test_api/                 # API 엔드포인트 테스트 (통합)
│   ├── test_auth.py
│   ├── test_conversations.py
│   └── ...
├── test_services/            # 서비스 로직 테스트 (단위)
│   ├── test_message_service.py
│   ├── test_procedure_service.py
│   └── ...
├── test_messenger/           # 메신저 어댑터 테스트
│   ├── test_telegram_adapter.py
│   └── ...
└── test_ai/                  # AI 엔진 테스트
    ├── test_knowledge_chain.py
    ├── test_consultation_agent.py
    └── ...
```

**테스트 도구:**
- pytest + pytest-asyncio
- httpx (FastAPI TestClient)
- factory_boy (테스트 데이터 팩토리)
- unittest.mock / pytest-mock

**테스트 원칙:**
- 새 기능 = 테스트 먼저 (TDD)
- 버그 수정 = 재현 테스트 먼저
- 외부 API (메신저, PG, LLM) = mock 사용
- DB 테스트 = 테스트 전용 PostgreSQL (Docker)

### Frontend

```
src/__tests__/
├── components/
├── hooks/
└── utils/
```

**테스트 도구:**
- Vitest + React Testing Library
- MSW (API 모킹)

## 문서화 규칙

### 문서를 작성해야 하는 경우

- 새로운 모듈/서비스 추가 시
- API 엔드포인트 추가/변경 시
- 아키텍처 결정 시 (ADR 형태)
- 복잡한 비즈니스 로직 구현 시
- 환경 설정 변경 시

### 문서 위치

```
docs/
├── adr/                      # Architecture Decision Records
│   ├── 001-tech-stack.md
│   ├── 002-multi-llm-strategy.md
│   └── ...
├── api/                      # API 문서 (자동생성: FastAPI /docs)
├── guides/                   # 개발 가이드
│   ├── local-setup.md
│   ├── deployment.md
│   └── adding-messenger.md
└── changelog/                # 변경 이력
```

### 문서 참조 원칙

- 문서를 작성했으면 반드시 참조한다 (작성만 하고 안 보는 문서는 만들지 않는다)
- 코드 변경 시 관련 문서도 함께 업데이트한다
- 오래된 문서는 삭제하거나 업데이트한다
- README.md에 핵심 문서 링크를 유지한다

## 참조 문서

| 문서 | 위치 | 설명 |
|------|------|------|
| 기획서 | `medical-messenger-mvp.md` | 전체 기획 (필독) |
| 아키텍처 | `plan/01-overview-and-architecture.md` | 기술 스택, 디렉토리, AI 구조 |
| DB 스키마 | `plan/02-database-schema.md` | 전체 테이블 설계 |
| Phase 0~4 | `plan/03-phases-part1.md` | 기반, 메신저, AI, 번역, UI |
| Phase 5~8 | `plan/04-phases-part2.md` | 프로시져, 결제, CRM, 만족도 |
| Phase 9~11 + API | `plan/05-phases-part3-and-api.md` | 사람다움, 정산, AI고급, API 전체 목록 |

## 프로젝트 명령어

### Backend
```bash
# 개발 서버
cd backend && uvicorn app.main:app --reload --port 8000

# 테스트
cd backend && pytest
cd backend && pytest tests/test_api/test_auth.py -v      # 특정 파일
cd backend && pytest -k "test_create_booking" -v          # 특정 테스트

# DB 마이그레이션
cd backend && alembic revision --autogenerate -m "add bookings table"
cd backend && alembic upgrade head

# Celery
cd backend && celery -A app.tasks.celery_app worker --loglevel=info
cd backend && celery -A app.tasks.celery_app beat --loglevel=info

# 린트/포매팅
cd backend && ruff check .
cd backend && ruff format .
```

### Frontend
```bash
cd frontend && npm run dev        # 개발 서버
cd frontend && npm run build      # 빌드
cd frontend && npm run test       # 테스트
cd frontend && npm run lint       # 린트
```

### Docker
```bash
docker compose -f docker-compose.dev.yml up -d    # 전체 실행
docker compose -f docker-compose.dev.yml down      # 중지
docker compose -f docker-compose.dev.yml logs -f backend  # 로그
```
