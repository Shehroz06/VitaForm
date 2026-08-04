from fastapi import APIRouter

from app.api.v1 import health
from features.auth.router import router as auth_router
from features.education.router import router as education_router
from features.experience.router import router as experience_router
from features.profiles.router import router as profiles_router
from features.projects.router import router as projects_router
from features.skills.router import router as skills_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(profiles_router)
api_v1_router.include_router(education_router)
api_v1_router.include_router(experience_router)
api_v1_router.include_router(projects_router)
api_v1_router.include_router(skills_router)
