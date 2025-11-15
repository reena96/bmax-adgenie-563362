"""
Integration tests for database integrity.

Tests verify:
- Foreign key constraints
- CASCADE delete behavior
- Unique constraints
- JSONB operations
- Complex queries across relationships
- Check constraints
"""

import uuid
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import (
    User,
    Brand,
    AdProject,
    ChatMessage,
    Script,
    GenerationJob,
    LoRAModel,
)


class TestForeignKeyConstraints:
    """Test foreign key constraint enforcement."""

    def test_brand_requires_valid_user(self, db: Session):
        """Test that brand creation fails with invalid user_id."""
        invalid_uuid = uuid.uuid4()
        brand = Brand(
            user_id=invalid_uuid,
            title="Invalid Brand"
        )
        db.add(brand)
        with pytest.raises(IntegrityError):
            db.commit()

    def test_ad_project_requires_valid_brand_and_user(self, db: Session):
        """Test that ad_project requires valid brand_id and user_id."""
        invalid_uuid = uuid.uuid4()
        project = AdProject(
            user_id=invalid_uuid,
            brand_id=invalid_uuid
        )
        db.add(project)
        with pytest.raises(IntegrityError):
            db.commit()

    def test_chat_message_requires_valid_project(self, db: Session):
        """Test that chat message requires valid project_id."""
        invalid_uuid = uuid.uuid4()
        message = ChatMessage(
            project_id=invalid_uuid,
            role="user",
            content="Test message"
        )
        db.add(message)
        with pytest.raises(IntegrityError):
            db.commit()

    def test_script_requires_valid_project(self, db: Session):
        """Test that script requires valid project_id."""
        invalid_uuid = uuid.uuid4()
        script = Script(
            project_id=invalid_uuid,
            storyline="Test storyline"
        )
        db.add(script)
        with pytest.raises(IntegrityError):
            db.commit()

    def test_generation_job_requires_valid_project_and_script(self, db: Session):
        """Test that generation job requires valid project_id and script_id."""
        invalid_uuid = uuid.uuid4()
        job = GenerationJob(
            project_id=invalid_uuid,
            script_id=invalid_uuid,
            job_type="visual_generation"
        )
        db.add(job)
        with pytest.raises(IntegrityError):
            db.commit()

    def test_lora_model_requires_valid_brand(self, db: Session):
        """Test that LoRA model requires valid brand_id."""
        invalid_uuid = uuid.uuid4()
        lora = LoRAModel(
            brand_id=invalid_uuid,
            model_name="Test Model"
        )
        db.add(lora)
        with pytest.raises(IntegrityError):
            db.commit()


class TestCascadeDeleteBehavior:
    """Test CASCADE delete behavior across relationships."""

    def test_delete_user_cascades_to_brands(self, db: Session):
        """Test that deleting user deletes all associated brands."""
        user = User(email="cascade_user@example.com", name="Cascade User")
        db.add(user)
        db.commit()

        brand1 = Brand(user_id=user.id, title="Brand 1")
        brand2 = Brand(user_id=user.id, title="Brand 2")
        db.add_all([brand1, brand2])
        db.commit()

        brand_ids = [brand1.id, brand2.id]

        # Delete user
        db.delete(user)
        db.commit()

        # Brands should be deleted
        for brand_id in brand_ids:
            assert db.query(Brand).filter(Brand.id == brand_id).first() is None

    def test_delete_brand_cascades_to_projects(self, db: Session):
        """Test that deleting brand deletes all associated projects."""
        user = User(email="brand_cascade@example.com", name="Brand Cascade")
        brand = Brand(user_id=user.id, title="Cascade Brand")
        db.add_all([user, brand])
        db.commit()

        project1 = AdProject(user_id=user.id, brand_id=brand.id)
        project2 = AdProject(user_id=user.id, brand_id=brand.id)
        db.add_all([project1, project2])
        db.commit()

        project_ids = [project1.id, project2.id]

        # Delete brand
        db.delete(brand)
        db.commit()

        # Projects should be deleted
        for project_id in project_ids:
            assert db.query(AdProject).filter(AdProject.id == project_id).first() is None

    def test_delete_project_cascades_to_messages_and_script(self, db: Session):
        """Test that deleting project deletes chat messages and script."""
        user = User(email="project_cascade@example.com", name="Project Cascade")
        brand = Brand(user_id=user.id, title="Project Brand")
        project = AdProject(user_id=user.id, brand_id=brand.id)
        db.add_all([user, brand, project])
        db.commit()

        # Add chat messages
        message1 = ChatMessage(project_id=project.id, role="user", content="Message 1")
        message2 = ChatMessage(project_id=project.id, role="assistant", content="Message 2")
        db.add_all([message1, message2])
        db.commit()

        # Add script
        script = Script(project_id=project.id, storyline="Test storyline")
        db.add(script)
        db.commit()

        message_ids = [message1.id, message2.id]
        script_id = script.id

        # Delete project
        db.delete(project)
        db.commit()

        # Messages and script should be deleted
        for message_id in message_ids:
            assert db.query(ChatMessage).filter(ChatMessage.id == message_id).first() is None
        assert db.query(Script).filter(Script.id == script_id).first() is None

    def test_delete_script_cascades_to_generation_jobs(self, db: Session):
        """Test that deleting script deletes all generation jobs."""
        user = User(email="script_cascade@example.com", name="Script Cascade")
        brand = Brand(user_id=user.id, title="Script Brand")
        project = AdProject(user_id=user.id, brand_id=brand.id)
        script = Script(project_id=project.id, storyline="Test")
        db.add_all([user, brand, project, script])
        db.commit()

        job1 = GenerationJob(project_id=project.id, script_id=script.id, job_type="visual_generation")
        job2 = GenerationJob(project_id=project.id, script_id=script.id, job_type="audio_generation")
        db.add_all([job1, job2])
        db.commit()

        job_ids = [job1.id, job2.id]

        # Delete script
        db.delete(script)
        db.commit()

        # Jobs should be deleted
        for job_id in job_ids:
            assert db.query(GenerationJob).filter(GenerationJob.id == job_id).first() is None

    def test_delete_brand_cascades_to_lora_model(self, db: Session):
        """Test that deleting brand deletes associated LoRA model."""
        user = User(email="lora_cascade@example.com", name="LoRA Cascade")
        brand = Brand(user_id=user.id, title="LoRA Brand")
        lora = LoRAModel(brand_id=brand.id, model_name="Test Model")
        db.add_all([user, brand, lora])
        db.commit()

        lora_id = lora.id

        # Delete brand
        db.delete(brand)
        db.commit()

        # LoRA model should be deleted
        assert db.query(LoRAModel).filter(LoRAModel.id == lora_id).first() is None


class TestUniqueConstraints:
    """Test unique constraint enforcement."""

    def test_user_email_unique(self, db: Session):
        """Test that user email must be unique."""
        user1 = User(email="unique@example.com", name="User 1")
        db.add(user1)
        db.commit()

        user2 = User(email="unique@example.com", name="User 2")
        db.add(user2)
        with pytest.raises(IntegrityError):
            db.commit()

    def test_script_project_id_unique(self, db: Session):
        """Test that only one script per project is allowed."""
        user = User(email="script_unique@example.com", name="Script Unique")
        brand = Brand(user_id=user.id, title="Script Brand")
        project = AdProject(user_id=user.id, brand_id=brand.id)
        db.add_all([user, brand, project])
        db.commit()

        script1 = Script(project_id=project.id, storyline="Script 1")
        db.add(script1)
        db.commit()

        script2 = Script(project_id=project.id, storyline="Script 2")
        db.add(script2)
        with pytest.raises(IntegrityError):
            db.commit()

    def test_lora_model_brand_id_unique(self, db: Session):
        """Test that only one LoRA model per brand is allowed."""
        user = User(email="lora_unique@example.com", name="LoRA Unique")
        brand = Brand(user_id=user.id, title="LoRA Brand")
        db.add_all([user, brand])
        db.commit()

        lora1 = LoRAModel(brand_id=brand.id, model_name="Model 1")
        db.add(lora1)
        db.commit()

        lora2 = LoRAModel(brand_id=brand.id, model_name="Model 2")
        db.add(lora2)
        with pytest.raises(IntegrityError):
            db.commit()


class TestJSONBOperations:
    """Test JSONB data storage and retrieval."""

    def test_brand_product_images_array(self, db: Session):
        """Test storing and retrieving product images array."""
        user = User(email="images@example.com", name="Images User")
        db.add(user)
        db.commit()

        images = [
            "s3://bucket/image1.png",
            "s3://bucket/image2.png",
            "s3://bucket/image3.png"
        ]
        brand = Brand(
            user_id=user.id,
            title="Image Brand",
            product_images=images
        )
        db.add(brand)
        db.commit()
        db.refresh(brand)

        assert len(brand.product_images) == 3
        assert brand.product_images[0] == "s3://bucket/image1.png"

    def test_brand_guidelines_object(self, db: Session):
        """Test storing and retrieving brand guidelines object."""
        user = User(email="guidelines@example.com", name="Guidelines User")
        db.add(user)
        db.commit()

        guidelines = {
            "colors": ["#FFEB3B", "#FFFFFF", "#0A0E27"],
            "fonts": ["Arial", "Helvetica"],
            "tone": "professional, friendly",
            "additionalAssets": ["s3://bucket/asset1.png"]
        }
        brand = Brand(
            user_id=user.id,
            title="Guidelines Brand",
            brand_guidelines=guidelines
        )
        db.add(brand)
        db.commit()
        db.refresh(brand)

        assert brand.brand_guidelines["tone"] == "professional, friendly"
        assert len(brand.brand_guidelines["colors"]) == 3

    def test_ad_project_conversation_history(self, db: Session):
        """Test storing and retrieving conversation history."""
        user = User(email="conversation@example.com", name="Conversation User")
        brand = Brand(user_id=user.id, title="Conversation Brand")
        db.add_all([user, brand])
        db.commit()

        conversation = [
            {
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "content": "Hello! How can I help?",
                "timestamp": "2025-11-15T10:00:00Z"
            },
            {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": "I need an ad",
                "timestamp": "2025-11-15T10:01:00Z"
            }
        ]
        project = AdProject(
            user_id=user.id,
            brand_id=brand.id,
            conversation_history=conversation
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        assert len(project.conversation_history) == 2
        assert project.conversation_history[0]["role"] == "assistant"
        assert project.conversation_history[1]["role"] == "user"

    def test_script_scenes_array(self, db: Session):
        """Test storing and retrieving scenes array."""
        user = User(email="scenes@example.com", name="Scenes User")
        brand = Brand(user_id=user.id, title="Scenes Brand")
        project = AdProject(user_id=user.id, brand_id=brand.id)
        db.add_all([user, brand, project])
        db.commit()

        scenes = [
            {
                "sceneNumber": 1,
                "description": "Opening scene",
                "duration": 5,
                "visualPrompt": "Product showcase",
                "audioPrompt": "Upbeat music",
                "generatedVideoUrl": "s3://bucket/scene1.mp4"
            },
            {
                "sceneNumber": 2,
                "description": "Closing scene",
                "duration": 3,
                "visualPrompt": "Call to action",
                "audioPrompt": "Voiceover"
            }
        ]
        script = Script(
            project_id=project.id,
            storyline="Test storyline",
            scenes=scenes
        )
        db.add(script)
        db.commit()
        db.refresh(script)

        assert len(script.scenes) == 2
        assert script.scenes[0]["sceneNumber"] == 1
        assert script.scenes[1]["duration"] == 3


class TestCheckConstraints:
    """Test check constraint enforcement."""

    def test_generation_job_progress_percentage_range(self, db: Session):
        """Test that progress_percentage must be between 0 and 100."""
        user = User(email="progress@example.com", name="Progress User")
        brand = Brand(user_id=user.id, title="Progress Brand")
        project = AdProject(user_id=user.id, brand_id=brand.id)
        script = Script(project_id=project.id, storyline="Test")
        db.add_all([user, brand, project, script])
        db.commit()

        # Valid: 0
        job0 = GenerationJob(
            project_id=project.id,
            script_id=script.id,
            job_type="visual_generation",
            progress_percentage=0
        )
        db.add(job0)
        db.commit()

        # Valid: 100
        job100 = GenerationJob(
            project_id=project.id,
            script_id=script.id,
            job_type="audio_generation",
            progress_percentage=100
        )
        db.add(job100)
        db.commit()

        # Invalid: 101
        job_invalid = GenerationJob(
            project_id=project.id,
            script_id=script.id,
            job_type="video_composition",
            progress_percentage=101
        )
        db.add(job_invalid)
        with pytest.raises(IntegrityError):
            db.commit()

    def test_lora_model_progress_range(self, db: Session):
        """Test that LoRA training_progress must be between 0 and 100."""
        user = User(email="lora_progress@example.com", name="LoRA Progress")
        brand = Brand(user_id=user.id, title="LoRA Progress Brand")
        db.add_all([user, brand])
        db.commit()

        # Valid
        lora = LoRAModel(
            brand_id=brand.id,
            model_name="Valid Model",
            training_progress=50
        )
        db.add(lora)
        db.commit()

        assert lora.training_progress == 50


class TestComplexQueries:
    """Test complex queries across relationships."""

    def test_query_user_with_brands_and_projects(self, db: Session):
        """Test querying user with all related brands and projects."""
        user = User(email="complex@example.com", name="Complex User")
        db.add(user)
        db.commit()

        brand1 = Brand(user_id=user.id, title="Brand 1")
        brand2 = Brand(user_id=user.id, title="Brand 2")
        db.add_all([brand1, brand2])
        db.commit()

        project1 = AdProject(user_id=user.id, brand_id=brand1.id, status="initial")
        project2 = AdProject(user_id=user.id, brand_id=brand2.id, status="completed")
        db.add_all([project1, project2])
        db.commit()

        # Query user and verify relationships
        queried_user = db.query(User).filter(User.id == user.id).first()
        assert len(queried_user.brands) == 2
        assert len(queried_user.ad_projects) == 2

    def test_query_project_with_all_relationships(self, db: Session):
        """Test querying project with messages, script, and jobs."""
        user = User(email="full_project@example.com", name="Full Project")
        brand = Brand(user_id=user.id, title="Full Brand")
        project = AdProject(user_id=user.id, brand_id=brand.id)
        db.add_all([user, brand, project])
        db.commit()

        # Add messages
        msg1 = ChatMessage(project_id=project.id, role="user", content="Message 1")
        msg2 = ChatMessage(project_id=project.id, role="assistant", content="Message 2")
        db.add_all([msg1, msg2])
        db.commit()

        # Add script
        script = Script(project_id=project.id, storyline="Full storyline")
        db.add(script)
        db.commit()

        # Add generation job
        job = GenerationJob(
            project_id=project.id,
            script_id=script.id,
            job_type="visual_generation"
        )
        db.add(job)
        db.commit()

        # Query project and verify all relationships
        queried_project = db.query(AdProject).filter(AdProject.id == project.id).first()
        assert len(queried_project.chat_messages) == 2
        assert queried_project.script is not None
        assert len(queried_project.generation_jobs) == 1

    def test_filter_projects_by_status(self, db: Session):
        """Test filtering projects by status enum."""
        user = User(email="filter@example.com", name="Filter User")
        brand = Brand(user_id=user.id, title="Filter Brand")
        db.add_all([user, brand])
        db.commit()

        # Create projects with different statuses
        p1 = AdProject(user_id=user.id, brand_id=brand.id, status="initial")
        p2 = AdProject(user_id=user.id, brand_id=brand.id, status="completed")
        p3 = AdProject(user_id=user.id, brand_id=brand.id, status="completed")
        db.add_all([p1, p2, p3])
        db.commit()

        # Query completed projects
        completed = db.query(AdProject).filter(AdProject.status == "completed").all()
        assert len(completed) == 2
