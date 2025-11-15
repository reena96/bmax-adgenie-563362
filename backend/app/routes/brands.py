"""
Brand management routes for CRUD operations and image uploads.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import BrandCreate, BrandUpdate, BrandResponse, BrandListResponse, BrandGuidelines
from app.security import get_current_user
from app.services import brand_service

router = APIRouter()


@router.post("", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    title: str = Form(...),
    description: str = Form(None),
    brand_guidelines: str = Form(None),  # JSON string
    images: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new brand with product images.

    - **title**: Brand title (required, max 255 chars)
    - **description**: Brand description (optional, max 500 chars)
    - **brand_guidelines**: JSON string with brand guidelines (optional)
    - **images**: 2-10 product images (JPG, PNG, WEBP, max 10MB each)

    Returns created brand with all fields including S3 image URLs.
    """
    import json

    # Parse brand guidelines if provided
    guidelines = None
    if brand_guidelines:
        try:
            guidelines_dict = json.loads(brand_guidelines)
            guidelines = BrandGuidelines(**guidelines_dict)
        except (json.JSONDecodeError, ValueError) as e:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid brand_guidelines JSON: {str(e)}"
            )

    # Create brand data
    brand_data = BrandCreate(
        title=title,
        description=description,
        brand_guidelines=guidelines
    )

    return await brand_service.create_brand(db, current_user.id, brand_data, images)


@router.get("", response_model=BrandListResponse)
def list_brands(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of user's brands.

    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)

    Returns list of brands sorted by creation date (newest first).
    """
    # Enforce max limit
    if limit > 100:
        limit = 100

    return brand_service.get_user_brands(db, current_user.id, page, limit)


@router.get("/{brand_id}", response_model=BrandResponse)
def get_brand(
    brand_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get brand details by ID.

    - **brand_id**: Brand UUID

    Returns complete brand object with all images and guidelines.
    Validates ownership - returns 403 if user doesn't own the brand.
    """
    return brand_service.get_brand_by_id(db, brand_id, current_user.id)


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: UUID,
    title: str = Form(None),
    description: str = Form(None),
    brand_guidelines: str = Form(None),  # JSON string
    images: List[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update brand details and/or replace product images.

    - **brand_id**: Brand UUID
    - **title**: New brand title (optional)
    - **description**: New description (optional)
    - **brand_guidelines**: JSON string with brand guidelines (optional)
    - **images**: New product images - replaces all existing images (optional, 2-10 images if provided)

    Returns updated brand object.
    Validates ownership - returns 403 if user doesn't own the brand.
    """
    import json

    # Parse brand guidelines if provided
    guidelines = None
    if brand_guidelines:
        try:
            guidelines_dict = json.loads(brand_guidelines)
            guidelines = BrandGuidelines(**guidelines_dict)
        except (json.JSONDecodeError, ValueError) as e:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid brand_guidelines JSON: {str(e)}"
            )

    # Create update data
    brand_data = BrandUpdate(
        title=title,
        description=description,
        brand_guidelines=guidelines
    )

    return await brand_service.update_brand(db, brand_id, current_user.id, brand_data, images)


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brand(
    brand_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete brand and all associated product images from S3.

    - **brand_id**: Brand UUID

    Returns 204 No Content on success.
    Validates ownership - returns 403 if user doesn't own the brand.
    Returns 409 Conflict if brand has active ad projects.
    """
    brand_service.delete_brand(db, brand_id, current_user.id)
    return None
