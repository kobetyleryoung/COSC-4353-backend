from fastapi import APIRouter
from .routes import events, profile, volunteer_matching, volunteer_history, notifications

# create main v1 router
api_router = APIRouter(prefix="/v1")

# include individual routers
api_router.include_router(events.router)
api_router.include_router(profile.router)
api_router.include_router(volunteer_matching.router)
api_router.include_router(volunteer_history.router)
api_router.include_router(notifications.router)