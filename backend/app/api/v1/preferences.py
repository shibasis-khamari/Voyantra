from fastapi import APIRouter
from ...schemas.preference import UserPreferences, UserProfile

router = APIRouter(prefix="/preferences", tags=["User Preferences"])

# In-memory session preference store (can easily be synced with Supabase Auth / Postgres)
_CURRENT_PROFILE = UserProfile(
    id="usr-guest",
    name="Guest Explorer",
    preferences=UserPreferences()
)

@router.get("", response_model=UserProfile)
def get_preferences():
    return _CURRENT_PROFILE

@router.post("", response_model=UserProfile)
def update_preferences(preferences: UserPreferences):
    global _CURRENT_PROFILE
    _CURRENT_PROFILE.preferences = preferences
    return _CURRENT_PROFILE
