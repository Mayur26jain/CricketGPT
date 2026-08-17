from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class TeamResponse(BaseModel):
    id: int
    name: str
    short_name: str
    team_type: str
    logo_url: Optional[str] = None

    class Config:
        from_attributes = True

class PlayerStatsResponse(BaseModel):
    id: int
    format: str
    matches_played: int
    innings_batted: int
    runs_scored: int
    highest_score: int
    batting_average: float
    strike_rate: float
    centuries: int
    half_centuries: int
    wickets_taken: int
    bowling_average: float
    economy_rate: float
    best_bowling: str

    class Config:
        from_attributes = True

class PlayerResponse(BaseModel):
    id: int
    name: str
    country: str
    date_of_birth: Optional[date] = None
    batting_style: Optional[str] = None
    bowling_style: Optional[str] = None
    image_url: Optional[str] = None
    stats: List[PlayerStatsResponse] = []

    class Config:
        from_attributes = True

class MatchResponse(BaseModel):
    id: int
    match_type: str
    team_home_id: int
    team_away_id: int
    status: str
    result: Optional[str] = None
    match_date: date
    venue: Optional[str] = None
    team_home: TeamResponse
    team_away: TeamResponse

    class Config:
        from_attributes = True
