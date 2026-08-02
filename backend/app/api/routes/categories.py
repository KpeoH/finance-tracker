from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.category import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
async def get_categories(
    session: SessionDep,
    current_user: CurrentUser,
):
    return await CategoryService.get_list(session, current_user.id)


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: int,
    session: SessionDep,
    current_user: CurrentUser,
):
    category = await CategoryService.get_by_id(session, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return category


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    existing = await CategoryService.get_by_name(session, data.name, current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category with this name already exists",
        )

    if current_user.role == "test":
        count = await CategoryService.count_by_user(session, current_user.id)
        if count >= settings.TEST_USER_MAX_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Test user category limit reached",
            )

    return await CategoryService.create(
        session,
        name=data.name,
        user_id=current_user.id,
    )


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    session: SessionDep,
    current_user: CurrentUser,
):
    category = await CategoryService.get_by_id(session, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    if data.name is None:
        return category

    existing = await CategoryService.get_by_name(session, data.name, current_user.id)
    if existing and existing.id != category.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category with this name already exists",
        )

    return await CategoryService.update(session, category, data.name)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    session: SessionDep,
    current_user: CurrentUser,
):
    category = await CategoryService.get_by_id(session, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    await CategoryService.delete(session, category)
