import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.ai.models import AIProviderLog, GenerationHistory, PromptHistory


class PromptHistoryRepository(BaseRepository[PromptHistory]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, PromptHistory)

    async def get_or_create(self, purpose: str, version: int, template: str) -> PromptHistory:
        stmt = select(PromptHistory).where(
            PromptHistory.purpose == purpose, PromptHistory.version == version
        )
        existing = (await self._db.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            return existing
        return await self.create(
            purpose=purpose,
            version=version,
            prompt_hash=hashlib.sha256(template.encode()).hexdigest(),
            template=template,
        )


class GenerationHistoryRepository(BaseRepository[GenerationHistory]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, GenerationHistory)


class AIProviderLogRepository(BaseRepository[AIProviderLog]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, AIProviderLog)
