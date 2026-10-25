from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal

class CrowdReportLevel(str, Enum):
    serene = "serene"
    moderate = "moderate"
    bustling = "bustling"
    overcrowded = "overcrowded"

# Equidistant continuous mapping (Assumption to be calibrated against field observations)
CROWD_LEVEL_TO_DENSITY: Dict[CrowdReportLevel, int] = {
    CrowdReportLevel.serene: 20,
    CrowdReportLevel.moderate: 50,
    CrowdReportLevel.bustling: 75,
    CrowdReportLevel.overcrowded: 95
}

class CrowdReportRequest(BaseModel):
    place_id: str = Field(..., description="ID of place being reported")
    city_id: str = Field("pondicherry", description="City identifier (pondicherry, chennai)")
    crowd_level: CrowdReportLevel = Field(..., description="Observed crowd category (serene, moderate, bustling, overcrowded)")
    user_lat: float = Field(..., ge=-90.0, le=90.0, description="Reporting user GPS latitude")
    user_lng: float = Field(..., ge=-180.0, le=180.0, description="Reporting user GPS longitude")

class CrowdReportResponse(BaseModel):
    message: str
    place_id: str
    reported_density_pct: int
    blended_density_pct: int
    crowd_level: str
    active_reports_count: int
    is_surge: bool = False
    anomaly_alert: Optional[str] = None

class LiveCrowdResponse(BaseModel):
    place_id: str
    place_name: str
    city_id: str
    rule_baseline_density_pct: int
    blended_density_pct: int
    crowd_level: str
    status_badge: str
    active_reports_count: int
    is_surge: bool = False
    anomaly_alert: Optional[str] = None
    last_reported_time: Optional[str] = None
    confidence_badge: str = "Rule Baseline"
    confidence_level: Literal["HIGH", "MEDIUM", "LOW"] = "LOW"
