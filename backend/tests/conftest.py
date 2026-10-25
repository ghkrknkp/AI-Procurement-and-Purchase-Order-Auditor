import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import User, UserRole
from app.security import get_password_hash, create_access_token

# Test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_procurement.db"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_submitter(db_session):
    user = User(
        name="Test Submitter",
        email="test_sub@edvexa.com",
        password_hash=get_password_hash("Password123!"),
        role=UserRole.SUBMITTER.value,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_reviewer(db_session):
    user = User(
        name="Test Reviewer",
        email="test_rev@edvexa.com",
        password_hash=get_password_hash("Password123!"),
        role=UserRole.REVIEWER.value,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def submitter_token(test_submitter):
    return create_access_token(data={"sub": test_submitter.email, "role": test_submitter.role, "user_id": test_submitter.id})

@pytest.fixture
def reviewer_token(test_reviewer):
    return create_access_token(data={"sub": test_reviewer.email, "role": test_reviewer.role, "user_id": test_reviewer.id})
