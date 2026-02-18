# 01. 기술 스택 & 아키텍처 총괄

## 1. 확정 기술 스택

| 영역 | 기술 | 비고 |
|------|------|------|
| **Backend** | Python 3.12 + FastAPI | 비동기, 타입 힌트 |
| **Frontend** | Next.js 15 (App Router) + TypeScript | React 19, Tailwind CSS, shadcn/ui |
| **DB** | Azure Database for PostgreSQL Flexible Server | pgvector 확장 포함 |
| **ORM** | SQLAlchemy 2.0 + Alembic | async 세션 |
| **캐시** | Azure Cache for Redis | 세션, 캐시, rate limiting |
| **벡터 DB** | pgvector (MVP) → Azure AI Search (고도화) | LangChain 추상화로 교체 용이 |
| **AI - LLM** | Claude API + Azure OpenAI + Gemini | LangChain으로 멀티 LLM 라우팅 |
| **AI - 프레임워크** | LangChain 전면 활용 (Agent/RAG/Chain) | LangSmith 모니터링 |
| **AI - 임베딩** | Azure OpenAI text-embedding-3-small | RAG용 벡터 임베딩 |
| **메시지 큐** | Celery + RabbitMQ | CRM 스케줄링, 비동기 처리 |
| **실시간** | WebSocket (FastAPI native + Socket.IO) | 채팅 UI 실시간 업데이트 |
| **스토리지** | Azure Blob Storage | 이미지, 파일, 엑셀 |
| **인프라** | Azure Container Apps | 컨테이너 기반, 자동 스케일링 |
| **CI/CD** | GitHub Actions → Azure Container Registry | 자동 빌드/배포 |
| **모니터링** | LangSmith (AI) + Azure Monitor (인프라) | |

---

## 2. Azure 인프라 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        Azure Cloud                               │
│                                                                   │
│  ┌──────────────────┐    ┌──────────────────┐                    │
│  │ Azure Container  │    │ Azure Container  │                    │
│  │ Apps: backend    │    │ Apps: frontend   │                    │
│  │ (FastAPI)        │◄──►│ (Next.js)        │                    │
│  │ + Celery Worker  │    │                  │                    │
│  │ + Celery Beat    │    │                  │                    │
│  └────────┬─────────┘    └──────────────────┘                    │
│           │                                                       │
│  ┌────────▼─────────┐    ┌──────────────────┐                    │
│  │ Azure DB for     │    │ Azure Cache for  │                    │
│  │ PostgreSQL       │    │ Redis            │                    │
│  │ (+ pgvector)     │    │                  │                    │
│  └──────────────────┘    └──────────────────┘                    │
│                                                                   │
│  ┌──────────────────┐    ┌──────────────────┐                    │
│  │ RabbitMQ         │    │ Azure Blob       │                    │
│  │ (Container App   │    │ Storage          │                    │
│  │  or CloudAMQP)   │    │                  │                    │
│  └──────────────────┘    └──────────────────┘                    │
│                                                                   │
│  ┌──────────────────┐    ┌──────────────────┐                    │
│  │ Azure OpenAI     │    │ Azure Container  │                    │
│  │ Service          │    │ Registry (ACR)   │                    │
│  └──────────────────┘    └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘

외부 서비스:
├── Anthropic Claude API
├── Google Gemini API
├── LangSmith (모니터링)
├── Meta Business Platform (Instagram/FB/WhatsApp)
├── LINE Messaging API
├── Telegram Bot API
├── KakaoTalk Channel API
├── 킹오더브라더스 PG API
├── 알리엑스 (Alipay) API
└── Stripe API (백업)
```

---

## 3. 프로젝트 디렉토리 구조

```
medical-messenger-platform/
├── docker-compose.yml              # 로컬 개발용
├── docker-compose.dev.yml
├── .env.example
├── .github/
│   └── workflows/
│       ├── backend-ci.yml
│       └── frontend-ci.yml
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   │
│   ├── app/
│   │   ├── main.py                 # FastAPI 앱 엔트리
│   │   ├── config.py               # pydantic-settings 기반 설정
│   │   ├── dependencies.py         # DI (DB 세션, 현재 유저 등)
│   │   │
│   │   ├── models/                 # SQLAlchemy ORM 모델
│   │   │   ├── base.py             # Base, TimestampMixin, TenantMixin
│   │   │   ├── clinic.py           # Clinic
│   │   │   ├── user.py             # User (관리자/수퍼바이저)
│   │   │   ├── messenger.py        # MessengerAccount, MessengerType(enum)
│   │   │   ├── customer.py         # Customer
│   │   │   ├── conversation.py     # Conversation
│   │   │   ├── message.py          # Message, MessageTranslation
│   │   │   ├── procedure.py        # Procedure, ClinicProcedure, ProcedureRelation
│   │   │   ├── pricing.py          # ProcedurePricing
│   │   │   ├── booking.py          # Booking
│   │   │   ├── payment.py          # Payment, PaymentProvider
│   │   │   ├── crm.py              # CRMEvent, SatisfactionSurvey, Review
│   │   │   ├── satisfaction.py     # SatisfactionScore (실시간)
│   │   │   ├── settlement.py       # Settlement, SettlementItem
│   │   │   ├── medical_term.py     # MedicalTerm (다국어 사전)
│   │   │   └── ai_config.py        # AIPersona, CulturalProfile, ResponseLibrary
│   │   │
│   │   ├── schemas/                # Pydantic 요청/응답 스키마
│   │   │   ├── auth.py
│   │   │   ├── clinic.py
│   │   │   ├── conversation.py
│   │   │   ├── message.py
│   │   │   ├── procedure.py
│   │   │   ├── payment.py
│   │   │   ├── crm.py
│   │   │   └── settlement.py
│   │   │
│   │   ├── api/                    # API 라우트
│   │   │   ├── v1/
│   │   │   │   ├── router.py       # 라우터 통합
│   │   │   │   ├── auth.py
│   │   │   │   ├── clinics.py
│   │   │   │   ├── conversations.py
│   │   │   │   ├── messages.py
│   │   │   │   ├── procedures.py
│   │   │   │   ├── pricing.py
│   │   │   │   ├── payments.py
│   │   │   │   ├── crm.py
│   │   │   │   ├── satisfaction.py
│   │   │   │   ├── settlements.py
│   │   │   │   ├── analytics.py
│   │   │   │   ├── medical_terms.py
│   │   │   │   └── ai_settings.py
│   │   │   │
│   │   │   └── webhooks/           # 메신저 Webhook
│   │   │       ├── telegram.py
│   │   │       ├── meta.py         # Instagram + FB + WhatsApp
│   │   │       ├── line.py
│   │   │       └── kakao.py
│   │   │
│   │   ├── services/               # 비즈니스 로직
│   │   │   ├── auth_service.py
│   │   │   ├── clinic_service.py
│   │   │   ├── conversation_service.py
│   │   │   ├── message_service.py
│   │   │   ├── procedure_service.py
│   │   │   ├── payment_service.py
│   │   │   ├── crm_service.py
│   │   │   ├── satisfaction_service.py
│   │   │   ├── settlement_service.py
│   │   │   └── translation_service.py
│   │   │
│   │   ├── messenger/              # 메신저 어댑터 (전략 패턴)
│   │   │   ├── base.py             # AbstractMessengerAdapter
│   │   │   ├── telegram.py         # TelegramAdapter
│   │   │   ├── instagram.py        # InstagramAdapter
│   │   │   ├── facebook.py         # FacebookAdapter
│   │   │   ├── whatsapp.py         # WhatsAppAdapter
│   │   │   ├── line.py             # LineAdapter
│   │   │   ├── kakao.py            # KakaoAdapter
│   │   │   └── factory.py          # MessengerAdapterFactory
│   │   │
│   │   ├── ai/                     # AI 엔진 (LangChain)
│   │   │   ├── llm_router.py       # 멀티 LLM 라우팅 + Fallback
│   │   │   ├── chains/
│   │   │   │   ├── knowledge_chain.py    # 레이어1: 지식
│   │   │   │   ├── style_chain.py        # 레이어2: 말투/문화
│   │   │   │   ├── sales_skill_chain.py  # 레이어3: 상담 스킬
│   │   │   │   ├── response_chain.py     # 3레이어 통합 답변 생성
│   │   │   │   └── translation_chain.py  # 번역 체인
│   │   │   ├── agents/
│   │   │   │   ├── consultation_agent.py # 메인 상담 Agent
│   │   │   │   ├── tools.py             # Agent Tools
│   │   │   │   └── simulation_agent.py  # AI vs AI 시뮬레이션
│   │   │   ├── rag/
│   │   │   │   ├── vectorstore.py       # pgvector 설정
│   │   │   │   ├── embeddings.py        # 임베딩 모델
│   │   │   │   ├── retriever.py         # clinic_id 필터 Retriever
│   │   │   │   └── indexer.py           # 문서 인덱싱
│   │   │   ├── prompts/
│   │   │   │   ├── system_prompts.py
│   │   │   │   ├── cultural_prompts.py
│   │   │   │   └── sales_prompts.py
│   │   │   ├── memory/
│   │   │   │   └── conversation_memory.py
│   │   │   └── satisfaction/
│   │   │       └── analyzer.py          # 실시간 만족도 분석
│   │   │
│   │   ├── tasks/                  # Celery 비동기 작업
│   │   │   ├── celery_app.py       # Celery 설정
│   │   │   ├── crm_tasks.py        # CRM 타임라인 작업
│   │   │   ├── message_tasks.py    # 메시지 처리
│   │   │   ├── analytics_tasks.py  # 분석/점수 계산
│   │   │   └── simulation_tasks.py # AI 시뮬레이션 야간 배치
│   │   │
│   │   ├── core/                   # 핵심 유틸
│   │   │   ├── database.py         # async engine, session
│   │   │   ├── security.py         # JWT, password hashing
│   │   │   ├── exceptions.py
│   │   │   └── middleware.py       # CORS, tenant, logging, rate limit
│   │   │
│   │   └── utils/
│   │       ├── excel.py            # 엑셀 업로드/다운로드
│   │       ├── ocr.py              # 이미지 OCR
│   │       └── currency.py         # 환율 변환
│   │
│   └── tests/
│       ├── conftest.py
│       ├── test_api/
│       ├── test_services/
│       ├── test_messenger/
│       └── test_ai/
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   │
│   ├── src/
│   │   ├── app/                    # Next.js App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx            # 랜딩/로그인
│   │   │   ├── (auth)/
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── register/page.tsx
│   │   │   └── (dashboard)/
│   │   │       ├── layout.tsx      # 대시보드 레이아웃 (4패널)
│   │   │       ├── inbox/page.tsx  # 메인 채팅 (받은 메시지)
│   │   │       ├── analytics/page.tsx
│   │   │       ├── procedures/page.tsx
│   │   │       ├── crm/page.tsx
│   │   │       ├── settlements/page.tsx
│   │   │       └── settings/
│   │   │           ├── page.tsx
│   │   │           ├── procedures/page.tsx
│   │   │           ├── personas/page.tsx
│   │   │           ├── terms/page.tsx
│   │   │           └── payments/page.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn/ui 기반
│   │   │   ├── chat/
│   │   │   │   ├── ChatWindow.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   ├── ConversationList.tsx
│   │   │   │   ├── ConversationFilters.tsx
│   │   │   │   ├── CustomerInfoPanel.tsx
│   │   │   │   ├── TranslationToggle.tsx
│   │   │   │   ├── AIToggle.tsx    # AI/수동 전환
│   │   │   │   └── SuggestedReplies.tsx
│   │   │   ├── procedure/
│   │   │   │   ├── ProcedureForm.tsx
│   │   │   │   ├── ProcedureList.tsx
│   │   │   │   ├── PricingEditor.tsx
│   │   │   │   └── PerformanceScore.tsx
│   │   │   ├── crm/
│   │   │   │   ├── CRMTimeline.tsx
│   │   │   │   ├── SatisfactionChart.tsx
│   │   │   │   └── NPSGauge.tsx
│   │   │   └── common/
│   │   │       ├── Sidebar.tsx
│   │   │       ├── Header.tsx
│   │   │       └── DataTable.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useConversations.ts
│   │   │   ├── useAuth.ts
│   │   │   └── useSatisfaction.ts
│   │   │
│   │   ├── lib/
│   │   │   ├── api-client.ts       # Axios 인스턴스 + 인터셉터
│   │   │   ├── websocket.ts
│   │   │   └── utils.ts
│   │   │
│   │   ├── stores/                 # Zustand 상태 관리
│   │   │   ├── auth-store.ts
│   │   │   ├── conversation-store.ts
│   │   │   └── ui-store.ts
│   │   │
│   │   └── types/
│   │       ├── api.ts
│   │       ├── conversation.ts
│   │       ├── procedure.ts
│   │       └── payment.ts
│   │
│   └── public/
│
└── infra/
    ├── azure/
    │   ├── main.bicep               # Azure IaC
    │   └── modules/
    │       ├── container-apps.bicep
    │       ├── database.bicep
    │       ├── redis.bicep
    │       └── storage.bicep
    └── docker/
        └── nginx.conf
```

---

## 4. 메시지 수신→AI 답변 전체 플로우

```
[고객] ─── 메신저 앱에서 메시지 전송 ───►

  1. 메신저 API → Webhook 호출
     POST /api/webhooks/{messenger_type}

  2. Webhook Handler
     ├── 요청 검증 (서명 확인)
     ├── StandardMessage 변환 (어댑터 패턴)
     ├── Customer upsert (신규면 생성)
     ├── Conversation upsert (신규면 생성)
     ├── Message DB 저장 (원문)
     └── Celery 태스크 디스패치 → process_incoming_message.delay(message_id)

  3. Celery Worker: process_incoming_message
     ├── 3a. 번역 파이프라인
     │   ├── 언어 감지 (고객 프로필 or AI 감지)
     │   ├── 의료 용어 사전 매칭 (MedicalTerm DB)
     │   └── LangChain TranslationChain → 한국어 번역 저장
     │
     ├── 3b. 에스컬레이션 체크
     │   ├── 키워드 감지 ("부작용", "환불", "아파요" 등)
     │   ├── LLM 문맥 분석 (필요시)
     │   └── 위급 판정 → 수퍼바이저 알림 + 고객에게 안내 메시지
     │       (AI 자동 답변 중단, 사람 모드 전환)
     │
     ├── 3c. AI 답변 생성 (에스컬레이션 아닌 경우)
     │   ├── ConsultationAgent 호출
     │   │   ├── 대화 히스토리 로드 (Memory)
     │   │   ├── Tool 사용 결정 (Agent)
     │   │   │   ├── search_procedure → RAG (pgvector)
     │   │   │   ├── search_faq → 답변 라이브러리
     │   │   │   ├── create_booking → 예약 생성
     │   │   │   ├── send_payment_link → 결제 링크 생성
     │   │   │   └── escalate_to_human → 사람 연결
     │   │   │
     │   │   ├── 3레이어 ResponseChain 실행
     │   │   │   ├── Layer 1 (지식): RAG 결과 + 클리닉 매뉴얼
     │   │   │   ├── Layer 2 (말투): 고객 나라/문화 프롬프트
     │   │   │   └── Layer 3 (스킬): 세일즈 전략 + 예약 유도 패턴
     │   │   │
     │   │   └── 최종 답변 (고객 언어)
     │   │
     │   ├── 답변 번역 (한국어 → 고객 언어, 필요시)
     │   ├── 정보 접근 권한 체크 (내부 정보 노출 여부 검증)
     │   └── 답변 DB 저장
     │
     ├── 3d. 만족도 분석
     │   ├── 언어 신호 분석
     │   ├── 행동 신호 분석 (답장 속도, 메시지 길이 등)
     │   └── 점수 업데이트 → 경고 체계 확인
     │
     └── 3e. 답변 발송
         ├── 답변 딜레이 (1~3초, 메시지 길이 비례)
         ├── "입력 중..." 표시 (메신저 API)
         ├── MessengerAdapter.send_message()
         └── WebSocket → 관리자 대시보드 실시간 업데이트

  4. 관리자 대시보드 (실시간)
     ├── 새 메시지 알림
     ├── AI 답변 표시 (원문 + 번역)
     ├── 만족도 점수 업데이트
     └── 수동 개입 가능 (AI 전환 토글)
```

---

## 5. LangChain AI 아키텍처 상세

### 5-1. 멀티 LLM 라우팅

```python
# 개념적 구조 (llm_router.py)

LLM 라우팅 전략:
├── Primary: Claude (Anthropic)
│   └── 용도: 메인 상담 답변 생성, 복잡한 상담
├── Secondary: Azure OpenAI (GPT-4o)
│   └── 용도: 번역, 분류, 만족도 분석, 임베딩
├── Tertiary: Gemini
│   └── 용도: 보조 분석, 시뮬레이션
│
├── Fallback 전략:
│   Claude 실패 → Azure OpenAI → Gemini
│
├── 비용 최적화:
│   ├── 단순 분류/감지 → GPT-4o-mini (저렴)
│   ├── 번역 → GPT-4o-mini
│   ├── 상담 답변 → Claude Sonnet
│   ├── 복잡한 의료 상담 → Claude Opus (필요시)
│   └── 임베딩 → text-embedding-3-small
│
└── LangChain 구현:
    ChatAnthropic (Claude)
    AzureChatOpenAI (GPT-4o)
    ChatGoogleGenerativeAI (Gemini)
    → with_fallbacks() 체인으로 자동 폴백
```

### 5-2. RAG 파이프라인

```
문서 인덱싱 (indexer.py):
  프로시져 허브 DB 변경 감지
  → Document 변환 (시술명, 설명, 효능, 부작용, 주의사항, 가격 등)
  → 메타데이터 태깅 (clinic_id, procedure_id, category, language)
  → Azure OpenAI 임베딩 생성
  → pgvector 저장

검색 (retriever.py):
  고객 질문 입력
  → 임베딩 변환
  → pgvector 유사도 검색 (cosine similarity)
  → clinic_id 필터 (멀티테넌시)
  → 상위 K개 문서 반환
  → 정보 접근 권한 필터 (내부 전용 정보 제거)

인덱싱 대상:
├── procedures (시술 정보) - 고객 공개용만
├── clinic_procedures (클리닉 커스터마이징) - 기본값 덮어쓰기
├── response_library (답변 라이브러리) - FAQ
├── medical_terms (의료 용어 사전)
└── conversation_skills (상담 스킬 패턴) - 내부 참조용
```

### 5-3. 3레이어 Chain 구조

```
ConsultationAgent (LangChain Agent)
│
├── Tools (Agent가 필요에 따라 호출)
│   ├── SearchProcedureTool     → RAG 검색
│   ├── SearchFAQTool           → 답변 라이브러리 검색
│   ├── GetClinicInfoTool       → 운영시간, 위치 등
│   ├── CreateBookingTool       → 예약 생성
│   ├── SendPaymentLinkTool     → 결제 링크 발송
│   ├── CheckAvailabilityTool   → 예약 가능 시간 확인
│   └── EscalateToHumanTool    → 사람 연결
│
├── ResponseChain (3레이어 통합)
│   │
│   ├── Layer 1: KnowledgeChain
│   │   ├── Input: 고객 질문 + RAG 검색 결과 + 클리닉 매뉴얼
│   │   ├── Logic: 클리닉 커스텀 > 교과서 기본값 우선순위
│   │   └── Output: 의학적으로 정확한 정보 (사실만)
│   │
│   ├── Layer 2: StyleChain
│   │   ├── Input: Layer1 결과 + 고객 국가/언어 + 문화 프로필
│   │   ├── Logic: 나라별 문화 프롬프트 적용
│   │   │   ├── 일본 → 존경어, 겸손, 간접 권유
│   │   │   ├── 중국 → 직접적, VIP, 결과 중심
│   │   │   ├── 미국 → 캐주얼, 간결, 리뷰 중심
│   │   │   └── ...
│   │   └── Output: 문화적으로 적절한 표현
│   │
│   └── Layer 3: SalesSkillChain
│       ├── Input: Layer2 결과 + 대화 컨텍스트 + 세일즈 퍼포먼스 점수
│       ├── Logic:
│       │   ├── 세일즈 퍼포먼스 높은 시술 우선 노출
│       │   ├── 예약 유도 패턴 적용
│       │   ├── 업셀링/크로스셀링 기회 감지
│       │   └── A/B 테스트 화법 선택 (Phase 11)
│       └── Output: 최종 답변 (자연스러운 세일즈 포함)
│
└── Memory (conversation_memory.py)
    ├── PostgreSQL 기반 대화 히스토리
    ├── ConversationBufferWindowMemory (최근 N턴)
    ├── ConversationSummaryMemory (오래된 대화 요약)
    └── 고객 프로필 컨텍스트 (이름, 관심 시술, 이전 예약 등)
```

### 5-4. Agent Tools 상세

```python
# 각 Tool의 역할과 입출력

SearchProcedureTool:
  입력: query (고객 질문)
  동작: RAG retriever → pgvector 검색 (clinic_id 필터)
  출력: 관련 시술 정보 (고객 공개용만)

SearchFAQTool:
  입력: query
  동작: 답변 라이브러리 검색 (RAG 또는 키워드)
  출력: 매칭된 FAQ 답변

GetClinicInfoTool:
  입력: info_type (hours, location, parking, etc.)
  동작: 클리닉 설정 DB 조회
  출력: 클리닉 운영 정보

CreateBookingTool:
  입력: procedure_id, date, time, customer_id
  동작: 예약 가능 확인 → Booking DB 생성
  출력: 예약 확인 정보

SendPaymentLinkTool:
  입력: booking_id, amount, currency
  동작: PG API → 결제 링크 생성
  출력: 결제 링크 URL

CheckAvailabilityTool:
  입력: procedure_id, preferred_dates
  동작: 예약 DB 조회 → 가용 슬롯 확인
  출력: 가능한 시간 목록

EscalateToHumanTool:
  입력: reason, urgency_level
  동작: 수퍼바이저 알림 발송 + 대화 모드 전환
  출력: 고객에게 안내 메시지
```
