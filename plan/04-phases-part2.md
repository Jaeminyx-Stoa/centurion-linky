# 04. Phase별 상세 구현 계획 (Part 2: Phase 5~8)

---

## Phase 5: 프로시져 허브

### 목표
시술 정보 라이브러리 + 수가 관리 + 세일즈 퍼포먼스 점수

### 5-1. 시술 정보 관리 API

```
# 교과서 기본값 (플랫폼 관리자 전용)
POST   /api/v1/procedures                   # 시술 등록 (기본값)
GET    /api/v1/procedures                   # 시술 목록
GET    /api/v1/procedures/{id}              # 시술 상세
PATCH  /api/v1/procedures/{id}              # 시술 수정

# 카테고리
GET    /api/v1/procedure-categories         # 카테고리 목록 (트리)
POST   /api/v1/procedure-categories         # 카테고리 추가

# 클리닉별 커스터마이징
GET    /api/v1/clinic-procedures                      # 내 클리닉 시술 목록
POST   /api/v1/clinic-procedures                      # 시술 추가 (기본값에서 선택)
GET    /api/v1/clinic-procedures/{id}                 # 상세 (기본값 + 커스텀 병합 응답)
PATCH  /api/v1/clinic-procedures/{id}                 # 커스터마이징 (덮어쓰기)
DELETE /api/v1/clinic-procedures/{id}                 # 비활성화
POST   /api/v1/clinic-procedures/{id}/reset/{field}   # 특정 필드 기본값으로 리셋
```

### 5-2. 기본값 vs 커스터마이징 병합 로직

```python
# app/services/procedure_service.py

class ProcedureService:
    async def get_merged_procedure(self, clinic_procedure_id) -> dict:
        """교과서 기본값 + 클리닉 커스텀 병합"""

        cp = await self.clinic_procedure_repo.get(clinic_procedure_id)
        base = await self.procedure_repo.get(cp.procedure_id)

        merged = {}
        fields = [
            'description', 'effects', 'duration_minutes',
            'effect_duration', 'downtime_days', 'min_interval_days',
            'precautions_before', 'precautions_during', 'precautions_after',
            'pain_level', 'anesthesia_options'
        ]

        for field in fields:
            custom_value = getattr(cp, f'custom_{field}')
            base_value = getattr(base, field)
            merged[field] = {
                'value': custom_value if custom_value is not None else base_value,
                'source': 'custom' if custom_value is not None else 'default',
                'default_value': base_value,  # UI에서 "기본값: xxx" 표시용
            }

        return merged
```

### 5-3. 수가 관리 API

```
POST   /api/v1/pricing                       # 수가 등록
GET    /api/v1/pricing                       # 수가 목록
PATCH  /api/v1/pricing/{id}                  # 수가 수정
DELETE /api/v1/pricing/{id}                  # 수가 삭제

# 엑셀 업로드/다운로드
GET    /api/v1/pricing/template              # 엑셀 템플릿 다운로드
POST   /api/v1/pricing/import                # 엑셀 업로드 (일괄 등록/수정)
GET    /api/v1/pricing/export                # 현재 수가 엑셀 다운로드

# 이미지 OCR
POST   /api/v1/pricing/ocr                   # 이미지 → 가격 추출
  Request: multipart/form-data (image)
  Response: {extracted_procedures: [{name, price, event_price, period}]}
```

### 5-4. 할인율 49% 검증

```python
# app/services/pricing_service.py

class PricingService:
    async def validate_and_save(self, data: PricingCreate) -> ProcedurePricing:
        # 할인율 자동 계산
        if data.event_price and data.regular_price:
            discount_rate = (
                (data.regular_price - data.event_price)
                / data.regular_price * 100
            )
            data.discount_rate = round(discount_rate, 2)

            # 49% 초과 경고
            data.discount_warning = discount_rate > 49.0

        return await self.pricing_repo.create(data)
```

### 5-5. 세일즈 퍼포먼스 점수 계산

```python
# app/services/procedure_service.py

class SalesPerformanceCalculator:
    """
    세일즈 퍼포먼스 점수 (100점 만점) =
      분당 마진 점수 (40점) + 난이도 점수 (30점) + 클리닉 선호 점수 (30점)
    """

    async def calculate(self, clinic_id: UUID):
        procedures = await self.clinic_procedure_repo.list_by_clinic(clinic_id)

        # 1. 분당 마진 계산
        margins = []
        for p in procedures:
            pricing = await self.pricing_repo.get_active(p.id)
            if pricing and p.material_cost and p.custom_duration_minutes:
                price = pricing.event_price or pricing.regular_price
                margin_per_min = (price - p.material_cost) / p.custom_duration_minutes
                margins.append((p.id, margin_per_min))

        # 상대 순위로 점수화 (백분위 → 40점 만점)
        margins.sort(key=lambda x: x[1], reverse=True)
        margin_scores = {}
        for rank, (pid, _) in enumerate(margins):
            percentile = 1 - (rank / len(margins))
            margin_scores[pid] = round(percentile * 40, 2)

        # 2. 난이도 점수 (30점 만점)
        difficulty_map = {1: 30, 2: 24, 3: 18, 4: 12, 5: 6}

        # 3. 클리닉 선호 점수 (30점 만점)
        preference_map = {1: 30, 2: 15, 3: 0}

        # 4. 합산
        for p in procedures:
            score = (
                margin_scores.get(p.id, 20)  # 기본 20점
                + difficulty_map.get(p.difficulty_score, 18)
                + preference_map.get(p.clinic_preference, 15)
            )
            p.sales_performance_score = min(score, 100)
            await self.clinic_procedure_repo.update(p)

    # 트리거: 수가/비즈니스데이터 변경 시 자동 재계산
```

### 5-6. 엑셀 처리

```python
# app/utils/excel.py

class ProcedureExcelHandler:
    """프로시져 허브 엑셀 폼"""

    def generate_template(self, clinic_id) -> BytesIO:
        """다운로드용 엑셀 템플릿 생성"""
        # openpyxl로 양식 생성
        # 시트 구성:
        #   Sheet 1: 시술 정보 (이름, 설명, 시간, 부작용 등)
        #   Sheet 2: 수가 (정가, 이벤트가, 기간 등)
        #   Sheet 3: 비즈니스 데이터 (재료비, 난이도, 선호등급)

    async def import_data(self, clinic_id, file: UploadFile):
        """엑셀 업로드 → DB 반영"""
        # 1. 파싱
        # 2. 밸리데이션 (필수값, 할인율 검증 등)
        # 3. DB upsert (기존 시술이면 업데이트, 없으면 생성)
        # 4. 세일즈 퍼포먼스 점수 재계산
        # 5. RAG 인덱스 재생성 트리거

    async def export_data(self, clinic_id) -> BytesIO:
        """현재 데이터 엑셀 다운로드"""
```

### 5-7. OCR 처리

```python
# app/utils/ocr.py

class EventPosterOCR:
    """이벤트 포스터 이미지 → 시술/가격 추출"""

    async def extract(self, image_bytes: bytes) -> list[dict]:
        # Azure AI Vision (OCR) 또는 LLM 기반 추출
        # GPT-4o에 이미지 전달 → 구조화된 데이터 추출
        #
        # Prompt:
        # "이 이미지는 미용의료 이벤트 포스터입니다.
        #  다음 정보를 JSON으로 추출하세요:
        #  - 시술명
        #  - 정가
        #  - 이벤트가
        #  - 이벤트 기간
        #  ..."
        #
        # → [{name: "보톡스", regular_price: 150000, event_price: 120000, ...}]
```

### 5-8. RAG 인덱스 자동 갱신

```python
# 프로시져 허브 데이터 변경 시 RAG 인덱스 자동 갱신

트리거 포인트:
├── clinic_procedures 생성/수정/삭제
├── procedure_pricing 변경
├── response_library 변경
└── medical_terms 변경

→ Celery 태스크: reindex_documents.delay(clinic_id, source_type, source_id)
→ DocumentIndexer.reindex_document() 실행
→ pgvector 업데이트
```

### Phase 5 DB 마이그레이션

```
추가 테이블: procedure_categories, procedures, clinic_procedures, procedure_pricing
```

---

## Phase 6: QR 결제 시스템

### 목표
전체 결제를 QR/결제 링크로 통일, PG 연동, 결제 플로우

### 6-1. 결제 서비스 아키텍처

```python
# app/services/payment_service.py

결제 어댑터 패턴 (메신저와 동일):

AbstractPaymentProvider:
├── create_payment_link(amount, currency, metadata) → {link, qr_url}
├── verify_webhook(request) → bool
├── parse_webhook(request) → PaymentResult
├── get_payment_status(payment_id) → status
└── refund(payment_id, amount) → RefundResult

KingOrderProvider(AbstractPaymentProvider):
├── 킹오더브라더스 API 연동
├── 지원: 카카오페이, 네이버페이, 카드, LINE Pay
└── 한국/일본/대만 결제

AlipayProvider(AbstractPaymentProvider):
├── 알리엑스 API 연동
└── 중국 Alipay 결제

StripeProvider(AbstractPaymentProvider):
├── Stripe API 연동
├── 글로벌 카드, Apple Pay
└── 백업용

PaymentProviderFactory:
├── 나라/결제수단에 따라 적절한 Provider 선택
├── 'JP' + 'line_pay' → KingOrderProvider
├── 'CN' + 'alipay' → AlipayProvider
├── fallback → StripeProvider
└── 클리닉 결제 설정 참조
```

### 6-2. 결제 플로우 (예약금)

```
1. AI가 예약 확정 시:
   → ConsultationAgent.CreateBookingTool 실행
   → Booking 생성 (status: pending)

2. 예약금 결제 요청:
   → ConsultationAgent.SendPaymentLinkTool 실행
   → PaymentService.create_payment_link()
     ├── 고객 국가 → 결제수단 결정
     ├── PG Provider 선택
     ├── 결제 링크 생성
     ├── Payment 레코드 생성 (status: link_sent)
     └── QR 코드 생성

3. 메신저로 결제 카드 발송:
   ┌─────────────────────────┐
   │ 💳 데이뷰의원 예약금      │
   │ 보톡스 - 이마             │
   │ 2026.03.10 (화) 14:00   │
   │ 예약금: ¥3,000           │
   │ [결제하기]               │
   └─────────────────────────┘

4. 고객 결제 완료:
   → PG Webhook 수신
   → POST /api/webhooks/payments/{provider}
   → PaymentService.handle_webhook()
     ├── Payment 상태 → completed
     ├── Booking 상태 → confirmed
     ├── 고객에게 확인 메시지 발송
     ├── 관리자에게 알림 (WebSocket)
     └── CRM 이벤트 스케줄링 트리거 (Phase 7)
```

### 6-3. 결제 플로우 (원내 잔금)

```
1. 시술 완료 후:
   → 직원이 대시보드에서 [잔금 결제 요청] 클릭

2. API 호출:
   POST /api/v1/payments/request-remaining
   {
     "booking_id": "...",
     "amount": 47000,
     "currency": "JPY"
   }

3. 서버:
   → 결제 링크 생성
   → 고객 메신저로 자동 발송
   → Payment 레코드 생성

4. 고객 결제 완료:
   → PG Webhook → Payment completed
   → CRM 타임라인 시작 (영수증, 리뷰 요청, 만족도 조사 등)
```

### 6-4. 결제 관련 API

```
# 결제
POST   /api/v1/payments/create-link           # 결제 링크 생성
POST   /api/v1/payments/request-remaining     # 잔금 결제 요청
GET    /api/v1/payments                       # 결제 목록
GET    /api/v1/payments/{id}                  # 결제 상세
GET    /api/v1/payments/{id}/status           # 결제 상태 확인

# Webhook (PG사별)
POST   /api/webhooks/payments/kingorder       # 킹오더 Webhook
POST   /api/webhooks/payments/alipay          # 알리페이 Webhook
POST   /api/webhooks/payments/stripe          # Stripe Webhook

# 예약
POST   /api/v1/bookings                       # 예약 생성
GET    /api/v1/bookings                       # 예약 목록
GET    /api/v1/bookings/{id}                  # 예약 상세
PATCH  /api/v1/bookings/{id}                  # 예약 수정
POST   /api/v1/bookings/{id}/cancel           # 예약 취소
POST   /api/v1/bookings/{id}/complete         # 시술 완료 처리

# 결제 설정
GET    /api/v1/payment-settings               # 결제 설정 조회
PATCH  /api/v1/payment-settings               # 결제 설정 수정
POST   /api/v1/payment-settings/onboard       # PG 온보딩 시작
```

### Phase 6 DB 마이그레이션

```
추가 테이블: bookings, payments
```

---

## Phase 7: CRM 자동화

### 목표
결제 완료 → CRM 타임라인 자동 실행, 만족도 조사, 리뷰 요청, 재시술 리마인더

### 7-1. CRM 이벤트 스케줄링

```python
# app/services/crm_service.py

class CRMService:
    async def schedule_crm_timeline(self, payment_id: UUID):
        """결제 완료 시 CRM 타임라인 전체 스케줄링"""

        payment = await self.payment_repo.get(payment_id)
        booking = await self.booking_repo.get(payment.booking_id)
        now = datetime.utcnow()

        events = [
            # 즉시: 영수증 발송
            CRMEvent(
                event_type='receipt',
                scheduled_at=now,
            ),

            # 즉시~1시간: 리뷰 요청
            CRMEvent(
                event_type='review_request',
                scheduled_at=now + timedelta(minutes=30),
            ),

            # 3시간 후: 시술 후 주의사항
            CRMEvent(
                event_type='aftercare',
                scheduled_at=now + timedelta(hours=3),
            ),

            # 당일 (6시간 후): 만족도 1차 조사
            CRMEvent(
                event_type='survey_1',
                scheduled_at=now + timedelta(hours=6),
            ),

            # 7일 후: 만족도 2차 조사
            CRMEvent(
                event_type='survey_2',
                scheduled_at=now + timedelta(days=7),
            ),

            # 14일 후: 만족도 3차 조사 + NPS
            CRMEvent(
                event_type='survey_3',
                scheduled_at=now + timedelta(days=14),
            ),

            # 효과 지속기간 후: 재시술 리마인더
            # (프로시져 허브에서 지속기간 조회)
            CRMEvent(
                event_type='revisit_reminder',
                scheduled_at=now + timedelta(days=reminder_days),
            ),
        ]

        for event in events:
            event.clinic_id = payment.clinic_id
            event.customer_id = payment.customer_id
            event.payment_id = payment_id
            event.booking_id = payment.booking_id
            await self.crm_event_repo.create(event)
```

### 7-2. Celery Beat 스케줄러

```python
# app/tasks/crm_tasks.py

@celery_app.task
def execute_scheduled_crm_events():
    """매 1분마다 실행: 예정된 CRM 이벤트 처리"""

    events = CRMEventRepo.get_due_events(
        status='scheduled',
        scheduled_at__lte=datetime.utcnow()
    )

    for event in events:
        try:
            process_crm_event.delay(event.id)
        except Exception:
            event.status = 'failed'
            event.save()

# Celery Beat 설정
beat_schedule = {
    'check-crm-events': {
        'task': 'execute_scheduled_crm_events',
        'schedule': 60.0,  # 매 60초
    },
}


@celery_app.task
def process_crm_event(event_id: str):
    """개별 CRM 이벤트 처리"""

    event = CRMEventRepo.get(event_id)
    customer = CustomerRepo.get(event.customer_id)
    conversation = ConversationRepo.get_latest(customer.id)
    adapter = MessengerAdapterFactory.get_adapter(customer.messenger_type)

    match event.event_type:
        case 'receipt':
            # 영수증 발송
            receipt_message = generate_receipt(event.payment_id)
            adapter.send_message(account, customer.messenger_user_id, receipt_message)

        case 'review_request':
            # 리뷰 요청 (만족 고객에게만)
            # 직전 만족도 조사가 4~5점인 경우에만
            message = generate_review_request(customer, event.booking_id)
            adapter.send_message(account, customer.messenger_user_id, message)

        case 'aftercare':
            # 시술 후 주의사항 (프로시져 허브에서 조회)
            aftercare = get_aftercare_info(event.booking_id, customer.language_code)
            adapter.send_message(account, customer.messenger_user_id, aftercare)

        case 'survey_1' | 'survey_2' | 'survey_3':
            # 만족도 조사 메시지
            round_num = int(event.event_type[-1])
            survey_message = generate_survey(round_num, customer)
            adapter.send_message(account, customer.messenger_user_id, survey_message)

        case 'revisit_reminder':
            # 재시술 리마인더
            reminder = generate_revisit_reminder(customer, event.booking_id)
            adapter.send_message(account, customer.messenger_user_id, reminder)

    event.status = 'sent'
    event.executed_at = datetime.utcnow()
    event.save()
```

### 7-3. 만족도 조사 응답 처리

```python
# 고객이 만족도 조사에 응답하면:

수신 메시지 분석:
├── 이모지 응답 감지: 😍=5, 😊=4, 😐=3, 😕=2, 😢=1
├── 숫자 응답 감지: "4", "5점" 등
├── 텍스트 응답: AI가 만족도 추론
│
└── SatisfactionSurvey 레코드 생성
    ├── survey_round
    ├── satisfaction_score (1~5)
    ├── revisit_intention (2차)
    ├── nps_score (3차, 0~10)
    └── feedback_text

트리거 후속 작업:
├── 만족(4~5점) + 1차 → 리뷰 요청 CRM 이벤트 활성화
├── 불만(1~2점) → 수퍼바이저 알림 즉시 발송
├── NPS 9~10 → 추천 코드/링크 자동 제공
└── CRM 대시보드 실시간 업데이트
```

### 7-4. CRM 관련 API

```
# CRM 대시보드
GET    /api/v1/crm/dashboard                  # 전체 현황
GET    /api/v1/crm/satisfaction-trend          # 만족도 추이 (1차/2차/3차)
GET    /api/v1/crm/nps                        # NPS 현황
GET    /api/v1/crm/revisit-rate               # 재방문율

# CRM 이벤트
GET    /api/v1/crm/events                     # 이벤트 목록
GET    /api/v1/crm/events/{id}               # 이벤트 상세
PATCH  /api/v1/crm/events/{id}/cancel         # 이벤트 취소

# 만족도 조사
GET    /api/v1/crm/surveys                    # 조사 결과 목록
GET    /api/v1/crm/surveys/summary            # 요약 통계
```

### Phase 7 DB 마이그레이션

```
추가 테이블: crm_events, satisfaction_surveys
```

---

## Phase 8: 고객 만족도 실시간 측정

### 목표
대화 중 실시간 만족도 분석, 경고 체계, 수퍼바이저 피드백 학습

### 8-1. 만족도 분석기

```python
# app/ai/satisfaction/analyzer.py

class SatisfactionAnalyzer:
    """대화 중 실시간 만족도 분석"""

    async def analyze(self, conversation_id: UUID, new_message: Message) -> int:
        """0~100 점수 반환"""

        conversation = await self.conversation_repo.get(conversation_id)
        recent_messages = await self.message_repo.get_recent(conversation_id, limit=10)

        # 1. 언어 신호 분석 (가장 정확, 가중치 40%)
        language_score = self._analyze_language_signals(recent_messages)

        # 2. 행동 신호 분석 (꽤 정확, 가중치 35%)
        behavior_score = self._analyze_behavior_signals(recent_messages)

        # 3. 대화 흐름 분석 (보통, 가중치 25%)
        flow_score = self._analyze_flow_signals(recent_messages)

        total = (
            language_score * 0.40
            + behavior_score * 0.35
            + flow_score * 0.25
        )

        return round(total)

    def _analyze_language_signals(self, messages) -> int:
        """언어 신호 분석"""
        customer_messages = [m for m in messages if m.sender_type == 'customer']
        latest = customer_messages[-1] if customer_messages else None

        score = 70  # 기본 중립

        if latest:
            text = latest.content.lower()

            # 부정 감지 (다국어)
            negative_keywords = {
                'ko': ['아니요','됐어요','그만','싫어요','답답','왜 자꾸'],
                'ja': ['いいえ','結構','もういい','嫌','しつこい'],
                'en': ['no thanks','not interested','stop','annoying'],
                'zh': ['不要','算了','不需要','烦'],
            }

            positive_keywords = {
                'ko': ['좋아요','감사','궁금','네','언제','예약'],
                'ja': ['いいですね','ありがとう','予約','いつ'],
                'en': ['great','thanks','interested','when','book'],
                'zh': ['好的','谢谢','感兴趣','预约','什么时候'],
            }

            # 키워드 매칭 + 점수 조정
            # ...

            # LLM 기반 감정 분석 (정밀)
            sentiment = await self._llm_sentiment(text)
            # sentiment: 'very_positive'(+20), 'positive'(+10),
            #            'neutral'(0), 'negative'(-15), 'very_negative'(-30)

        return max(0, min(100, score))

    def _analyze_behavior_signals(self, messages) -> int:
        """행동 신호 분석"""
        score = 70

        customer_messages = [m for m in messages if m.sender_type == 'customer']
        if len(customer_messages) >= 2:
            # 답장 속도 변화
            recent_gap = (customer_messages[-1].created_at - customer_messages[-2].created_at)
            # 속도 느려짐 → 관심 ↓

            # 메시지 길이 변화
            recent_len = len(customer_messages[-1].content)
            prev_len = len(customer_messages[-2].content)
            if recent_len < prev_len * 0.3:  # 급격히 짧아짐
                score -= 15

            # 같은 질문 반복
            # → 임베딩 유사도로 반복 감지

        return max(0, min(100, score))

    def _analyze_flow_signals(self, messages) -> int:
        """대화 흐름 분석"""
        score = 70

        # 예약 방향 이동 → +20
        # 가격만 반복 질문 → -10
        # 다른 병원 언급 → -20
        # "생각해볼게요" → -15

        return max(0, min(100, score))
```

### 8-2. 경고 체계

```python
# 점수 → 레벨 매핑 + 알림

def score_to_level(score: int) -> tuple[str, str]:
    if score >= 90:
        return 'green', '완벽한 상담'
    elif score >= 70:
        return 'yellow', '정상'
    elif score >= 50:
        return 'orange', '모니터링 필요'   # → 수퍼바이저 모니터링 알림
    else:
        return 'red', '개입 권장'          # → 수퍼바이저 개입 알림

# 알림 발송:
# orange: WebSocket 알림 (대시보드에 주황색 표시)
# red: WebSocket 알림 + 이메일/문자 (긴급)
```

### 8-3. 수퍼바이저 피드백

```
POST   /api/v1/satisfaction/{score_id}/override
{
    "corrected_score": 80,
    "note": "이 고객은 원래 말이 짧아서 정상임"
}

→ SatisfactionScore.supervisor_override = 80
→ 이 피드백 데이터가 쌓이면 분석기 보정에 활용 (Phase 11)
```

### Phase 8 DB 마이그레이션

```
추가 테이블: satisfaction_scores
기존 테이블 수정: conversations에 satisfaction_score, satisfaction_level 캐시 추가
```
