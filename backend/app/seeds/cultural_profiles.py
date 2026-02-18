"""Seed data for cultural profiles — one per target country."""

CULTURAL_PROFILES = [
    {
        "country_code": "JP",
        "country_name": "일본",
        "language_code": "ja",
        "style_prompt": (
            "일본 고객에게 응대합니다. 존경어(敬語)를 사용하고, 공손하며 간접적인 표현을 선호합니다. "
            "직접적인 가격 할인 언급보다 가치와 품질을 강조하세요. "
            "결정을 재촉하지 말고 충분한 정보를 제공하여 스스로 판단하게 하세요."
        ),
        "preferred_expressions": [
            "ご検討いただけますか", "お気軽にお問い合わせください",
            "ご安心ください", "丁寧にご対応いたします",
        ],
        "avoided_expressions": [
            "今すぐ決めてください", "安いです", "他より良いです",
        ],
        "emoji_level": "low",
        "formality_level": "formal",
    },
    {
        "country_code": "CN",
        "country_name": "중국",
        "language_code": "zh-CN",
        "style_prompt": (
            "중국 고객에게 응대합니다. 실용적이고 직접적인 소통을 선호합니다. "
            "시술 효과와 가격 대비 가치를 명확히 전달하세요. "
            "한국 의료 기술의 우수성과 인기를 강조하면 효과적입니다."
        ),
        "preferred_expressions": [
            "效果很好", "性价比高", "很多顾客选择", "韩国正品",
        ],
        "avoided_expressions": [
            "便宜货", "差不多", "不确定",
        ],
        "emoji_level": "medium",
        "formality_level": "polite",
    },
    {
        "country_code": "TW",
        "country_name": "대만",
        "language_code": "zh-TW",
        "style_prompt": (
            "대만 고객에게 응대합니다. 친근하고 따뜻한 소통을 선호합니다. "
            "한류 문화에 친숙하므로 K-뷰티 트렌드를 활용하세요. "
            "부드러운 톤으로 상세한 설명을 제공하세요."
        ),
        "preferred_expressions": [
            "請放心", "很自然", "很多韓國明星也做", "效果很自然",
        ],
        "avoided_expressions": [
            "整形", "開刀", "很痛",
        ],
        "emoji_level": "high",
        "formality_level": "polite",
    },
    {
        "country_code": "US",
        "country_name": "미국",
        "language_code": "en",
        "style_prompt": (
            "미국/영어권 고객에게 응대합니다. 직접적이고 투명한 소통을 선호합니다. "
            "시술 과정, 다운타임, 가격을 명확하게 안내하세요. "
            "전문적이면서도 친절한 톤을 유지하세요."
        ),
        "preferred_expressions": [
            "We'd be happy to help", "Here's what you can expect",
            "Feel free to ask", "Our experienced team",
        ],
        "avoided_expressions": [
            "You should do this", "Trust me", "Everyone does it",
        ],
        "emoji_level": "low",
        "formality_level": "polite",
    },
    {
        "country_code": "VN",
        "country_name": "베트남",
        "language_code": "vi",
        "style_prompt": (
            "베트남 고객에게 응대합니다. 친근하고 열정적인 소통을 선호합니다. "
            "한국 의료 관광의 안전성과 품질을 강조하세요. "
            "가격 정보와 패키지 혜택에 관심이 높습니다."
        ),
        "preferred_expressions": [
            "Chào bạn", "Rất an toàn", "Nhiều khách hàng hài lòng",
            "Chúng tôi hỗ trợ",
        ],
        "avoided_expressions": [
            "Phẫu thuật lớn", "Đau lắm", "Không biết",
        ],
        "emoji_level": "high",
        "formality_level": "polite",
    },
    {
        "country_code": "TH",
        "country_name": "태국",
        "language_code": "th",
        "style_prompt": (
            "태국 고객에게 응대합니다. 예의 바르고 부드러운 소통을 선호합니다. "
            "태국의 สวัสดี(사와디) 문화를 존중하며 공손하게 응대하세요. "
            "가격과 편의시설 정보를 함께 제공하면 효과적입니다."
        ),
        "preferred_expressions": [
            "สวัสดีค่ะ", "ไม่ต้องกังวลค่ะ", "ปลอดภัยค่ะ",
            "ยินดีให้บริการค่ะ",
        ],
        "avoided_expressions": [
            "แพงมาก", "ไม่รู้", "ไม่แน่ใจ",
        ],
        "emoji_level": "high",
        "formality_level": "polite",
    },
    {
        "country_code": "ID",
        "country_name": "인도네시아",
        "language_code": "id",
        "style_prompt": (
            "인도네시아 고객에게 응대합니다. 친절하고 존중하는 소통을 선호합니다. "
            "할랄(Halal) 인증 여부에 관심이 있을 수 있으므로 준비해두세요. "
            "한국 뷰티에 대한 관심이 높으며, 안전성을 강조하세요."
        ),
        "preferred_expressions": [
            "Selamat datang", "Aman dan nyaman", "Banyak pelanggan puas",
            "Kami siap membantu",
        ],
        "avoided_expressions": [
            "Tidak tahu", "Mahal sekali", "Harus operasi",
        ],
        "emoji_level": "medium",
        "formality_level": "polite",
    },
]

MEDICAL_TERMS_SEED = [
    {
        "term_ko": "보톡스",
        "translations": {
            "ja": "ボトックス", "en": "Botox", "zh-CN": "肉毒素",
            "zh-TW": "肉毒桿菌", "vi": "Botox", "th": "โบท็อกซ์", "id": "Botox",
        },
        "category": "procedure",
        "description": "보툴리눔 톡신 주사 시술",
    },
    {
        "term_ko": "필러",
        "translations": {
            "ja": "フィラー", "en": "Filler", "zh-CN": "玻尿酸",
            "zh-TW": "玻尿酸", "vi": "Filler", "th": "ฟิลเลอร์", "id": "Filler",
        },
        "category": "material",
        "description": "히알루론산 필러 시술",
    },
    {
        "term_ko": "히알루론산",
        "translations": {
            "ja": "ヒアルロン酸", "en": "Hyaluronic acid", "zh-CN": "透明质酸",
            "zh-TW": "透明質酸", "vi": "Axit hyaluronic", "th": "ไฮยาลูรอนิก", "id": "Asam hialuronat",
        },
        "category": "material",
    },
    {
        "term_ko": "리프팅",
        "translations": {
            "ja": "リフティング", "en": "Lifting", "zh-CN": "提拉",
            "zh-TW": "拉提", "vi": "Nâng cơ", "th": "ลิฟติ้ง", "id": "Lifting",
        },
        "category": "procedure",
    },
    {
        "term_ko": "쌍꺼풀",
        "translations": {
            "ja": "二重まぶた", "en": "Double eyelid", "zh-CN": "双眼皮",
            "zh-TW": "雙眼皮", "vi": "Mắt hai mí", "th": "ตาสองชั้น", "id": "Kelopak mata ganda",
        },
        "category": "procedure",
    },
    {
        "term_ko": "코성형",
        "translations": {
            "ja": "鼻整形", "en": "Rhinoplasty", "zh-CN": "鼻整形",
            "zh-TW": "鼻整形", "vi": "Nâng mũi", "th": "เสริมจมูก", "id": "Rhinoplasti",
        },
        "category": "procedure",
    },
    {
        "term_ko": "물광주사",
        "translations": {
            "ja": "水光注射", "en": "Skin booster", "zh-CN": "水光针",
            "zh-TW": "水光針", "vi": "Tiêm dưỡng da", "th": "ฉีดน้ำแร่", "id": "Skin booster",
        },
        "category": "procedure",
    },
    {
        "term_ko": "레이저",
        "translations": {
            "ja": "レーザー", "en": "Laser", "zh-CN": "激光",
            "zh-TW": "雷射", "vi": "Laser", "th": "เลเซอร์", "id": "Laser",
        },
        "category": "procedure",
    },
    {
        "term_ko": "상담",
        "translations": {
            "ja": "カウンセリング", "en": "Consultation", "zh-CN": "咨询",
            "zh-TW": "諮詢", "vi": "Tư vấn", "th": "ปรึกษา", "id": "Konsultasi",
        },
        "category": "general",
    },
    {
        "term_ko": "예약",
        "translations": {
            "ja": "予約", "en": "Reservation", "zh-CN": "预约",
            "zh-TW": "預約", "vi": "Đặt lịch", "th": "จองคิว", "id": "Reservasi",
        },
        "category": "general",
    },
]
