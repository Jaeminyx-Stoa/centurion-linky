"""Treatment photo management service (before/after photos)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.customer import Customer
from app.models.procedure import Procedure
from app.models.treatment_photo import TreatmentPhoto


class TreatmentPhotoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_photo(
        self,
        clinic_id: uuid.UUID,
        photo_url: str,
        thumbnail_url: str | None,
        *,
        customer_id: uuid.UUID,
        photo_type: str,
        booking_id: uuid.UUID | None = None,
        procedure_id: uuid.UUID | None = None,
        description: str | None = None,
        taken_at=None,
        days_after_procedure: int | None = None,
        is_consent_given: bool = False,
        pair_id: uuid.UUID | None = None,
    ) -> TreatmentPhoto:
        photo = TreatmentPhoto(
            id=uuid.uuid4(),
            clinic_id=clinic_id,
            customer_id=customer_id,
            booking_id=booking_id,
            procedure_id=procedure_id,
            photo_type=photo_type,
            photo_url=photo_url,
            thumbnail_url=thumbnail_url,
            description=description,
            taken_at=taken_at,
            days_after_procedure=days_after_procedure,
            is_consent_given=is_consent_given,
            pair_id=pair_id,
        )
        self.db.add(photo)
        await self.db.flush()
        return photo

    async def list_photos(
        self,
        clinic_id: uuid.UUID,
        customer_id: uuid.UUID | None = None,
        booking_id: uuid.UUID | None = None,
        photo_type: str | None = None,
        portfolio_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TreatmentPhoto], int]:
        query = select(TreatmentPhoto).where(
            TreatmentPhoto.clinic_id == clinic_id
        )
        count_query = select(func.count(TreatmentPhoto.id)).where(
            TreatmentPhoto.clinic_id == clinic_id
        )

        if customer_id:
            query = query.where(TreatmentPhoto.customer_id == customer_id)
            count_query = count_query.where(TreatmentPhoto.customer_id == customer_id)
        if booking_id:
            query = query.where(TreatmentPhoto.booking_id == booking_id)
            count_query = count_query.where(TreatmentPhoto.booking_id == booking_id)
        if photo_type:
            query = query.where(TreatmentPhoto.photo_type == photo_type)
            count_query = count_query.where(TreatmentPhoto.photo_type == photo_type)
        if portfolio_only:
            query = query.where(
                TreatmentPhoto.is_portfolio_approved.is_(True),
                TreatmentPhoto.is_consent_given.is_(True),
            )
            count_query = count_query.where(
                TreatmentPhoto.is_portfolio_approved.is_(True),
                TreatmentPhoto.is_consent_given.is_(True),
            )

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        result = await self.db.execute(
            query.order_by(TreatmentPhoto.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        photos = list(result.scalars().all())
        return photos, total

    async def get_photo(
        self, photo_id: uuid.UUID, clinic_id: uuid.UUID
    ) -> TreatmentPhoto:
        result = await self.db.execute(
            select(TreatmentPhoto).where(
                TreatmentPhoto.id == photo_id,
                TreatmentPhoto.clinic_id == clinic_id,
            )
        )
        photo = result.scalar_one_or_none()
        if photo is None:
            raise NotFoundError("Treatment photo not found")
        return photo

    async def update_photo(
        self,
        photo_id: uuid.UUID,
        clinic_id: uuid.UUID,
        **kwargs,
    ) -> TreatmentPhoto:
        photo = await self.get_photo(photo_id, clinic_id)
        for key, value in kwargs.items():
            if value is not None and hasattr(photo, key):
                setattr(photo, key, value)
        await self.db.flush()
        return photo

    async def approve_for_portfolio(
        self,
        photo_id: uuid.UUID,
        clinic_id: uuid.UUID,
        approved_by: uuid.UUID,
    ) -> TreatmentPhoto:
        photo = await self.get_photo(photo_id, clinic_id)
        photo.is_portfolio_approved = True
        photo.approved_by = approved_by
        await self.db.flush()
        return photo

    async def delete_photo(
        self, photo_id: uuid.UUID, clinic_id: uuid.UUID
    ) -> None:
        photo = await self.get_photo(photo_id, clinic_id)
        await self.db.delete(photo)
        await self.db.flush()

    async def get_pairs(
        self,
        clinic_id: uuid.UUID,
        customer_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """Get before/after photo pairs."""
        query = (
            select(TreatmentPhoto)
            .where(
                TreatmentPhoto.clinic_id == clinic_id,
                TreatmentPhoto.pair_id.isnot(None),
            )
            .order_by(TreatmentPhoto.created_at.desc())
        )
        if customer_id:
            query = query.where(TreatmentPhoto.customer_id == customer_id)

        result = await self.db.execute(query)
        photos = result.scalars().all()

        # Group by pair_id
        pairs: dict[uuid.UUID, dict] = {}
        for photo in photos:
            if photo.pair_id not in pairs:
                pairs[photo.pair_id] = {"pair_id": photo.pair_id, "before": None, "after": None}
            if photo.photo_type == "before":
                pairs[photo.pair_id]["before"] = photo
            elif photo.photo_type == "after":
                pairs[photo.pair_id]["after"] = photo

        return list(pairs.values())[offset : offset + limit]
