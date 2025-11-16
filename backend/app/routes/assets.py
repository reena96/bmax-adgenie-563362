"""
Asset routes for file uploads and presigned URL generation.

This module provides endpoints for uploading files to S3 and generating
presigned URLs for asset access.
"""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.asset import Asset
from app.schemas.asset import (
    AssetUploadResponse,
    MultipleUploadResponse,
    PresignedUrlRequest,
    PresignedUrlResponse,
    AssetResponse
)
from app.services.s3_service import get_s3_service
from app.services.file_validation import FileValidator
from app.exceptions import (
    S3UploadError,
    S3ConnectionError,
    FileValidationError,
    InvalidFileError
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/upload",
    response_model=MultipleUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload Files",
    description="Upload one or more files to S3 with validation"
)
async def upload_files(
    files: List[UploadFile] = File(..., description="Files to upload (max 10)"),
    asset_type: str = Form(..., description="Type of asset: 'brand_image' or 'generated_video'"),
    project_id: str = Form(None, description="Optional project ID for organizing files"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MultipleUploadResponse:
    """
    Upload files to S3 with comprehensive validation.

    Args:
        files: List of files to upload (1-10 files)
        asset_type: Type of asset ('brand_image', 'generated_video', etc.)
        project_id: Optional project ID for file organization
        db: Database session
        current_user: Authenticated user

    Returns:
        MultipleUploadResponse with upload details for each file

    Raises:
        HTTPException 400: Validation errors (invalid type, size, format)
        HTTPException 413: File too large
        HTTPException 503: S3 service unavailable
        HTTPException 500: Server errors
    """
    # Validate number of files
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided for upload"
        )

    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many files. Maximum 10 files allowed, received {len(files)}"
        )

    # Validate asset_type
    valid_asset_types = ['brand_image', 'generated_video', 'b_roll_image', 'scene_video', 'lora_training']
    if asset_type not in valid_asset_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid asset_type '{asset_type}'. Allowed types: {', '.join(valid_asset_types)}"
        )

    # Get S3 service
    try:
        s3_service = get_s3_service()
    except S3ConnectionError as e:
        logger.error(f"S3 connection error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File upload service temporarily unavailable. Please try again later.",
            headers={"Retry-After": "60"}
        )

    uploaded_files = []
    total_size = 0

    for file in files:
        try:
            # Validate file based on asset type
            await FileValidator.validate_file_by_type(file, asset_type)

            # Upload to S3
            upload_result = await s3_service.upload_file(
                file=file,
                asset_type=asset_type,
                user_id=str(current_user.id),
                project_id=project_id
            )

            # Generate presigned URL for immediate access
            presigned_result = await s3_service.get_presigned_url(
                s3_key=upload_result['s3_key'],
                expiration_hours=24
            )

            # Save asset metadata to database
            asset = Asset(
                user_id=current_user.id,
                s3_key=upload_result['s3_key'],
                original_filename=file.filename,
                file_size=upload_result['file_size'],
                mime_type=upload_result['content_type'],
                asset_type=asset_type,
                asset_metadata={
                    'content_hash': upload_result['content_hash'],
                    'project_id': project_id
                }
            )
            db.add(asset)
            db.commit()
            db.refresh(asset)

            # Add to response
            uploaded_files.append(
                AssetUploadResponse(
                    asset_id=asset.id,
                    filename=file.filename,
                    s3_url=upload_result['s3_url'],
                    presigned_url=presigned_result['presigned_url'],
                    size_bytes=upload_result['file_size'],
                    mime_type=upload_result['content_type'],
                    asset_type=asset_type,
                    created_at=asset.created_at
                )
            )
            total_size += upload_result['file_size']

            logger.info(
                f"File uploaded successfully: {file.filename} "
                f"(user: {current_user.id}, asset: {asset.id})"
            )

        except FileValidationError as e:
            # Rollback transaction if validation fails
            db.rollback()
            logger.warning(f"File validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        except InvalidFileError as e:
            db.rollback()
            logger.warning(f"Invalid file error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        except S3UploadError as e:
            db.rollback()
            logger.error(f"S3 upload error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file. Please try again."
            )

        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error during upload: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during file upload"
            )

    return MultipleUploadResponse(
        uploads=uploaded_files,
        total_uploaded=len(uploaded_files),
        total_size_bytes=total_size
    )


@router.get(
    "/{asset_id}/presigned",
    response_model=PresignedUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Presigned URL",
    description="Generate presigned URL for asset access with time-limited expiration"
)
async def get_presigned_url(
    asset_id: UUID,
    expiration_hours: int = 24,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PresignedUrlResponse:
    """
    Generate presigned URL for accessing an asset.

    Args:
        asset_id: UUID of the asset
        expiration_hours: URL expiration time in hours (1-168 hours / 7 days)
        db: Database session
        current_user: Authenticated user

    Returns:
        PresignedUrlResponse with presigned URL and expiration time

    Raises:
        HTTPException 404: Asset not found
        HTTPException 403: User doesn't own the asset
        HTTPException 400: Invalid expiration hours
        HTTPException 500: Failed to generate presigned URL
    """
    # Validate expiration hours
    if expiration_hours < 1 or expiration_hours > 168:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expiration hours must be between 1 and 168 (7 days)"
        )

    # Fetch asset from database
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with ID {asset_id} not found"
        )

    # Verify ownership - users can only access their own assets
    if asset.user_id != current_user.id:
        logger.warning(
            f"Unauthorized access attempt: user {current_user.id} "
            f"tried to access asset {asset_id} owned by {asset.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this asset"
        )

    try:
        # Generate presigned URL
        s3_service = get_s3_service()
        presigned_result = await s3_service.get_presigned_url(
            s3_key=asset.s3_key,
            expiration_hours=expiration_hours
        )

        logger.info(
            f"Presigned URL generated for asset {asset_id} "
            f"(user: {current_user.id}, expires: {presigned_result['expiration_at']})"
        )

        return PresignedUrlResponse(
            asset_id=asset.id,
            presigned_url=presigned_result['presigned_url'],
            expiration_at=presigned_result['expiration_at'],
            original_filename=asset.original_filename,
            size_bytes=asset.file_size
        )

    except S3ConnectionError as e:
        logger.error(f"S3 connection error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Asset service temporarily unavailable. Please try again later.",
            headers={"Retry-After": "60"}
        )

    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate presigned URL"
        )


@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Asset Details",
    description="Get asset metadata by ID"
)
async def get_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AssetResponse:
    """
    Get asset metadata by ID.

    Args:
        asset_id: UUID of the asset
        db: Database session
        current_user: Authenticated user

    Returns:
        AssetResponse with asset details

    Raises:
        HTTPException 404: Asset not found
        HTTPException 403: User doesn't own the asset
    """
    # Fetch asset from database
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with ID {asset_id} not found"
        )

    # Verify ownership
    if asset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this asset"
        )

    return AssetResponse.model_validate(asset)


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Asset",
    description="Delete asset from S3 and database"
)
async def delete_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete asset from S3 and database.

    Args:
        asset_id: UUID of the asset
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException 404: Asset not found
        HTTPException 403: User doesn't own the asset
        HTTPException 500: Failed to delete from S3
    """
    # Fetch asset from database
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with ID {asset_id} not found"
        )

    # Verify ownership
    if asset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this asset"
        )

    try:
        # Delete from S3
        s3_service = get_s3_service()
        await s3_service.delete_file(asset.s3_key)

        # Delete from database
        db.delete(asset)
        db.commit()

        logger.info(f"Asset deleted: {asset_id} (user: {current_user.id})")

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting asset: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete asset"
        )
