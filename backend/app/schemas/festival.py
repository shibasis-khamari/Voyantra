from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Festival(BaseModel):
    id: str
    city_id: str
    name: str
    month_day_start: str
    month_day_end: str
    affected_areas: List[str] = Field(default_factory=list)
    affected_streets: List[str] = Field(default_factory=list)
    procession_routes: List[str] = Field(default_factory=list)
    closure_alerts: List[str] = Field(default_factory=list)
    advisory_level: str = "Moderate Crowd"
    description: str = ""

class FestivalCreate(BaseModel):
    id: Optional[str] = None
    city_id: str = "pondicherry"
    name: str
    month_day_start: str
    month_day_end: str
    affected_areas: List[str] = Field(default_factory=list)
    affected_streets: Optional[List[str]] = None
    procession_routes: Optional[List[str]] = None
    closure_alerts: Optional[List[str]] = None
    advisory_level: str = "Moderate Crowd"
    description: str = ""

class FestivalUpdate(BaseModel):
    name: Optional[str] = None
    city_id: Optional[str] = None
    month_day_start: Optional[str] = None
    month_day_end: Optional[str] = None
    affected_areas: Optional[List[str]] = None
    affected_streets: Optional[List[str]] = None
    procession_routes: Optional[List[str]] = None
    closure_alerts: Optional[List[str]] = None
    advisory_level: Optional[str] = None
    description: Optional[str] = None
