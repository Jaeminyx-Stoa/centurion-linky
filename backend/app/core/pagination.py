from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.pagination import PaginatedResponse, PaginationParams


async def paginate(
    db: AsyncSession,
    stmt: Select,
    pagination: PaginationParams,
) -> PaginatedResponse:
    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Fetch page
    paged_stmt = stmt.offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(paged_stmt)
    items = result.scalars().all()

    return PaginatedResponse(
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )
