"""
Tests for database models and connections.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models import (
    User, Brand, LoraModel, AdProject, ChatMessage,
    Script, GenerationJob, Session
)


@pytest.mark.unit
def test_database_connection(test_db):
    """Test that database connection works."""
    # Simple query to verify connection
    result = test_db.execute(text("SELECT 1")).scalar()
    assert result == 1


@pytest.mark.unit
def test_user_table_exists(test_db):
    """Test that users table exists and can be queried."""
    # Query should not raise error
    users = test_db.query(User).all()
    assert isinstance(users, list)


@pytest.mark.unit
def test_brand_table_exists(test_db):
    """Test that brands table exists and can be queried."""
    brands = test_db.query(Brand).all()
    assert isinstance(brands, list)


@pytest.mark.unit
def test_lora_model_table_exists(test_db):
    """Test that lora_models table exists and can be queried."""
    models = test_db.query(LoraModel).all()
    assert isinstance(models, list)


@pytest.mark.unit
def test_ad_project_table_exists(test_db):
    """Test that ad_projects table exists and can be queried."""
    projects = test_db.query(AdProject).all()
    assert isinstance(projects, list)


@pytest.mark.unit
def test_chat_message_table_exists(test_db):
    """Test that chat_messages table exists and can be queried."""
    messages = test_db.query(ChatMessage).all()
    assert isinstance(messages, list)


@pytest.mark.unit
def test_script_table_exists(test_db):
    """Test that scripts table exists and can be queried."""
    scripts = test_db.query(Script).all()
    assert isinstance(scripts, list)


@pytest.mark.unit
def test_generation_job_table_exists(test_db):
    """Test that generation_jobs table exists and can be queried."""
    jobs = test_db.query(GenerationJob).all()
    assert isinstance(jobs, list)


@pytest.mark.unit
def test_session_table_exists(test_db):
    """Test that sessions table exists and can be queried."""
    sessions = test_db.query(Session).all()
    assert isinstance(sessions, list)


@pytest.mark.unit
def test_create_user(test_db):
    """Test creating a user record."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        password_hash="hashed_password",
        subscription_tier="free",
        credits=0,
        free_videos_used=0
    )

    test_db.add(user)
    test_db.commit()

    # Verify user was created
    retrieved_user = test_db.query(User).filter_by(email="test@example.com").first()
    assert retrieved_user is not None
    assert retrieved_user.name == "Test User"
    assert retrieved_user.subscription_tier == "free"


@pytest.mark.unit
def test_user_uuid_generation(test_db):
    """Test that user ID is a valid UUID."""
    user = User(
        email="uuid_test@example.com",
        name="UUID Test",
        password_hash="hashed"
    )

    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    # Verify UUID was generated
    assert user.id is not None
    # UUID should be 36 characters (with hyphens)
    assert len(str(user.id)) == 36


@pytest.mark.unit
def test_brand_with_user_relationship(test_db):
    """Test creating brand with user foreign key."""
    # Create user first
    user = User(
        email="brand_user@example.com",
        name="Brand User",
        password_hash="hashed"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    # Create brand
    brand = Brand(
        user_id=user.id,
        title="Test Brand",
        description="A test brand",
        brand_guidelines={"color": "blue"}
    )
    test_db.add(brand)
    test_db.commit()

    # Verify relationship
    retrieved_brand = test_db.query(Brand).filter_by(title="Test Brand").first()
    assert retrieved_brand is not None
    assert retrieved_brand.user_id == user.id


@pytest.mark.unit
def test_foreign_key_constraint(test_db):
    """Test that foreign key constraints are enforced."""
    # Try to create brand with non-existent user_id
    fake_user_id = uuid4()
    brand = Brand(
        user_id=fake_user_id,
        title="Invalid Brand",
        description="Should fail"
    )

    test_db.add(brand)

    # This should raise an IntegrityError due to foreign key constraint
    # Note: SQLite in-memory might not enforce this strictly, but PostgreSQL will
    with pytest.raises(IntegrityError):
        test_db.commit()

    test_db.rollback()


@pytest.mark.unit
def test_cascade_delete(test_db):
    """Test that cascade delete works (deleting user deletes brands)."""
    # Create user
    user = User(
        email="cascade@example.com",
        name="Cascade User",
        password_hash="hashed"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    # Create brand for user
    brand = Brand(
        user_id=user.id,
        title="Cascade Brand",
        description="Will be deleted"
    )
    test_db.add(brand)
    test_db.commit()
    test_db.refresh(brand)

    brand_id = brand.id

    # Delete user
    test_db.delete(user)
    test_db.commit()

    # Brand should be deleted due to cascade
    deleted_brand = test_db.query(Brand).filter_by(id=brand_id).first()
    assert deleted_brand is None


@pytest.mark.unit
def test_jsonb_field(test_db):
    """Test JSONB field storage and retrieval."""
    user = User(
        email="jsonb@example.com",
        name="JSONB User",
        password_hash="hashed"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    # Create brand with JSONB data
    guidelines = {
        "colors": ["#FF0000", "#00FF00"],
        "fonts": ["Arial", "Helvetica"],
        "tone": "professional"
    }

    brand = Brand(
        user_id=user.id,
        title="JSONB Brand",
        brand_guidelines=guidelines
    )
    test_db.add(brand)
    test_db.commit()
    test_db.refresh(brand)

    # Retrieve and verify JSONB data
    retrieved_brand = test_db.query(Brand).filter_by(id=brand.id).first()
    assert retrieved_brand.brand_guidelines == guidelines
    assert retrieved_brand.brand_guidelines["tone"] == "professional"
    assert len(retrieved_brand.brand_guidelines["colors"]) == 2


@pytest.mark.unit
def test_complete_project_workflow(test_db):
    """Test creating a complete project with all related entities."""
    # Create user
    user = User(
        email="workflow@example.com",
        name="Workflow User",
        password_hash="hashed"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    # Create brand
    brand = Brand(
        user_id=user.id,
        title="Workflow Brand",
        description="Complete workflow test"
    )
    test_db.add(brand)
    test_db.commit()
    test_db.refresh(brand)

    # Create ad project
    project = AdProject(
        user_id=user.id,
        brand_id=brand.id,
        status="draft",
        ad_details={"duration": 30}
    )
    test_db.add(project)
    test_db.commit()
    test_db.refresh(project)

    # Create chat message
    message = ChatMessage(
        ad_project_id=project.id,
        role="user",
        content="Create a video ad"
    )
    test_db.add(message)
    test_db.commit()

    # Create script
    script = Script(
        ad_project_id=project.id,
        storyline="Product showcase",
        scenes=[{"scene": 1, "description": "Opening shot"}]
    )
    test_db.add(script)
    test_db.commit()

    # Create generation job
    job = GenerationJob(
        ad_project_id=project.id,
        job_type="scene_1",
        status="pending",
        input_params={"prompt": "Product showcase"}
    )
    test_db.add(job)
    test_db.commit()

    # Verify all entities exist and are related
    retrieved_project = test_db.query(AdProject).filter_by(id=project.id).first()
    assert retrieved_project is not None
    assert len(retrieved_project.chat_messages) == 1
    assert len(retrieved_project.scripts) == 1
    assert len(retrieved_project.generation_jobs) == 1


@pytest.mark.unit
def test_session_token_unique(test_db):
    """Test that session tokens must be unique."""
    user = User(
        email="session@example.com",
        name="Session User",
        password_hash="hashed"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    # Create first session
    token = "unique_token_12345"
    session1 = Session(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    test_db.add(session1)
    test_db.commit()

    # Try to create second session with same token
    session2 = Session(
        user_id=user.id,
        token=token,  # Same token
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    test_db.add(session2)

    # Should raise IntegrityError due to unique constraint
    with pytest.raises(IntegrityError):
        test_db.commit()

    test_db.rollback()
