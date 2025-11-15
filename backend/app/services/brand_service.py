"""
Brand service for business logic and database operations.
"""
import uuid
from typing import List, Optional, Tuple

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Brand, AdProject
from app.schemas import (
    BrandCreate, BrandUpdate, BrandResponse,
    BrandListItem, BrandListResponse, PaginationMeta
)
from app.services.s3_service import upload_brand_images, delete_brand_images
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def validate_brand_ownership(brand: Brand, user_id: uuid.UUID) -> None:
    """
    Validate that the brand belongs to the user.

    Args:
        brand: Brand object
        user_id: User ID to validate

    Raises:
        HTTPException: 403 if user doesn't own the brand
    """
    if brand.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this brand"
        )


async def create_brand(
    db: Session,
    user_id: uuid.UUID,
    brand_data: BrandCreate,
    images: List[UploadFile]
) -> BrandResponse:
    """
    Create a new brand with product images.

    Args:
        db: Database session
        user_id: User ID creating the brand
        brand_data: Brand creation data
        images: List of product images to upload

    Returns:
        Created brand response

    Raises:
        HTTPException: If validation fails or creation fails
    """
    # Create brand record first to get brand_id
    brand = Brand(
        id=str(uuid.uuid4()),
        user_id=str(user_id),
        title=brand_data.title,
        description=brand_data.description,
        product_images=[],
        brand_guidelines=brand_data.brand_guidelines.model_dump() if brand_data.brand_guidelines else None
    )

    try:
        # Upload images to S3
        s3_urls = await upload_brand_images(user_id, brand.id, images)
        brand.product_images = s3_urls

        # Save to database
        db.add(brand)
        db.commit()
        db.refresh(brand)

        logger.info(f"Created brand {brand.id} for user {user_id}")

        return BrandResponse.model_validate(brand)

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create brand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create brand: {str(e)}"
        )


def get_user_brands(
    db: Session,
    user_id: uuid.UUID,
    page: int = 1,
    limit: int = 20
) -> BrandListResponse:
    """
    Get paginated list of user's brands.

    Args:
        db: Database session
        user_id: User ID
        page: Page number (1-indexed)
        limit: Items per page

    Returns:
        Paginated brand list response
    """
    # Calculate offset
    offset = (page - 1) * limit

    # Get total count
    total = db.query(func.count(Brand.id)).filter(Brand.user_id == user_id).scalar()

    # Get brands for current page
    brands = (
        db.query(Brand)
        .filter(Brand.user_id == user_id)
        .order_by(Brand.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Convert to list items
    brand_items = []
    for brand in brands:
        # Get thumbnail (first image)
        thumbnail_url = brand.product_images[0] if brand.product_images else None
        image_count = len(brand.product_images) if brand.product_images else 0

        brand_items.append(
            BrandListItem(
                id=brand.id,
                title=brand.title,
                thumbnail_url=thumbnail_url,
                image_count=image_count,
                created_at=brand.created_at
            )
        )

    # Calculate pagination metadata
    has_more = (offset + limit) < total

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        has_more=has_more
    )

    return BrandListResponse(brands=brand_items, pagination=pagination)


def get_brand_by_id(
    db: Session,
    brand_id: uuid.UUID,
    user_id: uuid.UUID
) -> BrandResponse:
    """
    Get brand by ID with ownership validation.

    Args:
        db: Database session
        brand_id: Brand ID
        user_id: User ID for ownership validation

    Returns:
        Brand response

    Raises:
        HTTPException: 404 if not found, 403 if not owner
    """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with id {brand_id} not found"
        )

    validate_brand_ownership(brand, user_id)

    return BrandResponse.model_validate(brand)


async def update_brand(
    db: Session,
    brand_id: uuid.UUID,
    user_id: uuid.UUID,
    brand_data: BrandUpdate,
    images: Optional[List[UploadFile]] = None
) -> BrandResponse:
    """
    Update brand with optional image replacement.

    Args:
        db: Database session
        brand_id: Brand ID
        user_id: User ID for ownership validation
        brand_data: Brand update data
        images: Optional new images (replaces all existing images)

    Returns:
        Updated brand response

    Raises:
        HTTPException: 404 if not found, 403 if not owner, 400 if validation fails
    """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with id {brand_id} not found"
        )

    validate_brand_ownership(brand, user_id)

    try:
        # Update text fields
        if brand_data.title is not None:
            brand.title = brand_data.title

        if brand_data.description is not None:
            brand.description = brand_data.description

        if brand_data.brand_guidelines is not None:
            brand.brand_guidelines = brand_data.brand_guidelines.model_dump()

        # Handle image replacement
        if images is not None:
            # Delete old images from S3
            old_images = brand.product_images if brand.product_images else []
            if old_images:
                delete_brand_images(old_images)

            # Upload new images
            s3_urls = await upload_brand_images(user_id, brand.id, images)
            brand.product_images = s3_urls

        db.commit()
        db.refresh(brand)

        logger.info(f"Updated brand {brand.id}")

        return BrandResponse.model_validate(brand)

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update brand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update brand: {str(e)}"
        )


def delete_brand(
    db: Session,
    brand_id: uuid.UUID,
    user_id: uuid.UUID
) -> None:
    """
    Delete brand and all associated S3 images.

    Args:
        db: Database session
        brand_id: Brand ID
        user_id: User ID for ownership validation

    Raises:
        HTTPException: 404 if not found, 403 if not owner, 409 if has active projects
    """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with id {brand_id} not found"
        )

    validate_brand_ownership(brand, user_id)

    # Check for active ad projects
    active_projects_count = (
        db.query(func.count(AdProject.id))
        .filter(AdProject.brand_id == brand_id)
        .scalar()
    )

    if active_projects_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete brand with {active_projects_count} active ad projects"
        )

    try:
        # Delete S3 images
        if brand.product_images:
            delete_brand_images(brand.product_images)

        # Delete brand from database
        db.delete(brand)
        db.commit()

        logger.info(f"Deleted brand {brand_id}")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete brand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete brand: {str(e)}"
        )
