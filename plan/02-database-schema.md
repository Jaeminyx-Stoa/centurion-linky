# 02. DB 스키마 상세 설계

> PostgreSQL + pgvector, SQLAlchemy 2.0, Alembic

## 공통 규칙

- 모든 테이블: `id` (UUID, PK), `created_at`, `updated_at`
- 멀티테넌시: 대부분 `clinic_id` FK 포함 (TenantMixin)
- Soft delete: `deleted_at` (필요한 테이블만)
- 타임존: 모두 UTC 저장, 표시 시 변환

---

## 1. Core 테이블

### clinics (클리닉)

```sql
CREATE TABLE clinics (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(200) NOT NULL,          -- "데이뷰의원"
    slug            VARCHAR(100) UNIQUE NOT NULL,    -- "daybeauclinic"
    business_number VARCHAR(20),                     -- 사업자등록번호
    phone           VARCHAR(20),
    email           VARCHAR(200),
    address         TEXT,
    timezone        VARCHAR(50) DEFAULT 'Asia/Seoul',
    logo_url        VARCHAR(500),

    -- 수수료 설정
    commission_rate DECIMAL(5,2) DEFAULT 10.00,      -- 수수료율 (%)

    -- 설정 JSON (유연한 확장)
    settings        JSONB DEFAULT '{}',
    -- settings 예시:
    -- {
    --   "operating_hours": {"mon": "09:00-18:00", ...},
    --   "default_language": "ko",
    --   "supported_languages": ["ko","ja","en","zh","vi"],
    --   "parking_info": "...",
    --   "directions": "..."
    -- }

    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);
```

### users (관리자/수퍼바이저)

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id       UUID REFERENCES clinics(id),
    email           VARCHAR(200) UNIQUE NOT NULL,
    password_hash   VARCHAR(200) NOT NULL,
    name            VARCHAR(100) NOT NULL,
    role            VARCHAR(20) NOT NULL,            -- 'superadmin','admin','supervisor','staff'
    phone           VARCHAR(20),
    is_active       BOOLEAN DEFAULT true,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- superadmin: 플랫폼 관리자 (clinic_id = NULL)
-- admin: 클리닉 관리자
-- supervisor: 수퍼바이저 (AI 감독)
-- staff: 일반 직원
```

### messenger_accounts (메신저 계정)

```sql
CREATE TABLE messenger_accounts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id       UUID NOT NULL REFERENCES clinics(id),

    messenger_type  VARCHAR(20) NOT NULL,
    -- 'telegram','instagram','facebook','whatsapp','line','kakao'

    account_name    VARCHAR(200) NOT NULL,           -- "daybeauclinic_jp"
    display_name    VARCHAR(200),                    -- 표시 이름

    -- API 인증 정보 (암호화 저장)
    credentials     JSONB NOT NULL,
    -- telegram: {"bot_token": "..."}
    -- instagram/fb/whatsapp: {"page_id": "...", "access_token": "...", "app_secret": "..."}
    -- line: {"channel_id": "...", "channel_secret": "...", "access_token": "..."}
    -- kakao: {"app_key": "...", "channel_id": "..."}

    webhook_url     VARCHAR(500),                    -- 자동 생성
    webhook_secret  VARCHAR(200),                    -- Webhook 검증용

    target_countries TEXT[],                          -- 타겟 국가 ['JP','TW']

    is_active       BOOLEAN DEFAULT true,
    is_connected    BOOLEAN DEFAULT false,            -- API 연결 상태
    last_synced_at  TIMESTAMPTZ,

    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_messenger_accounts_clinic ON messenger_accounts(clinic_id);
CREATE INDEX idx_messenger_accounts_type ON messenger_accounts(messenger_type);
```

---

## 2. Messaging 테이블

### customers (외국인 고객)

```sql
CREATE TABLE customers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id       UUID NOT NULL REFERENCES clinics(id),

    -- 메신저 식별
    messenger_type  VARCHAR(20) NOT NULL,
    messenger_user_id VARCHAR(200) NOT NULL,          -- 메신저별 고유 ID

    -- 프로필
    name            VARCHAR(200),
    display_name    VARCHAR(200),                     -- 메신저 표시 이름
    profile_image   VARCHAR(500),

    -- 국가/언어
    country_code    VARCHAR(5),                       -- 'JP','CN','US','VN','TW'
    language_code   VARCHAR(10),                      -- 'ja','zh','en','vi','zh-TW'
    timezone        VARCHAR(50),

    -- 연락처 (수집 시)
    phone           VARCHAR(20),
    email           VARCHAR(200),

    -- 태그/메모
    tags            TEXT[] DEFAULT '{}',
    notes           TEXT,

    -- 통계 (캐시)
    total_bookings  INTEGER DEFAULT 0,
    total_payments  DECIMAL(15,2) DEFAULT 0,
    last_visit_at   TIMESTAMPTZ,

    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),

    UNIQUE(clinic_id, messenger_type, messenger_user_id)
);

CREATE INDEX idx_customers_clinic ON customers(clinic_id);
CREATE INDEX idx_customers_country ON customers(country_code);
```

### conversations (대화)

```sql
CREATE TABLE conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id       UUID NOT NULL REFERENCES clinics(id),
    customer_id     UUID NOT NULL REFERENCES customers(id),
    messenger_account_id UUID NOT NULL REFERENCES messenger_accounts(id),

    -- 상태
    status          VARCHAR(20) DEFAULT 'active',
    -- 'active','waiting','resolved','archived'

    -- AI/수동 모드
    ai_mode         BOOLEAN DEFAULT true,             -- true: AI 자동, false: 수동
    assigned_to     UUID REFERENCES users(id),        -- 수동 시 담당자

    -- 만족도 (실시간, 캐시)
    satisfaction_score INTEGER,                        -- 0~100
    satisfaction_level VARCHAR(10),                    -- 'green','yellow','orange','red'

    -- 메타데이터
    last_message_at TIMESTAMPTZ,
    last_message_preview TEXT,                        -- 마지막 메시지 미리보기
    unread_count    INTEGER DEFAULT 0,

    -- 대화 요약 (AI 생성)
    summary         TEXT,
    detected_intents TEXT[],                          -- ['price_inquiry','booking','complaint']

    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_conversations_clinic ON conversations(clinic_id);
CREATE INDEX idx_conversations_status ON conversations(clinic_id, status);
CREATE INDEX idx_conversations_last_msg ON conversations(clinic_id, last_message_at DESC);
CREATE INDEX idx_conversations_satisfaction ON conversations(clinic_id, satisfaction_level);
```

### messages (메시지)

```sql
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id),
    clinic_id       UUID NOT NULL REFERENCES clinics(id),  -- 빠른 필터용

    -- 발신자
    sender_type     VARCHAR(10) NOT NULL,             -- 'customer','ai','staff'
    sender_id       UUID,                             -- customer_id or user_id

    -- 메시지 내용
    content         TEXT NOT NULL,                    -- 원문
    content_type    VARCHAR(20) DEFAULT 'text',       -- 'text','image','file','payment_link','booking_card'

    -- 번역
    original_language VARCHAR(10),                    -- 원문 언어
    translated_content TEXT,                          -- 한국어 번역 (고객 메시지) 또는 외국어 번역 (직원 메시지)
    translated_language VARCHAR(10),                  -- 번역된 언어

    -- 메신저 정보
    messenger_type  VARCHAR(20),
    messenger_message_id VARCHAR(200),                -- 메신저 측 메시지 ID

    -- AI 메타데이터 (AI가 보낸 경우)
    ai_metadata     JSONB,
    -- {
    --   "model": "claude-sonnet-4-5",
    --   "confidence": 0.92,
    --   "knowledge_sources": ["procedure:botox", "faq:pricing"],
    --   "sales_strategy": "부위 질문 → 맞춤 가격 → 예약 유도",
    --   "langsmith_trace_id": "..."
    -- }

    -- 첨부파일
    attachments     JSONB DEFAULT '[]',
    -- [{"type": "image", "url": "...", "thumbnail": "..."}]

    -- 상태
    is_read         BOOLEAN DEFAULT false,
    read_at         TIMESTAMPTZ,
    is_deleted      BOOLEAN DEFAULT false,

    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_messages_clinic ON messages(clinic_id, created_at DESC);
```

---

## 3. AI 설정 테이블

### ai_personas (AI 상담사 페르소나)

```sql
CREATE TABLE ai_personas (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id       UUID NOT NULL REFERENCES clinics(id),

    name            VARCHAR(100) NOT NULL,            -- "미나" (상담사 이름)
    language_code   VARCHAR(10) NOT NULL,             -- 대상 언어

    personality     TEXT,                              -- 성격 설명
    tone            VARCHAR(50),                       -- 'friendly','professional','casual'
    greeting_morning TEXT,                             -- 아침 인사
    greeting_afternoon TEXT,
    greeting_evening TEXT,

    system_prompt_override TEXT,                       -- 커스텀 시스템 프롬프트

    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);
```

### cultural_profiles (나라별 문화 프로필)

```sql
CREATE TABLE cultural_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_code    VARCHAR(5) NOT NULL UNIQUE,       -- 'JP','CN','US','VN','TW'
    country_name    VARCHAR(100),

    -- 응대 스타일 프롬프트
    style_prompt    TEXT NOT NULL,
    -- 예: "일본 고객: 존경어 철저, 겸손 표현, 직접 권유 피하기..."

    -- 선호 표현
    preferred_expressions JSONB,
    avoided_expressions JSONB,

    -- 이모지 사용 수준
    emoji_level     VARCHAR(10) DEFAULT 'moderate',   -- 'none','minimal','moderate','heavy'

    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);
```

### response_library (답변 라이브러리)

```sql
CREATE TABLE response_library (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id       UUID NOT NULL REFERENCES clinics(id),

    category        VARCHAR(50) NOT NULL,             -- 'pricing','booking','location','procedure','aftercare','foreigner'
    subcategory     VARCHAR(50),

    question_ko     TEXT NOT NULL,                    -- 질문 (한국어)
    answer_ko       TEXT NOT NULL,                    -- 답변 (한국어)

    -- 다국어 답변 (직접 입력 또는 AI 번역)
    translations    JSONB DEFAULT '{}',
    -- {"ja": {"question": "...", "answer": "..."}, "en": {...}}

    -- 검색용
    keywords        TEXT[],

    is_active       BOOLEAN DEFAULT true,
    sort_order      INTEGER DEFAULT 0,

    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_response_library_clinic ON response_library(clinic_id, category);
```

---

## 4. 프로시져 허브 테이블

### procedure_categories (시술 카테고리)

```sql
CREATE TABLE procedure_categories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name_ko         VARCHAR(100) NOT NULL,            -- "보톡스"
    name_en         VARCHAR(100),
    name_ja         VARCHAR(100),
    name_zh         VARCHAR(100),
    slug            VARCHAR(100) UNIQUE NOT NULL,
    parent_id       UUID REFERENCES procedure_categories(id),
    sort_order      INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

### procedures (시술 정보 - 교과서 기본값)

```sql
CREATE TABLE procedures (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id     UUID REFERENCES procedure_categories(id),

    -- 기본 정보 (다국어)
    name_ko         VARCHAR(200) NOT NULL,
    name_en         VARCHAR(200),
    name_ja         VARCHAR(200),
    name_zh         VARCHAR(200),
    name_vi         VARCHAR(200),

    slug            VARCHAR(200) UNIQUE NOT NULL,

    -- 시술 설명
    description_ko  TEXT,
    description_en  TEXT,
    effects_ko      TEXT,                             -- 효능효과

    -- 시간 관련 (교과서 기본값)
    duration_minutes INTEGER,                         -- 시술 소요 시간
    effect_duration  VARCHAR(100),                    -- "3~6개월"
    downtime_days   INTEGER,                          -- 다운타임
    min_interval_days INTEGER,                        -- 최소 시술 간격

    -- 부작용
    common_side_effects TEXT,                         -- 흔한 부작용
    rare_side_effects TEXT,                           -- 드문 부작용
    dangerous_side_effects TEXT,                      -- 위험 부작용 (고지 필수)

    -- 주의사항
    precautions_before TEXT,                          -- 시술 전
    precautions_during TEXT,                          -- 시술 중
    precautions_after TEXT,                           -- 시술 후

    -- 통증/마취
    pain_level      INTEGER,                          -- 1~10
    pain_type       VARCHAR(100),                     -- "찌릿/따끔"
    anesthesia_options TEXT,                          -- 가능한 마취 종류
    anesthesia_details JSONB,                         -- 마취 상세 정보

    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);
```

### clinic_procedures (클리닉별 시술 커스터마이징)

```sql
CREATE TABLE clinic_procedures (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id       UUID NOT NULL REFERENCES clinics(id),
    procedure_id    UUID NOT NULL REFERENCES procedures(id),

    -- 클리닉이 덮어쓴 값들 (NULL이면 교과서 기본값 사용)
    custom_description TEXT,
    custom_effects  TEXT,
    custom_duration_minutes INTEGER,
    custom_effect_duration VARCHAR(100),
    custom_downtime_days INTEGER,
    custom_min_interval_days INTEGER,
    custom_precautions_before TEXT,
    custom_precautions_during TEXT,
    custom_precautions_after TEXT,
    custom_pain_level INTEGER,
    custom_anesthesia_options TEXT,

    -- 연계 시술
    cross_sell_procedure_ids UUID[],                  -- 같이 받으면 좋은
    upsell_procedure_ids UUID[],                      -- 업셀링 대상
    incompatible_procedure_ids UUID[],                -- 같이 받으면 안 되는
    sequence_notes  TEXT,                             -- 시술 순서 주의사항

    -- 비즈니스 데이터 (내부용, 고객 비노출)
    material_cost   DECIMAL(10,2),                    -- 재료비
    difficulty_score INTEGER CHECK (difficulty_score BETWEEN 1 AND 5),
    clinic_preference INTEGER CHECK (clinic_preference BETWEEN 1 AND 3),
    -- 1: ⭐ 추천, 2: 🔵 보통, 3: ⚪ 비추천

    -- 세일즈 퍼포먼스 점수 (자동 계산)
    sales_performance_score DECIMAL(5,2),

    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),

    UNIQUE(clinic_id, procedure_id)
);

CREATE INDEX idx_clinic_procedures_clinic ON clinic_procedures(clinic_id);
CREATE INDEX idx_clinic_procedures_score ON clinic_procedures(clinic_id, sales_performance_score DESC);
```

### procedure_pricing (시술 수가)

```sql
CREATE TABLE procedure_pricing (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_procedure_id UUID NOT NULL REFERENCES clinic_procedures(id),
    clinic_id       UUID NOT NULL REFERENCES clinics(id),

    -- 가격
    regular_price   DECIMAL(12,2) NOT NULL,           -- 정가 (KRW)
    event_price     DECIMAL(12,2),                    -- 이벤트가
    discount_rate   DECIMAL(5,2),                     -- 할인율 (자동 계산)

    -- 이벤트 기간
    event_start_date DATE,
    event_end_date  DATE,

    -- 패키지
    is_package      BOOLEAN DEFAULT false,
    package_details JSONB,                            -- 패키지 구성 상세

    -- 외화 가격 (자동 환산 or 직접 입력)
    prices_by_currency JSONB DEFAULT '{}',
    -- {"JPY": 15000, "USD": 120, "CNY": 800}

    -- 할인율 경고
    discount_warning BOOLEAN DEFAULT false,           -- 49% 초과 여부

    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_pricing_clinic ON procedure_pricing(clinic_id);
```

---

## 5. 예약 & 결제 테이블

### bookings (예약)

```sql
CREATE TABLE bookings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id       UUID NOT NULL REFERENCES clinics(id),
    customer_id     UUID NOT NULL REFERENCES customers(id),
    conversation_id UUID REFERENCES conversations(id),
    clinic_procedure_id UUID REFERENCES clinic_procedures(id),

    -- 예약 정보
    booking_date    DATE NOT NULL,
    booking_time    TIME NOT NULL,

    -- 상태
    status          VARCHAR(20) DEFAULT 'pending',
    -- 'pending','confirmed','completed','cancelled','no_show'

    -- 금액
    total_amount    DECIMAL(12,2),
    currency        VARCHAR(5) DEFAULT 'KRW',
    deposit_amount  DECIMAL(12,2),                    -- 예약금
    remaining_amount DECIMAL(12,2),                   -- 잔금

    -- 메모
    notes           TEXT,
    cancellation_reason TEXT,

    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_bookings_clinic ON bookings(clinic_id, booking_date);
CREATE INDEX idx_bookings_customer ON bookings(customer_id);
CREATE INDEX idx_bookings_status ON bookings(clinic_id, status);
```

### payments (결제)

```sql
CREATE TABLE payments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id       UUID NOT NULL REFERENCES clinics(id),
    booking_id      UUID REFERENCES bookings(id),
    customer_id     UUID NOT NULL REFERENCES customers(id),

    -- 결제 정보
    payment_type    VARCHAR(20) NOT NULL,             -- 'deposit','remaining','full','additional'
    amount          DECIMAL(12,2) NOT NULL,
    currency        VARCHAR(5) DEFAULT 'KRW',

    -- PG 정보
    pg_provider     VARCHAR(50),                      -- 'kingorder','aliexpress','stripe'
    pg_payment_id   VARCHAR(200),                     -- PG사 결제 ID
    payment_method  VARCHAR(50),                      -- 'card','line_pay','kakao_pay','alipay','apple_pay'

    -- QR/결제 링크
    payment_link    VARCHAR(500),
    qr_code_url     VARCHAR(500),
    link_expires_at TIMESTAMPTZ,

    -- 상태
    status          VARCHAR(20) DEFAULT 'pending',
    -- 'pending','link_sent','processing','completed','failed','refunded','cancelled'

    paid_at         TIMESTAMPTZ,

    -- 메신저로 발송 여부
    sent_via_messenger BOOLEAN DEFAULT false,
    sent_at         TIMESTAMPTZ,

    -- 영수증
    receipt_url     VARCHAR(500),
    receipt_sent    BOOLEAN DEFAULT false,

    metadata        JSONB DEFAULT '{}',

    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_payments_clinic ON payments(clinic_id, created_at DESC);
CREATE INDEX idx_payments_booking ON payments(booking_id);
CREATE INDEX idx_payments_status ON payments(clinic_id, status);
```

---

## 6. CRM 테이블

### crm_events (CRM 이벤트/스케줄)

```sql
CREATE TABLE crm_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id       UUID NOT NULL REFERENCES clinics(id),
    customer_id     UUID NOT NULL REFERENCES customers(id),
    payment_id      UUID REFERENCES payments(id),
    booking_id      UUID REFERENCES bookings(id),

    -- 이벤트 타입
    event_type      VARCHAR(30) NOT NULL,
    -- 'receipt','review_request','aftercare','survey_1','survey_2','survey_3','revisit_reminder'

    -- 스케줄
    scheduled_at    TIMESTAMPTZ NOT NULL,              -- 발송 예정 시간
    executed_at     TIMESTAMPTZ,                       -- 실제 발송 시간

    -- 상태
    status          VARCHAR(20) DEFAULT 'scheduled',
    -- 'scheduled','sent','completed','cancelled','failed'

    -- 내용
    message_content TEXT,

    -- 결과
    response        JSONB,                             -- 고객 응답 (설문 결과 등)

    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_crm_events_schedule ON crm_events(scheduled_at) WHERE status = 'scheduled';
CREATE INDEX idx_crm_events_clinic ON crm_events(clinic_id, event_type);
```

### satisfaction_surveys (만족도 조사)

```sql
CREATE TABLE satisfaction_surveys (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id       UUID NOT NULL REFERENCES clinics(id),
    customer_id     UUID NOT NULL REFERENCES customers(id),
    booking_id      UUID REFERENCES bookings(id),
    crm_event_id    UUID REFERENCES crm_events(id),

    -- 조사 차수
    survey_round    INTEGER NOT NULL,                  -- 1, 2, 3
    -- 1차: 직후, 2차: 7일, 3차: 14일

    -- 만족도 점수
    satisfaction_score INTEGER CHECK (satisfaction_score BETWEEN 1 AND 5),

    -- 2차: 재방문 의사
    revisit_intention VARCHAR(10),                     -- 'yes','maybe','no'

    -- 3차: NPS
    nps_score       INTEGER CHECK (nps_score BETWEEN 0 AND 10),

    -- 추가 피드백
    feedback_text   TEXT,

    -- 부작용/불편사항 (2차)
    side_effects_reported TEXT,

    responded_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_surveys_clinic ON satisfaction_surveys(clinic_id, survey_round);
CREATE INDEX idx_surveys_customer ON satisfaction_surveys(customer_id);
```

---

## 7. 실시간 만족도 & 분석 테이블

### satisfaction_scores (대화 중 실시간 만족도)

```sql
CREATE TABLE satisfaction_scores (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id),
    clinic_id       UUID NOT NULL REFERENCES clinics(id),

    -- 점수 (0~100)
    score           INTEGER NOT NULL,
    level           VARCHAR(10) NOT NULL,              -- 'green','yellow','orange','red'

    -- 분석 상세
    language_signals JSONB,                            -- 언어 신호 분석
    behavior_signals JSONB,                            -- 행동 신호 분석
    flow_signals    JSONB,                             -- 대화 흐름 신호

    -- 수퍼바이저 교정
    supervisor_override INTEGER,                       -- 수퍼바이저가 교정한 점수
    supervisor_note TEXT,
    supervised_by   UUID REFERENCES users(id),
    supervised_at   TIMESTAMPTZ,

    -- 알림 발송 여부
    alert_sent      BOOLEAN DEFAULT false,
    alert_sent_at   TIMESTAMPTZ,

    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_satisfaction_conversation ON satisfaction_scores(conversation_id, created_at DESC);
```

### consultation_performance (상담 퍼포먼스 - 월별)

```sql
CREATE TABLE consultation_performance (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id       UUID NOT NULL REFERENCES clinics(id),
    period_year     INTEGER NOT NULL,
    period_month    INTEGER NOT NULL,

    -- 상담 퍼포먼스 점수 (100점 만점)
    total_score     DECIMAL(5,2),

    -- 세일즈 믹스 (40점)
    sales_mix_score DECIMAL(5,2),

    -- 예약 전환률 (30점)
    booking_conversion_score DECIMAL(5,2),
    booking_conversion_rate DECIMAL(5,2),              -- 실제 전환률 (%)
    total_consultations INTEGER,
    total_bookings  INTEGER,

    -- 결제 전환률 (30점)
    payment_conversion_score DECIMAL(5,2),
    payment_conversion_rate DECIMAL(5,2),
    total_payments  INTEGER,

    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),

    UNIQUE(clinic_id, period_year, period_month)
);
```

---

## 8. 정산 테이블

### settlements (월별 정산)

```sql
CREATE TABLE settlements (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id       UUID NOT NULL REFERENCES clinics(id),

    period_year     INTEGER NOT NULL,
    period_month    INTEGER NOT NULL,

    -- 금액
    total_payment_amount DECIMAL(15,2),                -- 총 결제액
    commission_rate DECIMAL(5,2),                      -- 수수료율
    commission_amount DECIMAL(15,2),                   -- 수수료 금액
    vat_amount      DECIMAL(15,2),                     -- 부가세
    total_settlement DECIMAL(15,2),                    -- 총 정산 금액

    -- 건수
    total_payment_count INTEGER,

    -- 상태
    status          VARCHAR(20) DEFAULT 'pending',
    -- 'pending','confirmed','invoice_sent','paid'

    -- 세금계산서
    invoice_number  VARCHAR(50),
    invoice_issued_at TIMESTAMPTZ,

    -- 입금
    paid_at         TIMESTAMPTZ,

    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),

    UNIQUE(clinic_id, period_year, period_month)
);
```

---

## 9. 의료 용어 사전 테이블

### medical_terms (다국어 의료 용어)

```sql
CREATE TABLE medical_terms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id       UUID,                              -- NULL이면 글로벌 기본값

    term_ko         VARCHAR(200) NOT NULL,             -- 한국어
    term_en         VARCHAR(200),
    term_ja         VARCHAR(200),
    term_zh         VARCHAR(200),                      -- 중국어 간체
    term_zh_tw      VARCHAR(200),                      -- 중국어 번체
    term_vi         VARCHAR(200),

    category        VARCHAR(50),                       -- 'procedure','symptom','body_part','equipment'

    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_medical_terms_clinic ON medical_terms(clinic_id);
CREATE INDEX idx_medical_terms_ko ON medical_terms(term_ko);
```

---

## 10. pgvector 테이블 (RAG용)

```sql
-- pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE embeddings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id       UUID REFERENCES clinics(id),       -- NULL이면 글로벌

    -- 소스 참조
    source_type     VARCHAR(30) NOT NULL,
    -- 'procedure','clinic_procedure','response_library','medical_term','conversation_skill'
    source_id       UUID NOT NULL,

    -- 임베딩
    content         TEXT NOT NULL,                     -- 원문 텍스트
    embedding       vector(1536),                      -- text-embedding-3-small 차원

    -- 메타데이터 (필터링용)
    metadata        JSONB DEFAULT '{}',
    -- {"category": "botox", "language": "ko", "access_level": "public"}

    created_at      TIMESTAMPTZ DEFAULT now()
);

-- HNSW 인덱스 (빠른 유사도 검색)
CREATE INDEX idx_embeddings_vector ON embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_embeddings_clinic ON embeddings(clinic_id, source_type);
```

---

## ER 다이어그램 요약 (관계)

```
clinics ─┬── users
         ├── messenger_accounts
         ├── customers ─── conversations ─── messages
         ├── clinic_procedures ─── procedure_pricing
         │        └── procedures (교과서 기본값)
         ├── bookings ─── payments
         ├── crm_events ─── satisfaction_surveys
         ├── satisfaction_scores
         ├── consultation_performance
         ├── settlements
         ├── response_library
         ├── ai_personas
         ├── medical_terms
         └── embeddings (pgvector)
```
