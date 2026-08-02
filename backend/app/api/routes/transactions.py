from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)
from app.services.category import CategoryService
from app.services.transaction import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionRead])
async def get_transactions(
    session: SessionDep,
    current_user: CurrentUser,
):
    return await TransactionService.get_list(session, current_user.id)


@router.get("/{transaction_id}", response_model=TransactionRead)
async def get_transaction(
    transaction_id: int,
    session: SessionDep,
    current_user: CurrentUser,
):
    transaction = await TransactionService.get_by_id(session, transaction_id)
    if not transaction or transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return transaction


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    category = await CategoryService.get_by_id(session, data.category_id)
    if not category or category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category",
        )

    if current_user.role == "test":
        count = await TransactionService.count_by_user(session, current_user.id)
        if count >= settings.TEST_USER_MAX_TRANSACTIONS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Test user transaction limit reached",
            )

    return await TransactionService.create(
        session,
        name=data.name,
        amount=data.amount,
        type=data.type,
        created_at=data.created_at,
        user_id=current_user.id,
        category_id=data.category_id,
    )


@router.patch("/{transaction_id}", response_model=TransactionRead)
async def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    session: SessionDep,
    current_user: CurrentUser,
):
    transaction = await TransactionService.get_by_id(session, transaction_id)
    if not transaction or transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    if data.category_id is not None:
        category = await CategoryService.get_by_id(session, data.category_id)
        if not category or category.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category",
            )

    return await TransactionService.update(
        session,
        transaction,
        name=data.name,
        amount=data.amount,
        type=data.type,
        category_id=data.category_id,
        created_at=data.created_at,
    )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    session: SessionDep,
    current_user: CurrentUser,
):
    transaction = await TransactionService.get_by_id(session, transaction_id)
    if not transaction or transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    await TransactionService.delete(session, transaction)
