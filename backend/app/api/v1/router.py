from fastapi import APIRouter
from .places import router as places_router
from .hotels import router as hotels_router
from .preferences import router as preferences_router
from .recommendations import router as recommendations_router
from .auth import router as auth_router
from .festivals import router as festivals_router
from .crowd import router as crowd_router
from .routes import router as routes_router
from .chat import router as chat_router

api_router = APIRouter()

api_router.include_router(chat_router)
api_router.include_router(places_router)
api_router.include_router(hotels_router)
api_router.include_router(preferences_router)
api_router.include_router(recommendations_router)
api_router.include_router(auth_router)
api_router.include_router(festivals_router)
api_router.include_router(crowd_router)
api_router.include_router(routes_router)
