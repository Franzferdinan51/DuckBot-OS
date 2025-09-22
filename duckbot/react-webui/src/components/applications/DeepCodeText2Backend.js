import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Server,
  Database,
  Settings,
  Play,
  Pause,
  X,
  CheckCircle,
  AlertCircle,
  Clock,
  Eye,
  Copy,
  Download,
  FolderOpen,
  Network,
  Shield,
  Zap,
  GitBranch,
  Users,
  Cloud,
  Key,
  Layers,
  Activity,
  Globe,
  Code,
  FileText,
  Folder,
  Terminal
} from 'lucide-react';

// Text2Backend Component
const DeepCodeText2Backend = ({ onClose }) => {
  // Form state
  const [step, setStep] = useState(1); // 1: Description, 2: Configuration, 3: Generation, 4: Results
  const [systemDescription, setSystemDescription] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentJob, setCurrentJob] = useState(null);
  const [generatedBackend, setGeneratedBackend] = useState(null);
  const [showCodePreview, setShowCodePreview] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  // Configuration state
  const [config, setConfig] = useState({
    architecture: 'monolithic',
    language: 'python',
    database: 'postgresql',
    authType: 'jwt',
    apis: [],
    projectName: 'my-backend-api',
    includeTests: true,
    includeDocumentation: true,
    includeDocker: true,
    includeCI: false,
    environment: 'development',
    logging: true,
    monitoring: false,
    caching: false,
  });

  // Predefined API endpoints
  const availableAPIs = [
    { id: 'users', label: 'User Management', icon: Users, description: 'CRUD operations for users' },
    { id: 'auth', label: 'Authentication', icon: Key, description: 'Login, logout, token refresh' },
    { id: 'products', label: 'Products', icon: Database, description: 'Product catalog management' },
    { id: 'orders', label: 'Orders', icon: FileText, description: 'Order processing and tracking' },
    { id: 'payments', label: 'Payments', icon: CreditCard, description: 'Payment processing' },
    { id: 'inventory', label: 'Inventory', icon: Package, description: 'Stock management' },
    { id: 'analytics', label: 'Analytics', icon: Activity, description: 'Data analysis and reporting' },
    { id: 'notifications', label: 'Notifications', icon: Bell, description: 'Email and push notifications' },
  ];

  // Architecture options
  const architectureOptions = [
    { value: 'monolithic', label: 'Monolithic', icon: '🏛️', description: 'Single unified application' },
    { value: 'microservices', label: 'Microservices', icon: '🔗', description: 'Distributed service architecture' },
    { value: 'serverless', label: 'Serverless', icon: '☁️', description: 'Function-based architecture' },
  ];

  // Language options
  const languageOptions = [
    { value: 'python', label: 'Python', icon: '🐍', description: 'FastAPI, Django, Flask' },
    { value: 'javascript', label: 'JavaScript', icon: '🟨', description: 'Node.js, Express' },
    { value: 'java', label: 'Java', icon: '☕', description: 'Spring Boot' },
    { value: 'go', label: 'Go', icon: '🔵', description: 'Gin, Echo' },
    { value: 'rust', label: 'Rust', icon: '🦀', description: 'Actix-web, Rocket' },
  ];

  // Database options
  const databaseOptions = [
    { value: 'postgresql', label: 'PostgreSQL', icon: '🐘', description: 'Relational database' },
    { value: 'mysql', label: 'MySQL', icon: '🐬', description: 'Popular relational database' },
    { value: 'mongodb', label: 'MongoDB', icon: '🍃', description: 'NoSQL document database' },
    { value: 'redis', label: 'Redis', icon: '🔴', description: 'In-memory data store' },
    { value: 'sqlite', label: 'SQLite', icon: '📦', description: 'Lightweight file-based database' },
  ];

  // Auth options
  const authOptions = [
    { value: 'jwt', label: 'JWT Tokens', icon: '🔑', description: 'JSON Web Token authentication' },
    { value: 'oauth', label: 'OAuth 2.0', icon: '🌐', description: 'Standard OAuth2 flow' },
    { value: 'session', label: 'Session-based', icon: '🍪', description: 'Server-side sessions' },
    { value: 'none', label: 'No Auth', icon: '🚫', description: 'No authentication' },
  ];

  // Processing steps
  const [processingSteps, setProcessingSteps] = useState([
    { id: 1, name: 'Requirements Analysis', status: 'pending', description: 'Analyzing system requirements' },
    { id: 2, name: 'Database Design', status: 'pending', description: 'Designing database schema' },
    { id: 3, name: 'API Design', status: 'pending', description: 'Designing RESTful APIs' },
    { id: 4, name: 'Code Generation', status: 'pending', description: 'Generating backend code' },
    { id: 5, name: 'Security Implementation', status: 'pending', description: 'Implementing security features' },
    { id: 6, name: 'Testing Setup', status: 'pending', description: 'Setting up tests and documentation' },
  ]);

  // Handle API toggle
  const toggleAPI = useCallback((apiId) => {
    setConfig(prev => ({
      ...prev,
      apis: prev.apis.includes(apiId)
        ? prev.apis.filter(a => a !== apiId)
        : [...prev.apis, apiId]
    }));
  }, []);

  // Generate backend
  const generateBackend = useCallback(async () => {
    if (!systemDescription.trim()) {
      alert('Please provide a system description');
      return;
    }

    setIsProcessing(true);
    setCurrentJob({
      id: `job_${Date.now()}`,
      type: 'text2backend',
      status: 'processing',
      progress: 0,
      created_at: new Date().toISOString(),
    });

    // Simulate processing
    for (let i = 0; i < processingSteps.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 2000));

      processingSteps[i].status = 'processing';
      if (i > 0) processingSteps[i - 1].status = 'completed';

      setProcessingSteps([...processingSteps]);
      setCurrentJob(prev => ({ ...prev, progress: ((i + 1) / processingSteps.length) * 100 }));
    }

    processingSteps[processingSteps.length - 1].status = 'completed';
    setProcessingSteps([...processingSteps]);
    setCurrentJob(prev => ({ ...prev, status: 'completed', progress: 100 }));

    // Generate mock backend structure
    const mockBackend = {
      name: config.projectName,
      architecture: config.architecture,
      structure: generateBackendStructure(),
      features: config.apis,
      config: config,
    };

    setGeneratedBackend(mockBackend);
    setIsProcessing(false);
  }, [systemDescription, config, processingSteps]);

  // Generate backend structure
  const generateBackendStructure = () => {
    const structure = {};

    // Main application directory
    structure['src/'] = {
      'controllers/': generateControllers(),
      'models/': generateModels(),
      'routes/': generateRoutes(),
      'middleware/': generateMiddleware(),
      'services/': generateServices(),
      'utils/': generateUtils(),
      'config/': generateConfig(),
      'main.py': generateMainFile(),
    };

    // Database migrations
    structure['migrations/'] = {
      '001_initial_schema.py': generateMigration(),
    };

    // Tests
    if (config.includeTests) {
      structure['tests/'] = {
        'test_models.py': '// Model tests',
        'test_routes.py': '// Route tests',
        'test_services.py': '// Service tests',
      };
    }

    // Documentation
    if (config.includeDocumentation) {
      structure['docs/'] = {
        'API.md': '# API Documentation',
        'DEPLOYMENT.md': '# Deployment Guide',
      };
    }

    // Docker files
    if (config.includeDocker) {
      structure['Dockerfile'] = generateDockerfile();
      structure['docker-compose.yml'] = generateDockerCompose();
    }

    // Configuration files
    structure['requirements.txt'] = generateRequirements();
    structure['.env.example'] = generateEnvExample();
    structure['README.md'] = generateReadme();

    return structure;
  };

  // Generate various backend components
  const generateControllers = () => {
    const controllers = {};

    config.apis.forEach(api => {
      controllers[`${api}_controller.py`] = `from fastapi import APIRouter, Depends, HTTPException
from ..models.${api} import ${api.charAt(0).toUpperCase() + api.slice(1)}
from ..services.${api}_service import ${api.charAt(0).toUpperCase() + api.slice(1)}Service
from ..middleware.auth import get_current_user

router = APIRouter(prefix="/api/v1/${api}", tags=["${api}"])

@router.get("/", response_model=list[${api.charAt(0).toUpperCase() + api.slice(1)}])
async def get_${api}s(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user)
):
    """Get all ${api}"""
    service = ${api.charAt(0).toUpperCase() + api.slice(1)}Service()
    return await service.get_all(skip=skip, limit=limit)

@router.get("/{${api}_id}", response_model=${api.charAt(0).toUpperCase() + api.slice(1)})
async def get_${api}(
    ${api}_id: int,
    current_user = Depends(get_current_user)
):
    """Get a specific ${api}"""
    service = ${api.charAt(0).toUpperCase() + api.slice(1)}Service()
    result = await service.get_by_id(${api}_id)
    if not result:
        raise HTTPException(status_code=404, detail="${api.charAt(0).toUpperCase() + api.slice(1)} not found")
    return result

@router.post("/", response_model=${api.charAt(0).toUpperCase() + api.slice(1)})
async def create_${api}(
    ${api}: ${api.charAt(0).toUpperCase() + api.slice(1)}Create,
    current_user = Depends(get_current_user)
):
    """Create a new ${api}"""
    service = ${api.charAt(0).toUpperCase() + api.slice(1)}Service()
    return await service.create(${api})

@router.put("/{${api}_id}", response_model=${api.charAt(0).toUpperCase() + api.slice(1)})
async def update_${api}(
    ${api}_id: int,
    ${api}: ${api.charAt(0).toUpperCase() + api.slice(1)}Update,
    current_user = Depends(get_current_user)
):
    """Update a ${api}"""
    service = ${api.charAt(0).toUpperCase() + api.slice(1)}Service()
    result = await service.update(${api}_id, ${api})
    if not result:
        raise HTTPException(status_code=404, detail="${api.charAt(0).toUpperCase() + api.slice(1)} not found")
    return result

@router.delete("/{${api}_id}")
async def delete_${api}(
    ${api}_id: int,
    current_user = Depends(get_current_user)
):
    """Delete a ${api}"""
    service = ${api.charAt(0).toUpperCase() + api.slice(1)}Service()
    result = await service.delete(${api}_id)
    if not result:
        raise HTTPException(status_code=404, detail="${api.charAt(0).toUpperCase() + api.slice(1)} not found")
    return {"message": "${api.charAt(0).toUpperCase() + api.slice(1)} deleted successfully"}`;
    });

    return controllers;
  };

  const generateModels = () => {
    const models = {};

    // Base model
    models['base.py'] = `from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)`;

    // User model (if auth is enabled)
    if (config.authType !== 'none' || config.apis.includes('users')) {
      models['user.py'] = `from sqlalchemy import Column, String, Boolean, DateTime
from .base import BaseModel
from passlib.context import CryptContext
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    def verify_password(self, plain_password: str) -> bool:
        return pwd_context.verify(plain_password, self.hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    def set_password(self, password: str):
        self.hashed_password = self.get_password_hash(password)`;
    }

    // API models
    config.apis.forEach(api => {
      models[`${api}.py`] = `from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, Float
from .base import BaseModel
from datetime import datetime

class ${api.charAt(0).toUpperCase() + api.slice(1)}(BaseModel):
    __tablename__ = "${api}s"

    name = Column(String(255), nullable=False)
    description = Column(Text)
    # Add additional fields based on API type
    ${generateModelFields(api)}

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }`;
    });

    return models;
  };

  const generateModelFields = (api) => {
    const fieldMap = {
      'users': 'email = Column(String(255), unique=True, index=True)\n    password_hash = Column(String(255))\n    is_active = Column(Boolean, default=True)',
      'products': 'price = Column(Float, nullable=False)\n    stock_quantity = Column(Integer, default=0)\n    category = Column(String(100))',
      'orders': 'user_id = Column(Integer, nullable=False)\n    total_amount = Column(Float, nullable=False)\n    status = Column(String(50), default="pending")',
      'payments': 'order_id = Column(Integer, nullable=False)\n    amount = Column(Float, nullable=False)\n    payment_method = Column(String(50))',
      'inventory': 'product_id = Column(Integer, nullable=False)\n    quantity = Column(Integer, nullable=False)\n    location = Column(String(100))',
      'analytics': 'metric_name = Column(String(255), nullable=False)\n    metric_value = Column(Float)\n    timestamp = Column(DateTime, default=datetime.utcnow)',
      'notifications': 'user_id = Column(Integer, nullable=False)\n    message = Column(Text, nullable=False)\n    is_read = Column(Boolean, default=False)',
      'auth': 'user_id = Column(Integer, nullable=False)\n    token = Column(String(255), nullable=False)\n    expires_at = Column(DateTime)',
    'default': 'value = Column(Text)\n    metadata = Column(Text)'
    };

    return fieldMap[api] || fieldMap['default'];
  };

  const generateRoutes = () => {
    const routes = {};

    config.apis.forEach(api => {
      routes[`${api}.py`] = `from fastapi import APIRouter
from ..controllers.${api}_controller import router as ${api}_router

router = APIRouter()
router.include_router(${api}_router, prefix="/${api}")`;
    });

    return routes;
  };

  const generateMiddleware = () => {
    const middleware = {};

    // Auth middleware
    if (config.authType !== 'none') {
      middleware['auth.py'] = `from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..models.user import User
from ..database import get_db

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    # Implement JWT token validation here
    # This is a placeholder implementation
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )`;
    }

    // Error handling middleware
    middleware['errors.py'] = `from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

async def http_exception_handler(request: Request, exc):
    """HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )`;

    return middleware;
  };

  const generateServices = () => {
    const services = {};

    config.apis.forEach(api => {
      services[`${api}_service.py`] = `from sqlalchemy.orm import Session
from ..models.${api} import ${api.charAt(0).toUpperCase() + api.slice(1)}
from ..database import get_db
from typing import List, Optional

class ${api.charAt(0).toUpperCase() + api.slice(1)}Service:
    async def get_all(self, skip: int = 0, limit: int = 100, db: Session = None) -> List[${api.charAt(0).toUpperCase() + api.slice(1)}]:
        """Get all ${api}s"""
        if db is None:
            db = next(get_db())

        ${api}s = db.query(${api.charAt(0).toUpperCase() + api.slice(1)}).offset(skip).limit(limit).all()
        return ${api}s

    async def get_by_id(self, ${api}_id: int, db: Session = None) -> Optional[${api.charAt(0).toUpperCase() + api.slice(1)}]:
        """Get ${api} by ID"""
        if db is None:
            db = next(get_db())

        ${api} = db.query(${api.charAt(0).toUpperCase() + api.slice(1)}).filter(${api.charAt(0).toUpperCase() + api.slice(1)}.id == ${api}_id).first()
        return ${api}

    async def create(self, ${api}: ${api.charAt(0).toUpperCase() + api.slice(1)}Create, db: Session = None) -> ${api.charAt(0).toUpperCase() + api.slice(1)}:
        """Create a new ${api}"""
        if db is None:
            db = next(get_db())

        db_${api} = ${api.charAt(0).toUpperCase() + api.slice(1)}(**${api}.dict())
        db.add(db_${api})
        db.commit()
        db.refresh(db_${api})
        return db_${api}

    async def update(self, ${api}_id: int, ${api}: ${api.charAt(0).toUpperCase() + api.slice(1)}Update, db: Session = None) -> Optional[${api.charAt(0).toUpperCase() + api.slice(1)}]:
        """Update a ${api}"""
        if db is None:
            db = next(get_db())

        db_${api} = db.query(${api.charAt(0).toUpperCase() + api.slice(1)}).filter(${api.charAt(0).toUpperCase() + api.slice(1)}.id == ${api}_id).first()
        if not db_${api}:
            return None

        for key, value in ${api}.dict(exclude_unset=True).items():
            setattr(db_${api}, key, value)

        db.commit()
        db.refresh(db_${api})
        return db_${api}

    async def delete(self, ${api}_id: int, db: Session = None) -> bool:
        """Delete a ${api}"""
        if db is None:
            db = next(get_db())

        ${api} = db.query(${api.charAt(0).toUpperCase() + api.slice(1)}).filter(${api.charAt(0).toUpperCase() + api.slice(1)}.id == ${api}_id).first()
        if not ${api}:
            return False

        db.delete(${api})
        db.commit()
        return True`;
    });

    return services;
  };

  const generateUtils = () => ({
    'database.py': `from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./${config.projectName}.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()`,
    'security.py': `from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt`,
    'logging.py': `import logging
import sys

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("${config.projectName}.log")
        ]
    )

    return logging.getLogger(__name__)`,
  });

  const generateConfig = () => ({
    'settings.py': `import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings"""

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"${config.database}://localhost/${config.projectName}")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Application
    APP_NAME: str = "${config.projectName}"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    VERSION: str = "1.0.0"

    # External services
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    class Config:
        env_file = ".env"

settings = Settings()`,
  });

  const generateMainFile = () => `from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging

from .routes import ${config.apis.map(api => api).join(', ')}
from .middleware.errors import global_exception_handler, http_exception_handler
from .utils.logging import setup_logging

# Setup logging
logger = setup_logging()

# Create FastAPI app
app = FastAPI(
    title="${config.projectName}",
    description="Backend API generated by DeepCode Text2Backend",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Include routers
${config.apis.map(api => `app.include_router(${api}.router)`).join('\n')}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to ${config.projectName} API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "${config.projectName}"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )`;

  const generateMigration = () => `"""Initial migration for ${config.projectName}"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    """Upgrade schema."""
    # Create users table if auth is enabled
    ${config.authType !== 'none' ? `
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    ` : ''}

    # Create API tables
    ${config.apis.map(api => `
    op.create_table(
        '${api}s',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        ${generateMigrationFields(api)}
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_${api}s_id'), '${api}s', ['id'], unique=False)
    `).join('\n')}

def downgrade():
    """Downgrade schema."""
    ${config.apis.map(api => `
    op.drop_index(op.f('ix_${api}s_id'), table_name='${api}s')
    op.drop_table('${api}s')
    `).join('\n')}

    ${config.authType !== 'none' ? `
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    ` : ''}`;

  const generateMigrationFields = (api) => {
    const fieldMap = {
      'users': '',
      'products': 'sa.Column(\'price\', sa.Float(), nullable=False),\\n        sa.Column(\'stock_quantity\', sa.Integer(), nullable=True),\\n        sa.Column(\'category\', sa.String(length=100), nullable=True),',
      'orders': 'sa.Column(\'user_id\', sa.Integer(), nullable=False),\\n        sa.Column(\'total_amount\', sa.Float(), nullable=False),\\n        sa.Column(\'status\', sa.String(length=50), nullable=True),',
      'payments': 'sa.Column(\'order_id\', sa.Integer(), nullable=False),\\n        sa.Column(\'amount\', sa.Float(), nullable=False),\\n        sa.Column(\'payment_method\', sa.String(length=50), nullable=True),',
      'inventory': 'sa.Column(\'product_id\', sa.Integer(), nullable=False),\\n        sa.Column(\'quantity\', sa.Integer(), nullable=False),\\n        sa.Column(\'location\', sa.String(length=100), nullable=True),',
      'analytics': 'sa.Column(\'metric_name\', sa.String(length=255), nullable=False),\\n        sa.Column(\'metric_value\', sa.Float(), nullable=True),\\n        sa.Column(\'timestamp\', sa.DateTime(), nullable=True),',
      'notifications': 'sa.Column(\'user_id\', sa.Integer(), nullable=False),\\n        sa.Column(\'message\', sa.Text(), nullable=False),\\n        sa.Column(\'is_read\', sa.Boolean(), nullable=True),',
      'auth': 'sa.Column(\'user_id\', sa.Integer(), nullable=False),\\n        sa.Column(\'token\', sa.String(length=255), nullable=False),\\n        sa.Column(\'expires_at\', sa.DateTime(), nullable=True),',
      'default': 'sa.Column(\'value\', sa.Text(), nullable=True),\\n        sa.Column(\'metadata\', sa.Text(), nullable=True),'
    };

    return fieldMap[api] || fieldMap['default'];
  };

  const generateDockerfile = () => `FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]`;

  const generateDockerCompose = () => `version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${config.database}://postgres:password@db:5432/${config.projectName}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs

  db:
    image: ${config.database}:latest
    environment:
      - POSTGRES_DB=${config.projectName}
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:`;

  const generateRequirements = () => `fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
redis==5.0.1
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2`;

  const generateEnvExample = () => `# Database Configuration
DATABASE_URL=${config.database}://postgres:password@localhost:5432/${config.projectName}

# Security
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://localhost:6379

# Application Settings
DEBUG=True
ENVIRONMENT=development

# External Services (if needed)
# STRIPE_API_KEY=your_stripe_key
# SENDGRID_API_KEY=your_sendgrid_key`;

  const generateReadme = () => `# ${config.projectName}

Backend API generated by DeepCode Text2Backend

## Architecture
- **Framework**: FastAPI (${config.language})
- **Database**: ${config.database}
- **Authentication**: ${config.authType}
- **Architecture**: ${config.architecture}

## Features
${config.apis.map(api => `- ${api.charAt(0).toUpperCase() + api.slice(1)} API`).join('\n')}

## Quick Start

### Prerequisites
- Python 3.11+
- ${config.database}
- Redis (optional)

### Installation

1. Clone the repository
\`\`\`bash
git clone <repository-url>
cd ${config.projectName}
\`\`\`

2. Create virtual environment
\`\`\`bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
\`\`\`

3. Install dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

4. Set up environment variables
\`\`\`bash
cp .env.example .env
# Edit .env with your configuration
\`\`\`

5. Run database migrations
\`\`\`bash
alembic upgrade head
\`\`\`

6. Start the application
\`\`\`bash
uvicorn src.main:app --reload
\`\`\`

The API will be available at http://localhost:8000
API documentation will be available at http://localhost:8000/docs

## API Endpoints

### Base URL: http://localhost:8000/api/v1
${config.apis.map(api => `
#### ${api.charAt(0).toUpperCase() + api.slice(1)}
- \`GET /${api}\` - Get all ${api}s
- \`GET /${api}/{id}\` - Get specific ${api}
- \`POST /${api}\` - Create new ${api}
- \`PUT /${api}/{id}\` - Update ${api}
- \`DELETE /${api}/{id}\` - Delete ${api}
`).join('')}

## Testing

Run tests:
\`\`\`bash
pytest
\`\`\`

## Docker

Build and run with Docker:
\`\`\`bash
docker-compose up --build
\`\`\`

## License

MIT`;

  // Download backend
  const downloadBackend = useCallback(() => {
    if (!generatedBackend) return;

    const projectFiles = [];

    const flattenStructure = (structure, path = '') => {
      Object.entries(structure).forEach(([key, value]) => {
        const fullPath = path ? `${path}/${key}` : key;

        if (typeof value === 'object' && !value.toString().includes('exports')) {
          flattenStructure(value, fullPath);
        } else {
          projectFiles.push({ path: fullPath, content: value });
        }
      });
    };

    flattenStructure(generatedBackend.structure);

    const zipContent = projectFiles.map(file =>
      `File: ${file.path}\n\n${file.content}\n${'='.repeat(50)}\n`
    ).join('\n');

    const blob = new Blob([zipContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${config.projectName}_backend_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [generatedBackend, config]);

  // Reset form
  const resetForm = useCallback(() => {
    setSystemDescription('');
    setStep(1);
    setGeneratedBackend(null);
    setCurrentJob(null);
    setShowCodePreview(false);
    setConfig({
      architecture: 'monolithic',
      language: 'python',
      database: 'postgresql',
      authType: 'jwt',
      apis: [],
      projectName: 'my-backend-api',
      includeTests: true,
      includeDocumentation: true,
      includeDocker: true,
      includeCI: false,
      environment: 'development',
      logging: true,
      monitoring: false,
      caching: false,
    });
    processingSteps.forEach(step => step.status = 'pending');
  }, []);

  return (
    <div className="h-full bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Server className="w-6 h-6 text-green-400" />
            <h2 className="text-white text-xl font-semibold">Text2Backend</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="bg-gray-800 px-6 py-4">
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          {[1, 2, 3, 4].map((stepNumber) => (
            <div key={stepNumber} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step >= stepNumber
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-700 text-gray-400'
                }`}
              >
                {stepNumber}
              </div>
              <div className={`ml-2 text-sm font-medium ${
                step === stepNumber ? 'text-green-400' : 'text-gray-400'
              }`}>
                {stepNumber === 1 && 'Description'}
                {stepNumber === 2 && 'Configuration'}
                {stepNumber === 3 && 'Generation'}
                {stepNumber === 4 && 'Results'}
              </div>
              {stepNumber < 4 && (
                <div className={`mx-4 w-16 h-0.5 ${
                  step > stepNumber ? 'bg-green-600' : 'bg-gray-700'
                }`} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Step 1: Description */}
        {step === 1 && (
          <div className="max-w-4xl mx-auto space-y-6">
            <h3 className="text-white text-lg font-medium">Describe Your Backend System</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-gray-300 text-sm mb-2">System Description</label>
                <textarea
                  value={systemDescription}
                  onChange={(e) => setSystemDescription(e.target.value)}
                  placeholder="Describe your backend system in detail. What APIs should it have? What data models? What business logic? What integrations?"
                  className="w-full h-48 bg-gray-800 text-white rounded-lg border border-gray-600 px-4 py-3 resize-none focus:outline-none focus:ring-2 focus:ring-green-500"
                />
                <p className="text-gray-500 text-sm mt-2">
                  {systemDescription.length}/1000 characters
                </p>
              </div>

              <div>
                <label className="block text-gray-300 text-sm mb-2">Project Name</label>
                <input
                  type="text"
                  value={config.projectName}
                  onChange={(e) => setConfig(prev => ({ ...prev, projectName: e.target.value }))}
                  placeholder="my-backend-api"
                  className="w-full bg-gray-800 text-white rounded-lg border border-gray-600 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={resetForm}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors"
              >
                Reset
              </button>
              <button
                onClick={() => setStep(2)}
                disabled={!systemDescription.trim()}
                className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Configuration */}
        {step === 2 && (
          <div className="max-w-6xl mx-auto space-y-6">
            <h3 className="text-white text-lg font-medium">Configure Your Backend System</h3>

            {/* Architecture Selection */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h4 className="text-white font-medium mb-4">Architecture</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {architectureOptions.map((arch) => (
                  <button
                    key={arch.value}
                    onClick={() => setConfig(prev => ({ ...prev, architecture: arch.value }))}
                    className={`p-4 rounded-lg border-2 transition-colors text-left ${
                      config.architecture === arch.value
                        ? 'border-green-500 bg-green-500/20'
                        : 'border-gray-600 hover:border-gray-500 hover:bg-gray-700'
                    }`}
                  >
                    <div className="text-2xl mb-2">{arch.icon}</div>
                    <div className="text-white font-medium">{arch.label}</div>
                    <div className="text-gray-400 text-sm">{arch.description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Technology Stack */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Language */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h4 className="text-white font-medium mb-4">Language</h4>
                <div className="space-y-3">
                  {languageOptions.map((lang) => (
                    <button
                      key={lang.value}
                      onClick={() => setConfig(prev => ({ ...prev, language: lang.value }))}
                      className={`w-full p-3 rounded-lg border-2 transition-colors text-left ${
                        config.language === lang.value
                          ? 'border-green-500 bg-green-500/20'
                          : 'border-gray-600 hover:border-gray-500 hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <span className="text-lg">{lang.icon}</span>
                        <div>
                          <div className="text-white font-medium">{lang.label}</div>
                          <div className="text-gray-400 text-sm">{lang.description}</div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Database */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h4 className="text-white font-medium mb-4">Database</h4>
                <div className="space-y-3">
                  {databaseOptions.map((db) => (
                    <button
                      key={db.value}
                      onClick={() => setConfig(prev => ({ ...prev, database: db.value }))}
                      className={`w-full p-3 rounded-lg border-2 transition-colors text-left ${
                        config.database === db.value
                          ? 'border-green-500 bg-green-500/20'
                          : 'border-gray-600 hover:border-gray-500 hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <span className="text-lg">{db.icon}</span>
                        <div>
                          <div className="text-white font-medium">{db.label}</div>
                          <div className="text-gray-400 text-sm">{db.description}</div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Authentication */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h4 className="text-white font-medium mb-4">Authentication</h4>
                <div className="space-y-3">
                  {authOptions.map((auth) => (
                    <button
                      key={auth.value}
                      onClick={() => setConfig(prev => ({ ...prev, authType: auth.value }))}
                      className={`w-full p-3 rounded-lg border-2 transition-colors text-left ${
                        config.authType === auth.value
                          ? 'border-green-500 bg-green-500/20'
                          : 'border-gray-600 hover:border-gray-500 hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <span className="text-lg">{auth.icon}</span>
                        <div>
                          <div className="text-white font-medium">{auth.label}</div>
                          <div className="text-gray-400 text-sm">{auth.description}</div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* API Endpoints */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h4 className="text-white font-medium mb-4">API Endpoints</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {availableAPIs.map((api) => {
                  const Icon = api.icon;
                  return (
                    <button
                      key={api.id}
                      onClick={() => toggleAPI(api.id)}
                      className={`p-4 rounded-lg border-2 transition-colors text-left ${
                        config.apis.includes(api.id)
                          ? 'border-green-500 bg-green-500/20'
                          : 'border-gray-600 hover:border-gray-500 hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <Icon className="w-5 h-5 text-green-400" />
                        <div>
                          <div className="text-white font-medium">{api.label}</div>
                          <div className="text-gray-400 text-sm">{api.description}</div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Additional Options */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h4 className="text-white font-medium mb-4">Additional Features</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={config.includeTests}
                    onChange={(e) => setConfig(prev => ({ ...prev, includeTests: e.target.checked }))}
                    className="rounded w-4 h-4 text-green-600 bg-gray-700 border-gray-600"
                  />
                  <span className="text-gray-300">Include Tests</span>
                </label>

                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={config.includeDocumentation}
                    onChange={(e) => setConfig(prev => ({ ...prev, includeDocumentation: e.target.checked }))}
                    className="rounded w-4 h-4 text-green-600 bg-gray-700 border-gray-600"
                  />
                  <span className="text-gray-300">Documentation</span>
                </label>

                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={config.includeDocker}
                    onChange={(e) => setConfig(prev => ({ ...prev, includeDocker: e.target.checked }))}
                    className="rounded w-4 h-4 text-green-600 bg-gray-700 border-gray-600"
                  />
                  <span className="text-gray-300">Docker Support</span>
                </label>

                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={config.includeCI}
                    onChange={(e) => setConfig(prev => ({ ...prev, includeCI: e.target.checked }))}
                    className="rounded w-4 h-4 text-green-600 bg-gray-700 border-gray-600"
                  />
                  <span className="text-gray-300">CI/CD Pipeline</span>
                </label>

                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={config.logging}
                    onChange={(e) => setConfig(prev => ({ ...prev, logging: e.target.checked }))}
                    className="rounded w-4 h-4 text-green-600 bg-gray-700 border-gray-600"
                  />
                  <span className="text-gray-300">Logging</span>
                </label>

                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={config.monitoring}
                    onChange={(e) => setConfig(prev => ({ ...prev, monitoring: e.target.checked }))}
                    className="rounded w-4 h-4 text-green-600 bg-gray-700 border-gray-600"
                  />
                  <span className="text-gray-300">Monitoring</span>
                </label>
              </div>
            </div>

            <div className="flex justify-between space-x-3">
              <button
                onClick={() => setStep(1)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors"
              >
                Previous
              </button>
              <button
                onClick={() => setStep(3)}
                className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Generation */}
        {step === 3 && (
          <div className="max-w-4xl mx-auto space-y-6">
            <h3 className="text-white text-lg font-medium">Generate Your Backend System</h3>

            {!currentJob && !generatedBackend && (
              <div className="bg-gray-800 rounded-lg p-6 text-center">
                <Server className="w-16 h-16 text-green-400 mx-auto mb-4" />
                <h4 className="text-white text-lg font-medium mb-2">Ready to Generate</h4>
                <p className="text-gray-400 mb-6">
                  Based on your description and configuration, we'll generate a complete backend system with:
                </p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-400">{config.apis.length}</div>
                    <div className="text-gray-400 text-sm">APIs</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-400">{config.language}</div>
                    <div className="text-gray-400 text-sm">Language</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-400">{config.database}</div>
                    <div className="text-gray-400 text-sm">Database</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-400">{config.architecture}</div>
                    <div className="text-gray-400 text-sm">Architecture</div>
                  </div>
                </div>
                <button
                  onClick={generateBackend}
                  className="px-6 py-3 bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors font-medium"
                >
                  Generate Backend System
                </button>
              </div>
            )}

            {/* Processing UI */}
            {currentJob && isProcessing && (
              <div className="space-y-4">
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-gray-300">Progress</span>
                    <span className="text-white font-medium">{currentJob.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${currentJob.progress}%` }}
                    />
                  </div>
                </div>

                <div className="space-y-3">
                  {processingSteps.map((step) => (
                    <div
                      key={step.id}
                      className="flex items-center space-x-3 p-3 bg-gray-800 rounded-lg"
                    >
                      {step.status === 'pending' && <Clock className="w-5 h-5 text-gray-400" />}
                      {step.status === 'processing' && <Play className="w-5 h-5 text-green-400 animate-pulse" />}
                      {step.status === 'completed' && <CheckCircle className="w-5 h-5 text-green-400" />}
                      <div className="flex-1">
                        <div className="text-white font-medium">{step.name}</div>
                        <div className="text-gray-400 text-sm">{step.description}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {generatedBackend && (
              <div className="flex justify-center">
                <button
                  onClick={() => setStep(4)}
                  className="px-6 py-3 bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors font-medium"
                >
                  View Generated Backend
                </button>
              </div>
            )}
          </div>
        )}

        {/* Step 4: Results */}
        {step === 4 && generatedBackend && (
          <div className="max-w-6xl mx-auto space-y-6">
            <h3 className="text-white text-lg font-medium">Generated Backend System</h3>

            {/* Project Summary */}
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-white font-medium">{generatedBackend.name}</h4>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setShowCodePreview(!showCodePreview)}
                    className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors text-sm"
                  >
                    <Eye className="w-4 h-4 inline mr-1" />
                    {showCodePreview ? 'Hide' : 'Show'} Code
                  </button>
                  <button
                    onClick={downloadBackend}
                    className="px-3 py-1 bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors text-sm"
                  >
                    <Download className="w-4 h-4 inline mr-1" />
                    Download
                  </button>
                  <button
                    onClick={resetForm}
                    className="px-3 py-1 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors text-sm"
                  >
                    <Play className="w-4 h-4 inline mr-1" />
                    New Project
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-400">{generatedBackend.features.length}</div>
                  <div className="text-gray-400 text-sm">APIs</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-400">{generatedBackend.config.language}</div>
                  <div className="text-gray-400 text-sm">Language</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-400">{generatedBackend.config.database}</div>
                  <div className="text-gray-400 text-sm">Database</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-400">{Object.keys(generatedBackend.structure).length}</div>
                  <div className="text-gray-400 text-sm">Directories</div>
                </div>
              </div>
            </div>

            {/* File Structure */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h4 className="text-white font-medium mb-4">Project Structure</h4>
              <Folder structure={generatedBackend.structure} />
            </div>

            {/* Quick Start Guide */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h4 className="text-white font-medium mb-4">Quick Start Guide</h4>
              <div className="space-y-4">
                <div className="bg-gray-700 rounded-lg p-4">
                  <h5 className="text-white font-medium mb-2">1. Install Dependencies</h5>
                  <pre className="text-gray-300 text-sm bg-gray-900 p-3 rounded overflow-x-auto">
pip install -r requirements.txt
                  </pre>
                </div>

                <div className="bg-gray-700 rounded-lg p-4">
                  <h5 className="text-white font-medium mb-2">2. Set Environment Variables</h5>
                  <pre className="text-gray-300 text-sm bg-gray-900 p-3 rounded overflow-x-auto">
cp .env.example .env
# Edit .env with your database credentials and secret keys
                  </pre>
                </div>

                <div className="bg-gray-700 rounded-lg p-4">
                  <h5 className="text-white font-medium mb-2">3. Run Database Migrations</h5>
                  <pre className="text-gray-300 text-sm bg-gray-900 p-3 rounded overflow-x-auto">
alembic upgrade head
                  </pre>
                </div>

                <div className="bg-gray-700 rounded-lg p-4">
                  <h5 className="text-white font-medium mb-2">4. Start the Server</h5>
                  <pre className="text-gray-300 text-sm bg-gray-900 p-3 rounded overflow-x-auto">
uvicorn src.main:app --reload
                  </pre>
                </div>

                <div className="bg-gray-700 rounded-lg p-4">
                  <h5 className="text-white font-medium mb-2">5. Access API Documentation</h5>
                  <p className="text-gray-300">
                    Open your browser to <span className="text-blue-400">http://localhost:8000/docs</span> for interactive API documentation.
                  </p>
                </div>
              </div>
            </div>

            {/* Code Preview */}
            {showCodePreview && (
              <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-white font-medium">Code Preview</h4>
                  <select
                    value={selectedFile || ''}
                    onChange={(e) => setSelectedFile(e.target.value)}
                    className="bg-gray-700 text-white rounded px-2 py-1 text-sm"
                  >
                    <option value="">Select a file to preview</option>
                    {flattenFileList(generatedBackend.structure).map(file => (
                      <option key={file.path} value={file.path}>{file.path}</option>
                    ))}
                  </select>
                </div>
                {selectedFile && (
                  <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                    <pre className="text-gray-300 text-sm">
                      {getFileContent(generatedBackend.structure, selectedFile)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Reuse Folder component from Text2Web
DeepCodeText2Backend.Folder = require('./DeepCodeText2Web').Folder;

// Helper functions (reused from Text2Web)
const flattenFileList = (structure, path = '') => {
  let files = [];

  Object.entries(structure).forEach(([key, value]) => {
    const fullPath = path ? `${path}/${key}` : key;

    if (typeof value === 'object' && !value.toString().includes('exports')) {
      files = files.concat(flattenFileList(value, fullPath));
    } else {
      files.push({ path: fullPath, content: value });
    }
  });

  return files;
};

const getFileContent = (structure, filePath) => {
  const parts = filePath.split('/');
  let current = structure;

  for (const part of parts) {
    if (current[part]) {
      current = current[part];
    } else {
      return 'File not found';
    }
  }

  return typeof current === 'string' ? current : JSON.stringify(current, null, 2);
};

// Missing icons
const CreditCard = () => <div>💳</div>;
const Package = () => <div>📦</div>;
const Bell = () => <div>🔔</div>;

export default DeepCodeText2Backend;