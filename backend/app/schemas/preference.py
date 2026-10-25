from pydantic import BaseModel
from typing import Optional, List
from .place import AgeGroupEnum, DietaryOptionEnum, BudgetTierEnum

class UserPreferences(BaseModel):
    user_id: Optional[str] = "guest-user"
    age_group: AgeGroupEnum = AgeGroupEnum.YOUNG_ADULT
    dietary_preference: DietaryOptionEnum = DietaryOptionEnum.ALL
    budget_tier: BudgetTierEnum = BudgetTierEnum.MODERATE
    interests: List[str] = ["heritage", "beach", "cafe"]
    pace_preference: str = "balanced"  # relaxed, balanced, fast-paced
    accessibility_needed: bool = False

class UserProfile(BaseModel):
    id: str
    name: str = "Traveler"
    email: Optional[str] = None
    preferences: UserPreferences = UserPreferences()
