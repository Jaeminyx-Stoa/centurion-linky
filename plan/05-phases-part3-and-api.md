# 05. Phase별 상세 구현 계획 (Part 3: Phase 9~11) + 전체 API 목록

---

## Phase 9: 사람다움 (자연스러운 AI)

### 목표
AI 응답의 자연스러움 극대화, 타이핑 딜레이, 페르소나, 시간대별 인사

### 9-1. 응답 딜레이 시스템

```python
# app/services/message_service.py

class HumanLikeDelay:
    """사람이 타이핑하는 것처럼 보이게 하는 딜레이"""

    @staticmethod
    def calculate_delay(response_text: str) -> float:
        """응답 텍스트 길이에 비례한 딜레이 (초)"""
        char_count = len(response_text)

        # 기본 "읽는 시간" (1~2초)
        reading_time = random.uniform(1.0, 2.0)

        # "타이핑 시간" (글자 수 기반, 분당 300자 기준)
        typing_time = min(char_count / 300 * 60, 5.0)  # 최대 5초

        # 랜덤 변동 (±0.5초)
        jitter = random.uniform(-0.5, 0.5)

        total = reading_time + typing_time + jitter
        return max(1.0, min(total, 8.0))  # 1~8초 범위

    @staticmethod
    async def send_with_delay(adapter, account, recipient_id, text):
        """딜레이 + 입력 중 표시 + 메시지 발송"""

        delay = HumanLikeDelay.calculate_delay(text)

        # 1. "입력 중..." 표시 시작
        await adapter.send_typing_indicator(account, recipient_id)

        # 2. 딜레이
        await asyncio.sleep(delay)

        # 3. 메시지 발송
        await adapter.send_message(account, recipient_id, text)
```

### 9-2. 시간대별 인사

```python
# app/ai/prompts/system_prompts.py

def get_time_greeting(customer_timezone: str, language_code: str) -> str:
    """고객 시간대 기반 인사말"""

    customer_hour = get_current_hour_in_timezone(customer_timezone)

    greetings = {
        'ja': {
            'morning': 'おはようございます☀️',     # 6~11시
            'afternoon': 'こんにちは😊',            # 12~17시
            'evening': 'こんばんは🌙',              # 18~22시
            'night': '夜遅くにありがとうございます✨', # 23~5시
        },
        'en': {
            'morning': 'Good morning! ☀️',
            'afternoon': 'Hello! 😊',
            'evening': 'Good evening! 🌙',
            'night': 'Thanks for reaching out! ✨',
        },
        # zh, vi, ko 등...
    }

    if 6 <= customer_hour < 12:
        period = 'morning'
    elif 12 <= customer_hour < 18:
        period = 'afternoon'
    elif 18 <= customer_hour < 23:
        period = 'evening'
    else:
        period = 'night'

    return greetings.get(language_code, greetings['en'])[period]
```

### 9-3. 대화 기억

```python
# app/ai/memory/conversation_memory.py

class PostgresConversationMemory:
    """PostgreSQL 기반 대화 메모리 (LangChain Memory 호환)"""

    async def load_memory(self, conversation_id: UUID) -> dict:
        # 최근 10턴 가져오기 (full messages)
        recent = await self.message_repo.get_recent(conversation_id, limit=20)

        # 이전 대화 요약 (20턴 이전은 요약으로)
        if total_count > 20:
            summary = await self._get_or_create_summary(conversation_id)
        else:
            summary = None

        # 고객 컨텍스트
        customer = await self.customer_repo.get_by_conversation(conversation_id)
        context = {
            'customer_name': customer.display_name,
            'country': customer.country_code,
            'previous_procedures': await self._get_customer_procedures(customer.id),
            'previous_bookings': await self._get_customer_bookings(customer.id),
        }

        return {
            'summary': summary,
            'recent_messages': recent,
            'customer_context': context,
        }

    async def _get_or_create_summary(self, conversation_id) -> str:
        """오래된 대화 내용 요약"""
        # LLM으로 요약 생성
        # "아래 대화 내용을 핵심만 간결하게 요약하세요:
        #  - 고객이 관심 있는 시술
        #  - 주요 질문과 답변
        #  - 예약/결제 상태
        #  - 고객의 감정/태도"
```

### 9-4. 페르소나 관리 API

```
POST   /api/v1/ai-personas                   # 페르소나 생성
GET    /api/v1/ai-personas                   # 목록
PATCH  /api/v1/ai-personas/{id}              # 수정
DELETE /api/v1/ai-personas/{id}              # 삭제
```

### 9-5. 법적 AI 고지

```python
# 신규 대화 시작 시 자동 삽입

AI_DISCLOSURE = {
    'ko': 'AI 상담사가 도와드리고 있으며, 필요시 전문 상담사가 연결됩니다.',
    'ja': 'AIアシスタントがご対応しております。必要に応じて専門スタッフにお繋ぎいたします。',
    'en': 'You are chatting with an AI assistant. A specialist can be connected if needed.',
    'zh': 'AI助手正在为您服务。如需要，可以为您转接专业顾问。',
}

# 메신저 프로필 설명 (bio/description)에도 설정
```

---

## Phase 10: 정산 관리

### 목표
클리닉별 월별 자동 정산, 세금계산서, 정산 대시보드

### 10-1. 정산 자동 계산

```python
# app/tasks/settlement_tasks.py

@celery_app.task
def generate_monthly_settlement():
    """매월 1일 자동 실행: 전월 정산 생성"""

    prev_month = get_previous_month()

    for clinic in ClinicRepo.get_all_active():
        # 전월 완료된 결제 합산
        payments = PaymentRepo.get_completed_by_period(
            clinic_id=clinic.id,
            year=prev_month.year,
            month=prev_month.month
        )

        total_amount = sum(p.amount for p in payments)
        commission = total_amount * (clinic.commission_rate / 100)
        vat = commission * 0.10  # 부가세 10%

        settlement = Settlement(
            clinic_id=clinic.id,
            period_year=prev_month.year,
            period_month=prev_month.month,
            total_payment_amount=total_amount,
            commission_rate=clinic.commission_rate,
            commission_amount=commission,
            vat_amount=vat,
            total_settlement=commission + vat,
            total_payment_count=len(payments),
            status='pending',
        )
        SettlementRepo.create(settlement)

# Beat 스케줄
beat_schedule['monthly-settlement'] = {
    'task': 'generate_monthly_settlement',
    'schedule': crontab(day_of_month=1, hour=2, minute=0),  # 매월 1일 02:00
}
```

### 10-2. 정산 관련 API

```
GET    /api/v1/settlements                    # 정산 목록
GET    /api/v1/settlements/{id}              # 정산 상세
PATCH  /api/v1/settlements/{id}/confirm       # 정산 확인
POST   /api/v1/settlements/{id}/invoice       # 세금계산서 발행
GET    /api/v1/settlements/{id}/download      # 정산서 PDF 다운로드
PATCH  /api/v1/settlements/{id}/mark-paid     # 입금 확인

# 플랫폼 관리자용
GET    /api/v1/admin/settlements              # 전체 정산 현황
GET    /api/v1/admin/settlements/summary      # 정산 요약 통계
```

---

## Phase 11: AI 고급 기능 (MVP 이후)

### 목표
A/B 테스트, 세일즈 자가 학습, 상담 퍼포먼스 점수, AI vs AI 시뮬레이션

### 11-1. A/B 테스트 엔진

```python
# 추가 테이블
# ab_tests: 테스트 정의
# ab_test_variants: 각 변형 (A안, B안)
# ab_test_results: 결과 추적

class ABTestEngine:
    async def select_variant(self, test_id, conversation_id):
        """대화에 대해 A/B 변형 선택"""
        # 해시 기반 일관적 분배 (같은 고객은 항상 같은 변형)
        variant = hash(conversation_id) % num_variants
        return variant

    async def record_outcome(self, test_id, variant_id, outcome):
        """결과 기록 (예약, 결제, 이탈 등)"""

    async def get_winner(self, test_id):
        """통계적 유의미한 승자 판별"""
        # 베이지안 A/B 테스트 또는 Chi-squared test
```

### 11-2. 세일즈 스킬 자동 학습

```python
# app/tasks/analytics_tasks.py

@celery_app.task
def analyze_sales_patterns():
    """매일 야간 실행: 세일즈 패턴 분석"""

    # 최근 30일 완료된 상담 조회
    conversations = ConversationRepo.get_completed_with_outcomes()

    for conv in conversations:
        messages = MessageRepo.get_all(conv.id)
        outcome = {
            'booked': conv.has_booking,
            'paid': conv.has_payment,
            'satisfaction': conv.satisfaction_score,
        }

        # AI 메시지별 효과 분석
        for msg in messages:
            if msg.sender_type == 'ai' and msg.ai_metadata:
                pattern = {
                    'strategy': msg.ai_metadata.get('sales_strategy'),
                    'knowledge_sources': msg.ai_metadata.get('knowledge_sources'),
                    'outcome': outcome,
                }
                PatternRepo.record(pattern)

    # 패턴 집계 → 성공률 높은 전략 강화
    top_patterns = PatternRepo.get_top_performing(limit=10)
    # → 프롬프트에 반영: "다음 패턴이 효과적입니다: ..."
```

### 11-3. 상담 퍼포먼스 점수 계산

```python
# app/tasks/analytics_tasks.py

@celery_app.task
def calculate_consultation_performance():
    """매월 말 실행: 상담 퍼포먼스 점수 계산"""

    for clinic in ClinicRepo.get_all_active():
        period = get_current_month()

        # ① 세일즈 믹스 점수 (40점)
        sold_procedures = PaymentRepo.get_sold_procedures(clinic.id, period)
        weighted_score = sum(
            cp.sales_performance_score * count
            for cp, count in sold_procedures
        ) / total_count
        sales_mix_score = (weighted_score / 100) * 40

        # ② 예약 전환률 점수 (30점)
        total_consultations = ConversationRepo.count_consultations(clinic.id, period)
        total_bookings = BookingRepo.count(clinic.id, period)
        booking_rate = total_bookings / total_consultations * 100
        booking_score = rate_to_score(booking_rate, [
            (90, 30), (80, 25), (70, 20), (60, 15), (50, 10)
        ], default=5)

        # ③ 결제 전환률 점수 (30점)
        total_payments = PaymentRepo.count_completed(clinic.id, period)
        payment_rate = total_payments / total_bookings * 100
        payment_score = rate_to_score(payment_rate, [
            (95, 30), (90, 25), (85, 20), (80, 15), (70, 10)
        ], default=5)

        performance = ConsultationPerformance(
            clinic_id=clinic.id,
            period_year=period.year,
            period_month=period.month,
            total_score=sales_mix_score + booking_score + payment_score,
            sales_mix_score=sales_mix_score,
            booking_conversion_score=booking_score,
            booking_conversion_rate=booking_rate,
            payment_conversion_score=payment_score,
            payment_conversion_rate=payment_rate,
            total_consultations=total_consultations,
            total_bookings=total_bookings,
            total_payments=total_payments,
        )
        ConsultationPerformanceRepo.upsert(performance)
```

### 11-4. AI vs AI 시뮬레이션

```python
# app/ai/agents/simulation_agent.py

class SimulationEngine:
    """AI 상담사 vs AI 고객 시뮬레이션"""

    # AI 고객 페르소나
    CUSTOMER_PERSONAS = [
        {
            'name': '유코',
            'profile': '일본인 30대 여성, 신중, 질문 많음, 가격 민감',
            'behavior': '3번 이상 확인해야 예약, 한국 미용 처음',
            'language': 'ja',
            'country': 'JP',
        },
        {
            'name': '웨이',
            'profile': '중국인 40대 남성, 직접적, 결과 중심',
            'behavior': 'VIP 대우 기대, Before/After 요구, 빠른 결정',
            'language': 'zh',
            'country': 'CN',
        },
        # 제시카 (US), 린 (VN) ...
    ]

    async def run_simulation(self, clinic_id, persona, num_rounds=20):
        """단일 시뮬레이션 세션"""

        # 상담 AI (실제 시스템과 동일)
        consultation_agent = ConsultationAgent(clinic_id=clinic_id)

        # 고객 AI
        customer_agent = self._create_customer_agent(persona)

        # 시뮬레이션 대화
        messages = []
        customer_msg = await customer_agent.start_conversation()

        for _ in range(num_rounds):
            # 상담 AI 응답
            ai_response = await consultation_agent.respond(customer_msg)
            messages.append(('ai', ai_response))

            # 고객 AI 응답
            customer_msg = await customer_agent.respond(ai_response)
            messages.append(('customer', customer_msg))

            # 종료 조건 체크 (예약 완료, 이탈 등)
            if self._is_conversation_ended(customer_msg):
                break

        # 결과 분석
        result = self._analyze_simulation(messages, persona)
        return result  # {booked, satisfaction, strategy_used, ...}

    def _create_customer_agent(self, persona):
        """AI 고객 페르소나 에이전트"""
        # LLM + 페르소나 프롬프트
        # "당신은 {persona.name}입니다. {persona.profile}
        #  행동 패턴: {persona.behavior}
        #  자연스럽게 대화하되, 설정된 성격과 행동 패턴을 따르세요.
        #  예약을 할지 말지는 상담 품질에 따라 자연스럽게 결정하세요."


# Celery 야간 배치
@celery_app.task
def run_nightly_simulations():
    """매일 밤 자동 실행"""
    engine = SimulationEngine()

    for clinic in ClinicRepo.get_all_active():
        for persona in SimulationEngine.CUSTOMER_PERSONAS:
            for _ in range(100):  # 페르소나당 100회
                run_single_simulation.delay(clinic.id, persona)

@celery_app.task
def run_single_simulation(clinic_id, persona):
    engine = SimulationEngine()
    result = engine.run_simulation(clinic_id, persona)
    SimulationResultRepo.save(result)

# Beat 스케줄
beat_schedule['nightly-simulation'] = {
    'task': 'run_nightly_simulations',
    'schedule': crontab(hour=3, minute=0),  # 매일 03:00
}
```

### Phase 11 DB 마이그레이션

```
추가 테이블: ab_tests, ab_test_variants, ab_test_results,
            consultation_performance, simulation_sessions, simulation_results
```

---

---

# 전체 API 엔드포인트 목록

## Auth
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me
```

## Clinics
```
GET    /api/v1/clinics/me                     # 내 클리닉 정보
PATCH  /api/v1/clinics/me                     # 클리닉 정보 수정
PATCH  /api/v1/clinics/me/settings            # 설정 수정
```

## Messenger Accounts
```
POST   /api/v1/messenger-accounts
GET    /api/v1/messenger-accounts
GET    /api/v1/messenger-accounts/{id}
PATCH  /api/v1/messenger-accounts/{id}
DELETE /api/v1/messenger-accounts/{id}
POST   /api/v1/messenger-accounts/{id}/test
POST   /api/v1/messenger-accounts/{id}/register-webhook
```

## Conversations
```
GET    /api/v1/conversations
GET    /api/v1/conversations/{id}
PATCH  /api/v1/conversations/{id}
GET    /api/v1/conversations/{id}/messages
POST   /api/v1/conversations/{id}/messages
POST   /api/v1/conversations/{id}/assign
POST   /api/v1/conversations/{id}/resolve
POST   /api/v1/conversations/{id}/toggle-ai
```

## Customers
```
GET    /api/v1/customers
GET    /api/v1/customers/{id}
PATCH  /api/v1/customers/{id}
GET    /api/v1/customers/{id}/history
```

## Procedures (교과서 기본값 - 플랫폼 관리자)
```
POST   /api/v1/procedures
GET    /api/v1/procedures
GET    /api/v1/procedures/{id}
PATCH  /api/v1/procedures/{id}
GET    /api/v1/procedure-categories
POST   /api/v1/procedure-categories
```

## Clinic Procedures (클리닉별 커스터마이징)
```
GET    /api/v1/clinic-procedures
POST   /api/v1/clinic-procedures
GET    /api/v1/clinic-procedures/{id}
PATCH  /api/v1/clinic-procedures/{id}
DELETE /api/v1/clinic-procedures/{id}
POST   /api/v1/clinic-procedures/{id}/reset/{field}
```

## Pricing
```
POST   /api/v1/pricing
GET    /api/v1/pricing
PATCH  /api/v1/pricing/{id}
DELETE /api/v1/pricing/{id}
GET    /api/v1/pricing/template
POST   /api/v1/pricing/import
GET    /api/v1/pricing/export
POST   /api/v1/pricing/ocr
```

## Bookings
```
POST   /api/v1/bookings
GET    /api/v1/bookings
GET    /api/v1/bookings/{id}
PATCH  /api/v1/bookings/{id}
POST   /api/v1/bookings/{id}/cancel
POST   /api/v1/bookings/{id}/complete
```

## Payments
```
POST   /api/v1/payments/create-link
POST   /api/v1/payments/request-remaining
GET    /api/v1/payments
GET    /api/v1/payments/{id}
GET    /api/v1/payments/{id}/status
GET    /api/v1/payment-settings
PATCH  /api/v1/payment-settings
POST   /api/v1/payment-settings/onboard
```

## CRM
```
GET    /api/v1/crm/dashboard
GET    /api/v1/crm/satisfaction-trend
GET    /api/v1/crm/nps
GET    /api/v1/crm/revisit-rate
GET    /api/v1/crm/events
GET    /api/v1/crm/events/{id}
PATCH  /api/v1/crm/events/{id}/cancel
GET    /api/v1/crm/surveys
GET    /api/v1/crm/surveys/summary
```

## Satisfaction (실시간)
```
GET    /api/v1/satisfaction/conversations/{id}/score
POST   /api/v1/satisfaction/{score_id}/override
GET    /api/v1/satisfaction/alerts
```

## Medical Terms
```
POST   /api/v1/medical-terms
GET    /api/v1/medical-terms
PATCH  /api/v1/medical-terms/{id}
DELETE /api/v1/medical-terms/{id}
POST   /api/v1/medical-terms/import
GET    /api/v1/medical-terms/export
```

## AI Settings
```
GET    /api/v1/ai-personas
POST   /api/v1/ai-personas
PATCH  /api/v1/ai-personas/{id}
DELETE /api/v1/ai-personas/{id}
GET    /api/v1/response-library
POST   /api/v1/response-library
PATCH  /api/v1/response-library/{id}
DELETE /api/v1/response-library/{id}
```

## Settlements
```
GET    /api/v1/settlements
GET    /api/v1/settlements/{id}
PATCH  /api/v1/settlements/{id}/confirm
POST   /api/v1/settlements/{id}/invoice
GET    /api/v1/settlements/{id}/download
PATCH  /api/v1/settlements/{id}/mark-paid
```

## Analytics
```
GET    /api/v1/analytics/overview              # 전체 요약
GET    /api/v1/analytics/conversations         # 상담 통계
GET    /api/v1/analytics/sales-performance     # 세일즈 퍼포먼스
GET    /api/v1/analytics/consultation-performance # 상담 퍼포먼스
GET    /api/v1/analytics/ab-tests              # A/B 테스트 결과
GET    /api/v1/analytics/simulation-results    # 시뮬레이션 결과
```

## Webhooks (외부 서비스 → 우리 서버)
```
POST   /api/webhooks/telegram/{account_id}
GET    /api/webhooks/meta/{account_id}         # verification
POST   /api/webhooks/meta/{account_id}
POST   /api/webhooks/line/{account_id}
POST   /api/webhooks/kakao/{account_id}
POST   /api/webhooks/payments/kingorder
POST   /api/webhooks/payments/alipay
POST   /api/webhooks/payments/stripe
```

## WebSocket
```
WS     /ws?token={jwt}
```

## Admin (플랫폼 관리자 전용)
```
GET    /api/v1/admin/clinics
GET    /api/v1/admin/settlements
GET    /api/v1/admin/settlements/summary
GET    /api/v1/admin/analytics/platform
```

---

# Phase 우선순위 및 의존 관계

```
Phase 0 (기반)
    │
    ▼
Phase 1 (메신저) ──────────────────────────────┐
    │                                          │
    ▼                                          │
Phase 2 (AI 엔진) ◄── Phase 5 (프로시져 허브)  │
    │                    │                     │
    ▼                    │                     │
Phase 3 (번역/문화)      │                     │
    │                    │                     │
    ▼                    ▼                     │
Phase 4 (UI) ◄──────────┘                     │
    │                                          │
    ├── Phase 6 (결제) ◄───────────────────────┘
    │       │
    │       ▼
    ├── Phase 7 (CRM) ◄── Phase 6 의존
    │
    ├── Phase 8 (만족도)
    │
    ├── Phase 9 (사람다움)
    │
    ├── Phase 10 (정산) ◄── Phase 6 의존
    │
    └── Phase 11 (AI 고급) ◄── Phase 2,7,8 의존

병렬 가능:
├── Phase 5 (프로시져 허브)는 Phase 1 이후 병렬 시작 가능
├── Phase 8 (만족도)과 Phase 9 (사람다움)은 병렬 가능
└── Phase 10 (정산)은 Phase 6 결제 완료 후 시작
```
