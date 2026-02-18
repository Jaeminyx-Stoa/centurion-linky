# 03. Phase별 상세 구현 계획 (Part 1: Phase 0~4)

---

## Phase 0: 프로젝트 기반 구축

### 목표
프로젝트 스캐폴딩, 개발 환경, 인증, DB 기본 설정

### 구현 상세

#### 0-1. Docker Compose 개발 환경

```yaml
# docker-compose.dev.yml 구성
services:
  db:         PostgreSQL 16 + pgvector 확장
  redis:      Redis 7
  rabbitmq:   RabbitMQ 3 (management 플러그인 포함)
  backend:    FastAPI (uvicorn, hot reload)
  celery-worker: Celery worker
  celery-beat:   Celery beat (스케줄러)
  frontend:   Next.js (dev server)
```

#### 0-2. Backend 초기 설정

```
app/config.py
├── pydantic-settings 기반
├── 환경변수: DATABASE_URL, REDIS_URL, RABBITMQ_URL
├── AZURE_OPENAI_*, ANTHROPIC_API_KEY, GOOGLE_API_KEY
├── LANGSMITH_API_KEY, LANGSMITH_PROJECT
├── JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY
├── BLOB_STORAGE_CONNECTION_STRING
└── 각 메신저별 기본 설정

app/core/database.py
├── create_async_engine (asyncpg)
├── async_sessionmaker
├── get_db() 의존성
└── pgvector 확장 초기화

app/core/security.py
├── password_hash (bcrypt via passlib)
├── create_access_token / create_refresh_token
├── verify_token
└── get_current_user 의존성

app/core/middleware.py
├── TenantMiddleware: 요청에서 clinic_id 추출 (JWT 기반)
├── LoggingMiddleware: 요청/응답 로깅
├── RateLimitMiddleware: Redis 기반 rate limiting
└── CORS 설정 (frontend origin 허용)

app/core/exceptions.py
├── AppException (base)
├── NotFoundError
├── PermissionError
├── ValidationError
└── global exception handler 등록
```

#### 0-3. 인증 시스템 (auth)

```
API 엔드포인트:
  POST   /api/v1/auth/register        # 클리닉 + 관리자 동시 등록
  POST   /api/v1/auth/login            # 로그인 → JWT 발급
  POST   /api/v1/auth/refresh          # 토큰 갱신
  GET    /api/v1/auth/me               # 현재 유저 정보

인증 플로우:
  1. 클리닉 등록 시 → Clinic 생성 + User(role=admin) 생성
  2. 로그인 → access_token (15분) + refresh_token (7일)
  3. 모든 API 요청에 Bearer token 필수
  4. 토큰에 user_id, clinic_id, role 포함
  5. 역할별 권한 체크 데코레이터: @require_role('admin','supervisor')
```

#### 0-4. Alembic 초기 마이그레이션

```
alembic init → 기본 설정
첫 번째 마이그레이션:
  - clinics
  - users
  - pgvector 확장 생성
이후 Phase마다 마이그레이션 추가
```

#### 0-5. Frontend 초기 설정

```
Next.js 15 프로젝트 생성 (App Router)
├── Tailwind CSS 설정
├── shadcn/ui 설치 (Button, Input, Card, Dialog, Table, Tabs 등)
├── Zustand 설치 (상태 관리)
├── Axios 인스턴스 설정 (인터셉터: JWT 자동 첨부, 401 → refresh)
├── 로그인/회원가입 페이지
├── 대시보드 레이아웃 (사이드바 + 메인 컨텐츠)
└── 라우트 가드 (미인증 → 로그인 리다이렉트)
```

#### 0-6. WebSocket 기본 설정

```
Backend: FastAPI WebSocket endpoint
  /ws?token={jwt_token}
  ├── 연결 시 토큰 검증
  ├── clinic_id 기반 채널 구독
  └── 이벤트 타입: new_message, message_update, satisfaction_alert, notification

Frontend: useWebSocket 커스텀 훅
  ├── 자동 연결/재연결
  ├── 이벤트 리스너 등록
  └── 상태 관리 연동 (Zustand store 업데이트)
```

---

## Phase 1: 메신저 통합 - 코어

### 목표
메신저 어댑터 패턴 구현, Telegram 먼저 → Meta → LINE → Kakao 순서

### 1-1. 메신저 어댑터 추상 인터페이스

```python
# app/messenger/base.py

class StandardMessage:
    """모든 메신저에서 통일된 메시지 포맷"""
    messenger_type: str          # 'telegram','instagram',...
    messenger_message_id: str    # 메신저 측 메시지 ID
    messenger_user_id: str       # 메신저 측 유저 ID
    account_id: UUID             # 우리 시스템의 messenger_account ID
    content: str                 # 텍스트 내용
    content_type: str            # 'text','image','file','sticker'
    attachments: list            # 첨부파일
    timestamp: datetime
    raw_data: dict               # 원본 Webhook 데이터

class AbstractMessengerAdapter(ABC):
    """메신저 어댑터 인터페이스"""

    @abstractmethod
    async def verify_webhook(request) -> bool:
        """Webhook 서명 검증"""

    @abstractmethod
    async def parse_webhook(request) -> list[StandardMessage]:
        """Webhook 요청을 StandardMessage로 변환"""

    @abstractmethod
    async def send_message(
        account: MessengerAccount,
        recipient_id: str,
        text: str,
        attachments: list = None
    ) -> str:  # returns messenger_message_id
        """메시지 발송"""

    @abstractmethod
    async def send_typing_indicator(
        account: MessengerAccount,
        recipient_id: str
    ):
        """입력 중... 표시"""

    @abstractmethod
    async def get_user_profile(
        account: MessengerAccount,
        user_id: str
    ) -> dict:
        """유저 프로필 조회"""
```

### 1-2. MessengerAdapterFactory

```python
# app/messenger/factory.py

class MessengerAdapterFactory:
    _adapters = {
        'telegram': TelegramAdapter,
        'instagram': InstagramAdapter,
        'facebook': FacebookAdapter,
        'whatsapp': WhatsAppAdapter,
        'line': LineAdapter,
        'kakao': KakaoAdapter,
    }

    @staticmethod
    def get_adapter(messenger_type: str) -> AbstractMessengerAdapter:
        return MessengerAdapterFactory._adapters[messenger_type]()
```

### 1-3. Telegram 구현 (1순위)

```
TelegramAdapter:
├── verify_webhook: secret_token 헤더 검증
├── parse_webhook: Update → StandardMessage 변환
├── send_message: Bot API sendMessage
├── send_typing_indicator: sendChatAction
└── get_user_profile: getChat

Webhook 등록:
  POST /api/webhooks/telegram/{account_id}
  → Telegram setWebhook API로 URL 등록

Webhook Handler:
  1. 서명 검증
  2. account_id로 MessengerAccount 조회
  3. clinic_id 확인
  4. TelegramAdapter.parse_webhook() → StandardMessage
  5. message_service.process_incoming(standard_message)
```

### 1-4. Meta 플랫폼 구현 (2순위: Instagram + Facebook + WhatsApp)

```
MetaAdapter (공통 Base):
├── verify_webhook: X-Hub-Signature-256 HMAC 검증
├── Meta Graph API v21.0 사용
└── Instagram, Facebook, WhatsApp 공통 로직

InstagramAdapter(MetaAdapter):
├── parse_webhook: messaging 이벤트 → StandardMessage
├── send_message: Instagram Send API
├── 특이사항: 24시간 응답 윈도우 (Human Agent Tag 필요)
└── 이미지/스토리 답장 지원

FacebookAdapter(MetaAdapter):
├── parse_webhook: messaging 이벤트
└── send_message: Send API

WhatsAppAdapter(MetaAdapter):
├── parse_webhook: WhatsApp Cloud API 이벤트
├── send_message: WhatsApp Cloud API
└── 특이사항: 24시간 세션 윈도우, Template 메시지

공통 Webhook:
  POST /api/webhooks/meta/{account_id}
  GET  /api/webhooks/meta/{account_id}  (verification challenge)
```

### 1-5. LINE 구현 (3순위)

```
LineAdapter:
├── verify_webhook: X-Line-Signature HMAC-SHA256
├── LINE Messaging API v2
├── parse_webhook: Event → StandardMessage
├── send_message: Reply API (reply token) + Push API
├── send_typing_indicator: 지원 안 함 (Loading animation은 가능)
└── 특이사항: reply token 30초 유효

Webhook:
  POST /api/webhooks/line/{account_id}
```

### 1-6. KakaoTalk 구현 (4순위)

```
KakaoAdapter:
├── 카카오톡 채널 API (비즈메시지)
├── verify_webhook: 서명 검증
├── parse_webhook: 카카오 이벤트 → StandardMessage
├── send_message: 알림톡/친구톡 API
└── 특이사항: 알림톡은 템플릿 기반, 친구톡은 자유

Webhook:
  POST /api/webhooks/kakao/{account_id}
```

### 1-7. 메시지 수신 서비스 (공통)

```python
# app/services/message_service.py

class MessageService:
    async def process_incoming(self, msg: StandardMessage):
        """메시지 수신 공통 처리"""

        # 1. Customer upsert
        customer = await self.customer_repo.upsert(
            clinic_id=msg.clinic_id,
            messenger_type=msg.messenger_type,
            messenger_user_id=msg.messenger_user_id
        )

        # 2. Conversation upsert
        conversation = await self.conversation_repo.get_or_create(
            customer_id=customer.id,
            messenger_account_id=msg.account_id
        )

        # 3. Message 저장
        message = await self.message_repo.create(
            conversation_id=conversation.id,
            sender_type='customer',
            content=msg.content,
            content_type=msg.content_type,
            messenger_message_id=msg.messenger_message_id,
            original_language=customer.language_code
        )

        # 4. WebSocket으로 대시보드에 실시간 알림
        await self.ws_manager.broadcast_to_clinic(
            clinic_id=msg.clinic_id,
            event='new_message',
            data=message.to_dict()
        )

        # 5. Celery 태스크 디스패치 (AI 처리)
        if conversation.ai_mode:
            process_ai_response.delay(message.id)

        # 6. 대화 메타 업데이트
        await self.conversation_repo.update_last_message(
            conversation.id, message
        )
```

### 1-8. 메신저 계정 관리 API

```
POST   /api/v1/messenger-accounts           # 계정 등록
GET    /api/v1/messenger-accounts           # 목록 조회
GET    /api/v1/messenger-accounts/{id}      # 상세
PATCH  /api/v1/messenger-accounts/{id}      # 수정
DELETE /api/v1/messenger-accounts/{id}      # 삭제
POST   /api/v1/messenger-accounts/{id}/test # 연결 테스트
POST   /api/v1/messenger-accounts/{id}/register-webhook  # Webhook 등록
```

### Phase 1 DB 마이그레이션

```
추가 테이블: messenger_accounts, customers, conversations, messages
```

---

## Phase 2: AI 답변 엔진

### 목표
LangChain 기반 3레이어 AI 답변 시스템, RAG, Agent 구축

### 2-1. LLM 라우터 설정

```python
# app/ai/llm_router.py

구성:
├── ChatAnthropic (Claude Sonnet 4.5)
│   └── 메인 상담 답변
├── AzureChatOpenAI (GPT-4o)
│   └── 번역, 분류, 보조 분석
├── AzureChatOpenAI (GPT-4o-mini)
│   └── 가벼운 작업 (키워드 추출, 언어 감지, 감정 분류)
├── ChatGoogleGenerativeAI (Gemini 2.5 Flash)
│   └── 시뮬레이션, 보조
├── AzureOpenAIEmbeddings (text-embedding-3-small)
│   └── RAG 임베딩
│
└── with_fallbacks():
    consultation_llm = claude.with_fallbacks([gpt4o, gemini])
    light_llm = gpt4o_mini.with_fallbacks([gemini_flash])
```

### 2-2. RAG 구축

```python
# app/ai/rag/vectorstore.py
PGVector 설정:
├── connection: DATABASE_URL
├── collection_name: "medical_knowledge"
├── embedding_function: AzureOpenAIEmbeddings
└── distance_strategy: CosineDistance

# app/ai/rag/retriever.py
ClinicFilteredRetriever (Custom Retriever):
├── base_retriever: PGVector.as_retriever(search_kwargs={"k": 5})
├── 추가 필터: clinic_id (멀티테넌시)
├── 추가 필터: access_level = 'public' (내부 정보 제외)
└── 추가 필터: source_type 지정 가능

# app/ai/rag/indexer.py
DocumentIndexer:
├── index_procedure(procedure, clinic_procedure):
│   → 시술 정보를 Document로 변환
│   → 클리닉 커스텀 값 우선, 없으면 기본값
│   → metadata: {clinic_id, procedure_id, category, access_level: 'public'}
│   → 임베딩 생성 → pgvector 저장
│
├── index_response_library(item):
│   → FAQ 답변을 Document로 변환
│   → metadata: {clinic_id, category, subcategory}
│
├── index_medical_terms():
│   → 의료 용어 사전을 Document로 변환
│   → 다국어 검색 가능하도록 각 언어별 인덱싱
│
├── reindex_clinic(clinic_id):
│   → 해당 클리닉의 모든 문서 재인덱싱
│   → 프로시져 허브 변경 시 트리거
│
└── delete_clinic_documents(clinic_id):
    → 클리닉 삭제/비활성화 시
```

### 2-3. 3레이어 Chain 구현

```python
# app/ai/chains/knowledge_chain.py

KnowledgeChain:
  Input: {query, rag_results, clinic_manual}
  Prompt:
    """
    당신은 {clinic_name}의 의료 지식 전문가입니다.

    [지식 우선순위]
    1순위: 클리닉 자체 매뉴얼 (아래 제공)
    2순위: 검색된 의학 정보 (아래 제공)

    [클리닉 매뉴얼]
    {clinic_manual}

    [검색된 의학 정보]
    {rag_results}

    [규칙]
    - 클리닉 매뉴얼에 있는 정보가 교과서와 다르면 클리닉 매뉴얼을 따른다
    - 내부 전용 정보(재료비, 마진, 난이도 등)는 절대 포함하지 않는다
    - 확실하지 않은 의료 정보는 "담당 의료진에게 확인해 드리겠습니다"로 안내
    - 위험한 부작용 정보는 반드시 포함한다

    고객 질문: {query}

    정확한 의학 정보만 추출하세요 (표현이나 세일즈 전략은 포함하지 마세요):
    """
  Output: 의학적 사실 정보 (raw facts)


# app/ai/chains/style_chain.py

StyleChain:
  Input: {knowledge_output, country_code, language_code, cultural_profile, persona}
  Prompt:
    """
    당신은 {persona_name}입니다. ({persona_personality})

    [문화 스타일 가이드 - {country_name}]
    {cultural_profile.style_prompt}

    [선호 표현]
    {cultural_profile.preferred_expressions}

    [피해야 할 표현]
    {cultural_profile.avoided_expressions}

    [이모지 사용 수준: {cultural_profile.emoji_level}]

    [시간대 인사: {time_greeting}]

    아래 정보를 {language_code} 언어로, 위 문화 스타일에 맞게 자연스럽게 표현하세요:
    {knowledge_output}
    """
  Output: 문화적으로 적절한 표현


# app/ai/chains/sales_skill_chain.py

SalesSkillChain:
  Input: {styled_output, conversation_history, sales_context}
  Prompt:
    """
    당신은 미용의료 상담 전문가입니다.

    [현재 대화 상황]
    {conversation_history (최근 5턴)}

    [세일즈 전략]
    - 추천 우선순위 시술: {top_procedures_by_sales_score}
    - 현재 이벤트: {active_events}
    - 크로스셀링 기회: {cross_sell_options}

    [상담 패턴]
    - 가격 질문 → 부위 먼저 질문 → 맞춤 가격 → 예약 유도
    - 망설임 감지 → 이벤트/혜택 강조
    - 경쟁 병원 언급 → 차별점 강조
    - "생각해볼게요" → 부담 없는 상담 예약 제안

    [규칙]
    - 노골적 세일즈 금지 (자연스러운 흐름 유지)
    - 고가 시술 문의 시 부담 적은 대안도 함께 제시
    - 예약 유도는 자연스러운 질문 형태로
    - 내부 세일즈 점수, 마진 정보 절대 노출 금지

    아래 답변에 자연스러운 세일즈 전략을 적용하세요:
    {styled_output}
    """
  Output: 최종 답변 (세일즈 전략 포함)


# app/ai/chains/response_chain.py

ResponseChain (3레이어 통합):
  1. KnowledgeChain 실행 → facts
  2. StyleChain 실행 → styled_response
  3. SalesSkillChain 실행 → final_response
  4. 정보 접근 권한 최종 검증 (내부 정보 누출 체크)
  5. return final_response
```

### 2-4. Consultation Agent

```python
# app/ai/agents/consultation_agent.py

ConsultationAgent (LangChain Agent):
├── LLM: consultation_llm (Claude + fallback)
├── Tools: [SearchProcedure, SearchFAQ, GetClinicInfo,
│          CreateBooking, SendPaymentLink, CheckAvailability,
│          EscalateToHuman]
├── Memory: PostgreSQL 기반 ConversationMemory
│
├── System Prompt:
│   """
│   당신은 {clinic_name}의 AI 상담사 {persona_name}입니다.
│   외국인 고객의 미용의료 상담을 담당합니다.
│
│   [핵심 원칙]
│   1. 정확한 의료 정보 제공 (지식 레이어 기반)
│   2. 고객 문화/언어에 맞는 자연스러운 응대
│   3. 예약 전환을 위한 자연스러운 유도
│   4. 위급 상황 감지 시 즉시 사람 연결
│
│   [절대 하지 않을 것]
│   - 내부 비즈니스 정보 노출 (마진, 재료비, 세일즈 점수 등)
│   - 확실하지 않은 의료 정보 단정
│   - AI임을 숨기려는 시도 (물어보면 솔직히 안내)
│   - 다른 클리닉 비방
│   """
│
└── Agent 실행 플로우:
    1. 고객 메시지 수신
    2. Memory에서 대화 히스토리 로드
    3. Agent가 Tool 사용 여부 결정
       ├── 시술 관련 질문 → SearchProcedure
       ├── FAQ 질문 → SearchFAQ
       ├── 예약 요청 → CheckAvailability → CreateBooking
       ├── 결제 요청 → SendPaymentLink
       └── 위급 상황 → EscalateToHuman
    4. ResponseChain으로 3레이어 답변 생성
    5. 답변 반환
```

### 2-5. 에스컬레이션 (사람 연결) 로직

```python
# app/ai/agents/tools.py - EscalateToHumanTool 내부

에스컬레이션 트리거:
├── 키워드 기반 (빠른 감지):
│   ko: "부작용","환불","아파요","피가","신고","불만","고소"
│   ja: "副作用","返金","痛い","血","クレーム"
│   en: "side effect","refund","pain","blood","complaint","lawsuit"
│   zh: "副作用","退款","疼","血","投诉"
│
├── LLM 기반 (문맥 감지):
│   light_llm에게 분류 요청:
│   "이 메시지가 다음 중 어디에 해당하는지 판단하세요:
│    1. 일반 문의 (AI 처리 가능)
│    2. 주의 필요 (모니터링 권장)
│    3. 즉시 사람 연결 (컴플레인/부작용/의료사고/환불)"
│
└── 에스컬레이션 실행:
    1. conversation.ai_mode = false
    2. 수퍼바이저에게 알림 (WebSocket + 이메일/문자)
    3. 고객에게 자동 메시지:
       "{persona_name}: 더 정확한 안내를 위해
        전문 상담사가 곧 연결됩니다. 잠시만 기다려주세요😊"
```

### Phase 2 DB 마이그레이션

```
추가 테이블: ai_personas, cultural_profiles, response_library, embeddings
기존 테이블 수정: conversations에 ai_mode, satisfaction 관련 컬럼 추가
```

---

## Phase 3: 자동 번역 + 문화 레이어

### 목표
미용의료 전문 번역 파이프라인, 용어 사전, 언어 자동 감지

### 3-1. 번역 파이프라인

```python
# app/ai/chains/translation_chain.py

번역 플로우 (수신: 외국어 → 한국어):
  1. 언어 감지
     ├── 고객 프로필에 언어 설정 있으면 그대로 사용
     └── 없으면 light_llm으로 감지 + 고객 프로필 업데이트

  2. 의료 용어 사전 매칭 (Pre-processing)
     ├── MedicalTerm DB에서 해당 언어 용어 검색
     ├── 매칭된 용어를 마크업: "ボトックス" → "[TERM:보톡스]"
     └── 사전 매칭으로 전문 용어 번역 정확도 보장

  3. AI 번역 (LangChain TranslationChain)
     ├── LLM: gpt4o_mini (빠르고 저렴)
     ├── Prompt: 미용의료 맥락을 고려한 번역
     │   "[TERM:xxx]로 표시된 부분은 이미 번역된 전문 용어입니다.
     │    그대로 사용하세요. 나머지를 한국어로 자연스럽게 번역하세요."
     └── 결과: 한국어 번역

  4. Message.translated_content에 저장


번역 플로우 (발신: 한국어 → 외국어):
  1. 직원/AI 답변 (한국어 또는 이미 고객 언어)
  2. 용어 사전 매칭
  3. AI 번역 → 고객 언어
  4. 메신저로 발송
```

### 3-2. 용어 사전 관리 API

```
POST   /api/v1/medical-terms           # 용어 추가
GET    /api/v1/medical-terms           # 목록 (필터: category, language)
PATCH  /api/v1/medical-terms/{id}      # 수정
DELETE /api/v1/medical-terms/{id}      # 삭제
POST   /api/v1/medical-terms/import    # 엑셀 일괄 등록
GET    /api/v1/medical-terms/export    # 엑셀 다운로드
```

### 3-3. 문화 프로필 시드 데이터

```python
# 초기 데이터 (alembic seed 또는 별도 스크립트)

cultural_profiles = [
    {
        "country_code": "JP",
        "style_prompt": """
        일본 고객 응대 규칙:
        - 반드시 존경어(敬語) 사용
        - 겸손한 표현 사용 ("~させていただきます")
        - 직접적 권유 대신 간접 제안 ("~はいかがでしょうか")
        - 배려하는 톤 유지
        - 결정을 재촉하지 않음
        """,
        "emoji_level": "moderate",
    },
    {
        "country_code": "CN",
        "style_prompt": """
        중국 고객 응대 규칙:
        - 가격과 혜택을 적극적으로 강조
        - 직접적이고 명확한 표현
        - VIP 대우 느낌 ("为您专属推荐")
        - 결과 중심 (Before/After 강조)
        - 신속한 응답
        """,
        "emoji_level": "moderate",
    },
    # ... US, VN, TW 등
]
```

### Phase 3 DB 마이그레이션

```
추가 테이블: medical_terms, cultural_profiles
기존 테이블 수정: messages에 translated_content, translated_language 컬럼
```

---

## Phase 4: 관리자 UI 대시보드

### 목표
채널톡 스타일 4패널 레이아웃, 채팅 인터페이스, 실시간 업데이트

### 4-1. 대시보드 레이아웃

```
┌───────────┬────────────────┬───────────────────┬────────────┐
│           │                │                   │            │
│ Sidebar   │ ConversationList│  ChatWindow       │ CustomerPanel
│ (60px)    │ (280px)        │  (flexible)       │ (320px)    │
│           │                │                   │            │
│ 💬 받은    │ 필터 바          │ 채팅 헤더           │ 프로필      │
│    메시지  │ ┌────────────┐ │ ┌──────────────┐  │ 이름/국가   │
│           │ │ 유코        │ │ │ 메시지 버블   │  │ 채널       │
│ 👥 내부   │ │ 🇯🇵 LINE   │ │ │ (원문+번역)  │  │ 만족도     │
│    채팅   │ │ 🟢 92점    │ │ │              │  │            │
│           │ │ "보톡스..." │ │ │ AI/수동 토글  │  │ 상담이력   │
│ 📊 통계   │ ├────────────┤ │ │              │  │ 결제이력   │
│           │ │ 제시카      │ │ │ 추천 답변    │  │ 예약현황   │
│ 💉 시술   │ │ 🇺🇸 Insta  │ │ └──────────────┘  │            │
│           │ │ 🟡 74점    │ │                   │ 메모/태그  │
│ 💰 정산   │ └────────────┘ │ 입력 창            │            │
│           │                │ [메시지 입력...]    │            │
│ ⚙️ 설정   │                │ [전송]             │            │
└───────────┴────────────────┴───────────────────┴────────────┘
```

### 4-2. 핵심 컴포넌트

```
ConversationList.tsx:
├── 필터: 메신저 타입, 계정, 상태(active/waiting/resolved), 만족도
├── 정렬: 최근 메시지 시간 DESC
├── 만족도 점수 뱃지 (🟢🟡🟠🔴)
├── 메신저 아이콘 + 계정명 태그
├── 안읽은 메시지 카운트
├── 실시간 업데이트 (WebSocket)
└── 무한 스크롤

ChatWindow.tsx:
├── 메시지 버블
│   ├── 고객 메시지: 원문 + 번역 토글
│   ├── AI 메시지: [AI] 태그 표시
│   └── 직원 메시지: [직원명] 표시
├── AI/수동 전환 토글
│   ├── AI 모드: AI 자동 답변 (직원은 모니터링)
│   └── 수동 모드: 직원이 직접 입력 (AI 추천 답변 표시)
├── 추천 답변 (수동 모드 시)
│   └── AI가 3개 후보 생성 → 클릭하면 자동 입력
├── 메시지 입력 (수동 모드)
│   ├── 한국어 입력 → 고객 언어 자동 번역 미리보기
│   └── 전송 버튼
└── 실시간 업데이트 (WebSocket)

CustomerInfoPanel.tsx:
├── 프로필 (이름, 국가, 언어, 채널)
├── 만족도 점수 게이지
├── 상담 이력 (과거 대화 목록)
├── 예약 현황
├── 결제 이력
├── 메모/태그 편집
└── [사람 연결] 긴급 버튼
```

### 4-3. 대화 관련 API

```
GET    /api/v1/conversations                # 목록 (필터, 정렬, 페이지네이션)
GET    /api/v1/conversations/{id}           # 상세 (고객 정보 포함)
PATCH  /api/v1/conversations/{id}           # 상태/AI모드 변경
GET    /api/v1/conversations/{id}/messages  # 메시지 히스토리 (페이지네이션)
POST   /api/v1/conversations/{id}/messages  # 수동 메시지 전송
POST   /api/v1/conversations/{id}/assign    # 담당자 배정
POST   /api/v1/conversations/{id}/resolve   # 해결 처리

GET    /api/v1/customers/{id}               # 고객 상세
PATCH  /api/v1/customers/{id}               # 고객 정보 수정 (메모, 태그)
GET    /api/v1/customers/{id}/history       # 고객 전체 이력 (상담+예약+결제)
```

### 4-4. WebSocket 이벤트

```
Server → Client:
├── new_message:        새 메시지 (고객/AI)
├── message_translated: 번역 완료
├── ai_response_ready:  AI 답변 생성 완료
├── satisfaction_update: 만족도 점수 변경
├── satisfaction_alert:  만족도 경고 (🟠🔴)
├── conversation_update: 대화 상태 변경
└── escalation_alert:   에스컬레이션 발생

Client → Server:
├── mark_read:          메시지 읽음 처리
├── typing:             직원 입력 중
└── subscribe_clinic:   클리닉 채널 구독
```
