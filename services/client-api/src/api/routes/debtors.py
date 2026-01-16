"""Debtor CRUD endpoints."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.debtor import DebtorCreate, DebtorResponse, DebtorUpdate
from schemas.enums import DelinquencyStage

from ...core.database import get_db
from ...models import Call, Client, Debtor
from ..schemas import DebtorListItem, PaginatedResponse

router = APIRouter()

# For demo, use a default client ID (in production, this would come from auth)
DEFAULT_CLIENT_ID = None


async def get_or_create_demo_client(db: AsyncSession) -> UUID:
    """Get or create a demo client for testing."""
    global DEFAULT_CLIENT_ID

    if DEFAULT_CLIENT_ID:
        return DEFAULT_CLIENT_ID

    # Check for existing demo client
    result = await db.execute(
        select(Client).where(Client.name == "Demo Company").limit(1)
    )
    client = result.scalar_one_or_none()

    if not client:
        # Create demo client
        import secrets

        client = Client(
            name="Demo Company",
            api_key=f"demo_{secrets.token_hex(16)}",
            webhook_url="https://demo.example.com/webhook",
        )
        db.add(client)
        await db.commit()
        await db.refresh(client)

    DEFAULT_CLIENT_ID = client.id
    return client.id


@router.get("", response_model=PaginatedResponse[DebtorListItem])
async def list_debtors(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    stage: DelinquencyStage | None = None,
    search: str | None = None,
    sort_by: Literal["created_at", "amount_owed", "due_date", "name"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[DebtorListItem]:
    """List debtors with pagination and filtering."""

    client_id = await get_or_create_demo_client(db)

    # Build query
    query = select(Debtor).where(Debtor.client_id == client_id)

    # Apply filters
    if stage:
        query = query.where(Debtor.stage == stage.value)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Debtor.first_name.ilike(search_pattern))
            | (Debtor.last_name.ilike(search_pattern))
            | (Debtor.phone.ilike(search_pattern))
            | (Debtor.email.ilike(search_pattern))
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply sorting
    if sort_by == "name":
        order_col = Debtor.first_name
    elif sort_by == "amount_owed":
        order_col = Debtor.amount_owed
    elif sort_by == "due_date":
        order_col = Debtor.due_date
    else:
        order_col = Debtor.created_at

    if sort_order == "desc":
        query = query.order_by(order_col.desc())
    else:
        query = query.order_by(order_col.asc())

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute
    result = await db.execute(query)
    debtors = result.scalars().all()

    # Get last call info for each debtor
    items = []
    for debtor in debtors:
        # Get last call
        last_call_result = await db.execute(
            select(Call)
            .where(Call.debtor_id == debtor.id)
            .order_by(Call.initiated_at.desc())
            .limit(1)
        )
        last_call = last_call_result.scalar_one_or_none()

        items.append(
            DebtorListItem(
                id=debtor.id,
                full_name=debtor.full_name,
                phone=debtor.phone,
                amount_owed=debtor.amount_owed,
                due_date=debtor.due_date,
                stage=debtor.stage,
                last_call_at=last_call.initiated_at if last_call else None,
                last_call_outcome=last_call.outcome if last_call else None,
                created_at=debtor.created_at,
            )
        )

    return PaginatedResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=skip + limit < total,
    )


@router.post("", response_model=DebtorResponse, status_code=201)
async def create_debtor(
    debtor_in: DebtorCreate,
    db: AsyncSession = Depends(get_db),
) -> DebtorResponse:
    """Create a new debtor."""

    client_id = await get_or_create_demo_client(db)

    # Check for duplicate phone
    existing = await db.execute(
        select(Debtor)
        .where(Debtor.client_id == client_id)
        .where(Debtor.phone == debtor_in.phone)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Debtor with phone {debtor_in.phone} already exists",
        )

    debtor = Debtor(
        client_id=client_id,
        **debtor_in.model_dump(),
    )
    db.add(debtor)
    await db.commit()
    await db.refresh(debtor)

    return DebtorResponse.model_validate(debtor)


@router.get("/{debtor_id}", response_model=DebtorResponse)
async def get_debtor(
    debtor_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> DebtorResponse:
    """Get a debtor by ID."""

    result = await db.execute(select(Debtor).where(Debtor.id == debtor_id))
    debtor = result.scalar_one_or_none()

    if not debtor:
        raise HTTPException(status_code=404, detail="Debtor not found")

    return DebtorResponse.model_validate(debtor)


@router.put("/{debtor_id}", response_model=DebtorResponse)
async def update_debtor(
    debtor_id: UUID,
    debtor_in: DebtorUpdate,
    db: AsyncSession = Depends(get_db),
) -> DebtorResponse:
    """Update a debtor."""

    result = await db.execute(select(Debtor).where(Debtor.id == debtor_id))
    debtor = result.scalar_one_or_none()

    if not debtor:
        raise HTTPException(status_code=404, detail="Debtor not found")

    # Update fields
    update_data = debtor_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(debtor, field, value)

    await db.commit()
    await db.refresh(debtor)

    return DebtorResponse.model_validate(debtor)


@router.delete("/{debtor_id}", status_code=204)
async def delete_debtor(
    debtor_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a debtor."""

    result = await db.execute(select(Debtor).where(Debtor.id == debtor_id))
    debtor = result.scalar_one_or_none()

    if not debtor:
        raise HTTPException(status_code=404, detail="Debtor not found")

    await db.delete(debtor)
    await db.commit()
