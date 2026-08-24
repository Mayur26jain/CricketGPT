from sqlalchemy import Column, String, Integer, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    short_name = Column(String(50), nullable=False)
    team_type = Column(String(50), default="National")  # National, Franchise
    logo_url = Column(String(555), nullable=True)

class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    batting_style = Column(String(100), nullable=True)
    bowling_style = Column(String(100), nullable=True)
    image_url = Column(String(555), nullable=True)

    stats = relationship("PlayerStats", back_populates="player", cascade="all, delete-orphan")

class PlayerStats(Base):
    __tablename__ = "player_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    format = Column(String(50), nullable=False)  # Test, ODI, T20I, IPL
    matches_played = Column(Integer, default=0)
    innings_batted = Column(Integer, default=0)
    runs_scored = Column(Integer, default=0)
    highest_score = Column(Integer, default=0)
    
    # Raw batting totals
    dismissals_total = Column(Integer, default=0)
    balls_faced_total = Column(Integer, default=0)
    
    # Derived batting statistics
    batting_average = Column(Float, default=0.0)
    strike_rate = Column(Float, default=0.0)
    
    centuries = Column(Integer, default=0)
    half_centuries = Column(Integer, default=0)
    wickets_taken = Column(Integer, default=0)
    
    # Raw bowling totals
    runs_conceded_total = Column(Integer, default=0)
    balls_bowled_total = Column(Integer, default=0)
    
    # Derived bowling statistics
    bowling_average = Column(Float, default=0.0)
    economy_rate = Column(Float, default=0.0)
    best_bowling = Column(String(50), default="0/0")

    player = relationship("Player", back_populates="stats")

class MatchupCache(Base):
    __tablename__ = "matchup_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    batsman_name = Column(String(255), nullable=False, index=True)
    bowler_name = Column(String(255), nullable=False, index=True)
    runs = Column(Integer, default=0)
    balls = Column(Integer, default=0)
    dismissals = Column(Integer, default=0)
    caught = Column(Integer, default=0)
    bowled = Column(Integer, default=0)
    lbw = Column(Integer, default=0)
    stumped = Column(Integer, default=0)
    fours = Column(Integer, default=0)
    sixes = Column(Integer, default=0)
    dots = Column(Integer, default=0)

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    match_type = Column(String(50), nullable=False)  # Test, ODI, T20
    team_home_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    team_away_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    status = Column(String(50), default="Upcoming")  # Upcoming, Live, Completed
    result = Column(String(255), nullable=True)
    match_date = Column(Date, nullable=False)
    venue = Column(String(255), nullable=True)

    team_home = relationship("Team", foreign_keys=[team_home_id])
    team_away = relationship("Team", foreign_keys=[team_away_id])

