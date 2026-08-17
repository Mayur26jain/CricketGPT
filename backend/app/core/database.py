from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# Determine DB URL
if settings.USE_SQLITE:
    db_url = settings.SQLITE_DATABASE_URL
    connect_args = {"check_same_thread": False}
else:
    db_url = settings.DATABASE_URL
    connect_args = {}

# Create async engine
engine = create_async_engine(
    db_url,
    connect_args=connect_args,
    echo=False,
    future=True
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    """Dependency for API endpoints to get a DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
