"""
Unit tests for SQLAlchemy models.

Tests verify:
- Model instantiation
- Column types and nullability
- Default values
- Enum constraints
- JSONB data storage
- Relationships
"""

import uuid
from datetime import datetime
import pytest
from sqlalchemy.orm import Session

from app.models import (
    User,
    Brand,
    AdProject,
    ChatMessage,
    Script,
    GenerationJob,
    LoRAModel,
)


class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self, db: Session):
        """Test creating a user with all required fields."""
        user = User(
            email="test@example.com",
            name="Test User",
            subscription_type="free"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.subscription_type == "free"
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.deleted_at is None

    def test_user_subscription_types(self, db: Session):
        """Test all valid subscription types."""
        for sub_type in ["free", "pro", "enterprise"]:
            user = User(
                email=f"test_{sub_type}@example.com",
                name=f"Test {sub_type}",
                subscription_type=sub_type
            )
            db.add(user)
            db.commit()
            assert user.subscription_type == sub_type

    def test_user_email_unique(self, db: Session):
        """Test that email must be unique."""
        user1 = User(email="duplicate@example.com", name="User 1")
        db.add(user1)
        db.commit()

        user2 = User(email="duplicate@example.com", name="User 2")
        db.add(user2)
        with pytest.raises(Exception):  # IntegrityError
            db.commit()

    def test_user_soft_delete(self, db: Session):
        """Test soft delete functionality."""
        user = User(email="softdelete@example.com", name="Soft Delete User")
        db.add(user)
        db.commit()

        # Soft delete
        user.deleted_at = datetime.utcnow()
        db.commit()
        assert user.deleted_at is not None


class TestBrandModel:
    """Tests for the Brand model."""

    def test_create_brand(self, db: Session):
        """Test creating a brand with JSONB fields."""
        # Create user first
        user = User(email="brand_owner@example.com", name="Brand Owner")
        db.add(user)
        db.commit()

        # Create brand
        brand = Brand(
            user_id=user.id,
            title="Test Brand",
            description="A test brand",
            product_images=["s3://bucket/image1.png", "s3://bucket/image2.png"],
            brand_guidelines={
                "colors": ["#FFEB3B", "#FFFFFF"],
                "fonts": ["Arial"],
                "tone": "professional"
            }
        )
        db.add(brand)
        db.commit()
        db.refresh(brand)

        assert brand.id is not None
        assert brand.user_id == user.id
        assert brand.title == "Test Brand"
        assert len(brand.product_images) == 2
        assert brand.brand_guidelines["tone"] == "professional"

    def test_brand_jsonb_empty_defaults(self, db: Session):
        """Test that JSONB fields have proper defaults."""
        user = User(email="jsonb_test@example.com", name="JSONB Test")
        db.add(user)
        db.commit()

        brand = Brand(
            user_id=user.id,
            title="Minimal Brand"
        )
        db.add(brand)
        db.commit()
        db.refresh(brand)

        assert brand.product_images == []
        assert brand.brand_guidelines == {}

    def test_brand_cascade_delete(self, db: Session):
        """Test that deleting user cascades to brands."""
        user = User(email="cascade@example.com", name="Cascade Test")
        db.add(user)
        db.commit()

        brand = Brand(user_id=user.id, title="Cascade Brand")
        db.add(brand)
        db.commit()

        brand_id = brand.id
        db.delete(user)
        db.commit()

        # Brand should be deleted
        assert db.query(Brand).filter(Brand.id == brand_id).first() is None


class TestAdProjectModel:
    """Tests for the AdProject model."""

    def test_create_ad_project(self, db: Session):
        """Test creating an ad project with all enums and JSONB."""
        user = User(email="project_owner@example.com", name="Project Owner")
        db.add(user)
        db.commit()

        brand = Brand(user_id=user.id, title="Project Brand")
        db.add(brand)
        db.commit()

        project = AdProject(
            user_id=user.id,
            brand_id=brand.id,
            status="initial",
            conversation_history=[
                {"id": str(uuid.uuid4()), "role": "assistant", "content": "Hello!", "timestamp": "2025-11-15T10:00:00Z"}
            ],
            ad_details={
                "targetAudience": "Young professionals",
                "adPlatform": "instagram",
                "adDuration": 30
            }
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        assert project.id is not None
        assert project.status == "initial"
        assert len(project.conversation_history) == 1
        assert project.ad_details["adPlatform"] == "instagram"

    def test_ad_project_status_values(self, db: Session):
        """Test all valid status enum values."""
        user = User(email="status_test@example.com", name="Status Test")
        brand = Brand(user_id=user.id, title="Status Brand")
        db.add_all([user, brand])
        db.commit()

        statuses = [
            "initial",
            "chat_in_progress",
            "script_generated",
            "script_approved",
            "video_generating",
            "completed",
            "failed"
        ]

        for status in statuses:
            project = AdProject(
                user_id=user.id,
                brand_id=brand.id,
                status=status
            )
            db.add(project)
            db.commit()
            assert project.status == status


class TestChatMessageModel:
    """Tests for the ChatMessage model."""

    def test_create_chat_message(self, db: Session):
        """Test creating chat messages."""
        user = User(email="chat@example.com", name="Chat User")
        brand = Brand(user_id=user.id, title="Chat Brand")
        project = AdProject(user_id=user.id, brand_id=brand.id)
        db.add_all([user, brand, project])
        db.commit()

        message = ChatMessage(
            project_id=project.id,
            role="user",
            content="What is the best ad strategy?"
        )
        db.add(message)
        db.commit()
        db.refresh(message)

        assert message.id is not None
        assert message.role == "user"
        assert message.content == "What is the best ad strategy?"
        assert message.timestamp is not None

    def test_chat_message_roles(self, db: Session):
        """Test both user and assistant roles."""
        user = User(email="roles@example.com", name="Roles User")
        brand = Brand(user_id=user.id, title="Roles Brand")
        project = AdProject(user_id=user.id, brand_id=brand.id)
        db.add_all([user, brand, project])
        db.commit()

        for role in ["user", "assistant"]:
            message = ChatMessage(
                project_id=project.id,
                role=role,
                content=f"Message from {role}"
            )
            db.add(message)
            db.commit()
            assert message.role == role

    def test_chat_message_cascade_delete(self, db: Session):
        """Test CASCADE delete when project is deleted."""
        user = User(email="msg_cascade@example.com", name="Msg Cascade")
        brand = Brand(user_id=user.id, title="Msg Brand")
        project = AdProject(user_id=user.id, brand_id=brand.id)
        db.add_all([user, brand, project])
        db.commit()

        message = ChatMessage(project_id=project.id, role="user", content="Test")
        db.add(message)
        db.commit()

        message_id = message.id
        db.delete(project)
        db.commit()

        # Message should be deleted
        assert db.query(ChatMessage).filter(ChatMessage.id == message_id).first() is None


class TestScriptModel:
    """Tests for the Script model."""

    def test_create_script(self, db: Session):
        """Test creating a script with scenes."""
        user = User(email="script@example.com", name="Script User")
        brand = Brand(user_id=user.id, title="Script Brand")
        project = AdProject(user_id=user.id, brand_id=brand.id)
        db.add_all([user, brand, project])
        db.commit()

        script = Script(
            project_id=project.id,
            storyline="A compelling ad story",
            scenes=[
                {
                    "sceneNumber": 1,
                    "description": "Opening scene",
                    "duration": 5,
                    "visualPrompt": "Product showcase",
                    "audioPrompt": "Upbeat music"
                }
            ],
            voiceover_text="This is the voiceover"
        )
        db.add(script)
        db.commit()
        db.refresh(script)

        assert script.id is not None
        assert script.storyline == "A compelling ad story"
        assert len(script.scenes) == 1
        assert script.scenes[0]["sceneNumber"] == 1
        assert script.voiceover_text == "This is the voiceover"
        assert script.approved_at is None

    def test_script_unique_per_project(self, db: Session):
        """Test that only one script per project is allowed."""
        user = User(email="unique_script@example.com", name="Unique Script")
        brand = Brand(user_id=user.id, title="Unique Brand")
        project = AdProject(user_id=user.id, brand_id=brand.id)
        db.add_all([user, brand, project])
        db.commit()

        script1 = Script(project_id=project.id, storyline="First script")
        db.add(script1)
        db.commit()

        script2 = Script(project_id=project.id, storyline="Second script")
        db.add(script2)
        with pytest.raises(Exception):  # IntegrityError
            db.commit()


class TestGenerationJobModel:
    """Tests for the GenerationJob model."""

    def test_create_generation_job(self, db: Session):
        """Test creating a generation job."""
        user = User(email="job@example.com", name="Job User")
        brand = Brand(user_id=user.id, title="Job Brand")
        project = AdProject(user_id=user.id, brand_id=brand.id)
        script = Script(project_id=project.id, storyline="Job storyline")
        db.add_all([user, brand, project, script])
        db.commit()

        job = GenerationJob(
            project_id=project.id,
            script_id=script.id,
            status="queued",
            job_type="visual_generation",
            progress_percentage=0
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        assert job.id is not None
        assert job.status == "queued"
        assert job.job_type == "visual_generation"
        assert job.progress_percentage == 0

    def test_generation_job_status_values(self, db: Session):
        """Test all valid status values."""
        user = User(email="job_status@example.com", name="Job Status")
        brand = Brand(user_id=user.id, title="Job Brand")
        project = AdProject(user_id=user.id, brand_id=brand.id)
        script = Script(project_id=project.id, storyline="Job storyline")
        db.add_all([user, brand, project, script])
        db.commit()

        for status in ["queued", "processing", "completed", "failed"]:
            job = GenerationJob(
                project_id=project.id,
                script_id=script.id,
                status=status,
                job_type="visual_generation"
            )
            db.add(job)
            db.commit()
            assert job.status == status

    def test_generation_job_types(self, db: Session):
        """Test all valid job types."""
        user = User(email="job_types@example.com", name="Job Types")
        brand = Brand(user_id=user.id, title="Job Brand")
        project = AdProject(user_id=user.id, brand_id=brand.id)
        script = Script(project_id=project.id, storyline="Job storyline")
        db.add_all([user, brand, project, script])
        db.commit()

        job_types = ["visual_generation", "audio_generation", "video_composition", "final_export"]
        for job_type in job_types:
            job = GenerationJob(
                project_id=project.id,
                script_id=script.id,
                job_type=job_type
            )
            db.add(job)
            db.commit()
            assert job.job_type == job_type


class TestLoRAModelModel:
    """Tests for the LoRAModel model."""

    def test_create_lora_model(self, db: Session):
        """Test creating a LoRA model."""
        user = User(email="lora@example.com", name="LoRA User")
        brand = Brand(user_id=user.id, title="LoRA Brand")
        db.add_all([user, brand])
        db.commit()

        lora = LoRAModel(
            brand_id=brand.id,
            model_name="brand_style_model",
            training_status="not_started",
            training_progress=0,
            trained_samples_count=0
        )
        db.add(lora)
        db.commit()
        db.refresh(lora)

        assert lora.id is not None
        assert lora.brand_id == brand.id
        assert lora.model_name == "brand_style_model"
        assert lora.training_status == "not_started"
        assert lora.training_progress == 0

    def test_lora_model_training_statuses(self, db: Session):
        """Test all valid training status values."""
        user = User(email="lora_status@example.com", name="LoRA Status")
        db.add(user)
        db.commit()

        statuses = ["not_started", "in_progress", "completed", "failed"]
        for idx, status in enumerate(statuses):
            brand = Brand(user_id=user.id, title=f"LoRA Brand {idx}")
            lora = LoRAModel(
                brand_id=brand.id,
                model_name=f"model_{idx}",
                training_status=status
            )
            db.add_all([brand, lora])
            db.commit()
            assert lora.training_status == status

    def test_lora_model_unique_per_brand(self, db: Session):
        """Test that only one LoRA model per brand is allowed."""
        user = User(email="unique_lora@example.com", name="Unique LoRA")
        brand = Brand(user_id=user.id, title="Unique LoRA Brand")
        db.add_all([user, brand])
        db.commit()

        lora1 = LoRAModel(brand_id=brand.id, model_name="Model 1")
        db.add(lora1)
        db.commit()

        lora2 = LoRAModel(brand_id=brand.id, model_name="Model 2")
        db.add(lora2)
        with pytest.raises(Exception):  # IntegrityError
            db.commit()
