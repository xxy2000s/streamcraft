import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from database import Base, get_db
from models import User
from utils.security import get_password_hash

# 测试数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """创建测试数据库表"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)

@pytest.fixture
def test_user():
    """创建测试用户"""
    db = TestingSessionLocal()
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()

def get_auth_token(client, username="testuser", password="password123"):
    """获取认证token"""
    response = client.post("/api/v1/login", data={
        "username": username,
        "password": password
    })
    return response.json()["access_token"]

class TestAuth:
    def test_register_user(self, client):
        """测试用户注册"""
        response = client.post("/api/v1/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        assert response.json()["success"] == True

    def test_login_user(self, client, test_user):
        """测试用户登录"""
        response = client.post("/api/v1/login", data={
            "username": "testuser",
            "password": "password123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_invalid_credentials(self, client):
        """测试无效凭据登录"""
        response = client.post("/api/v1/login", data={
            "username": "nonexistent",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

class TestCollections:
    def test_create_collection(self, client, test_user):
        """测试创建收藏"""
        token = get_auth_token(client)
        response = client.post("/api/v1/collections", 
            json={
                "platform": "xiaohongshu",
                "content_id": "test123",
                "title": "测试收藏",
                "content": "测试内容"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "测试收藏"
        assert data["platform"] == "xiaohongshu"

    def test_get_collections(self, client, test_user):
        """测试获取收藏列表"""
        token = get_auth_token(client)
        response = client.get("/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_unauthorized_access(self, client):
        """测试未授权访问"""
        response = client.get("/api/v1/collections")
        assert response.status_code == 401

class TestCategories:
    def test_create_category(self, client, test_user):
        """测试创建分类"""
        # 需要管理员权限
        token = get_auth_token(client)
        response = client.post("/api/v1/categories",
            json={
                "name": "测试分类",
                "description": "测试描述"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        # 普通用户应该被拒绝
        assert response.status_code == 403

class TestHealth:
    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

if __name__ == "__main__":
    pytest.main(["-v"])