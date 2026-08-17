from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.cricket import Match
from app.schemas.stats import MatchResponse
from app.services.external_apis import ExternalAPIService
from typing import List

router = APIRouter()

@router.get("", response_model=List[MatchResponse])
async def list_matches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Match)
        .options(selectinload(Match.team_home), selectinload(Match.team_away))
    )
    return list(result.scalars().all())

@router.get("/live")
async def get_live_scores_summary():
    return ExternalAPIService.get_live_scores()

@router.get("/live/details")
async def get_live_match_details(match_id: int = 1):
    # Return high-quality, rich match details matching real world
    return ExternalAPIService.get_detailed_match(match_id)

@router.get("/{match_id}/commentary")
async def get_match_commentary(match_id: int):
    return {
        "match_id": match_id,
        "commentary": ExternalAPIService.get_ball_by_ball(match_id)
    }
