"""Tests that MessageService integrates translation on incoming messages."""

import uuid

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chains.translation_chain import TranslationChain
from app.models import Clinic, MedicalTerm
from app.services.term_service import load_term_dict


@pytest.fixture
async def intg_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="통합테스트의원", slug="intg-test")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest.fixture
async def seeded_terms(db: AsyncSession) -> None:
    db.add(MedicalTerm(
        id=uuid.uuid4(),
        clinic_id=None,
        term_ko="보톡스",
        translations={"ja": "ボトックス", "en": "Botox", "zh-CN": "肉毒素"},
        category="procedure",
    ))
    db.add(MedicalTerm(
        id=uuid.uuid4(),
        clinic_id=None,
        term_ko="필러",
        translations={"ja": "フィラー", "en": "Filler"},
        category="material",
    ))
    await db.commit()


class TestTranslationIntegration:
    """End-to-end: load terms from DB → build chain → translate."""

    async def test_load_and_translate_japanese(
        self, db: AsyncSession, seeded_terms
    ):
        term_dict = await load_term_dict(db)

        fake_translation_llm = GenericFakeChatModel(
            messages=iter([AIMessage(content="[TERM:보톡스]의 가격을 알려주세요")])
        )
        fake_detect_llm = GenericFakeChatModel(
            messages=iter([AIMessage(content="ja")])
        )

        chain = TranslationChain(
            translation_llm=fake_translation_llm,
            detection_llm=fake_detect_llm,
            term_dict=term_dict,
        )

        result = await chain.translate_incoming(
            text="ボトックスの値段を教えてください",
            known_language="ja",
        )
        assert result.source_language == "ja"
        assert result.target_language == "ko"
        assert "보톡스" in result.translated_text

    async def test_load_and_translate_english(
        self, db: AsyncSession, seeded_terms
    ):
        term_dict = await load_term_dict(db)

        fake_translation_llm = GenericFakeChatModel(
            messages=iter([AIMessage(content="[TERM:보톡스]와 [TERM:필러] 가격이 어떻게 되나요?")])
        )
        fake_detect_llm = GenericFakeChatModel(
            messages=iter([AIMessage(content="en")])
        )

        chain = TranslationChain(
            translation_llm=fake_translation_llm,
            detection_llm=fake_detect_llm,
            term_dict=term_dict,
        )

        result = await chain.translate_incoming(
            text="How much is Botox and Filler?",
            known_language="en",
        )
        assert "보톡스" in result.translated_text
        assert "필러" in result.translated_text

    async def test_clinic_specific_terms_override(
        self, db: AsyncSession, seeded_terms, intg_clinic: Clinic
    ):
        # Add clinic-specific override
        db.add(MedicalTerm(
            id=uuid.uuid4(),
            clinic_id=intg_clinic.id,
            term_ko="보톡스주사",
            translations={"ja": "ボトックス"},
            category="procedure",
        ))
        await db.commit()

        term_dict = await load_term_dict(db, clinic_id=intg_clinic.id)
        # Clinic override should win
        assert term_dict["ja"]["ボトックス"] == "보톡스주사"

    async def test_outgoing_translation(
        self, db: AsyncSession, seeded_terms
    ):
        term_dict = await load_term_dict(db)

        fake_translation_llm = GenericFakeChatModel(
            messages=iter([AIMessage(content="ボトックスの料金をご案内いたします。")])
        )

        chain = TranslationChain(
            translation_llm=fake_translation_llm,
            detection_llm=GenericFakeChatModel(
                messages=iter([AIMessage(content="ko")])
            ),
            term_dict=term_dict,
        )

        result = await chain.translate_outgoing(
            text="보톡스 가격을 안내드리겠습니다.",
            target_language="ja",
        )
        assert result.target_language == "ja"
        assert result.translated_text is not None
