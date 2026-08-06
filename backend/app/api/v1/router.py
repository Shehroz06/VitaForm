from fastapi import APIRouter

from app.api.v1 import health
from features.achievements.router import router as achievements_router
from features.auth.router import router as auth_router
from features.awards.router import router as awards_router
from features.certifications.router import router as certifications_router
from features.competitions.router import router as competitions_router
from features.education.router import router as education_router
from features.experience.router import router as experience_router
from features.files.router import router as files_router
from features.hackathons.router import router as hackathons_router
from features.jobs.router import router as jobs_router
from features.languages.router import router as languages_router
from features.leadership_roles.router import router as leadership_roles_router
from features.organizations.router import router as organizations_router
from features.patents.router import router as patents_router
from features.profiles.router import router as profiles_router
from features.projects.router import router as projects_router
from features.references.router import router as references_router
from features.research.router import router as research_router
from features.resumes.router import router as resumes_router
from features.skills.router import router as skills_router
from features.volunteer_experience.router import router as volunteer_experience_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(profiles_router)
api_v1_router.include_router(education_router)
api_v1_router.include_router(experience_router)
api_v1_router.include_router(projects_router)
api_v1_router.include_router(skills_router)
api_v1_router.include_router(files_router)
api_v1_router.include_router(resumes_router)
api_v1_router.include_router(achievements_router)
api_v1_router.include_router(certifications_router)
api_v1_router.include_router(awards_router)
api_v1_router.include_router(research_router)
api_v1_router.include_router(volunteer_experience_router)
api_v1_router.include_router(leadership_roles_router)
api_v1_router.include_router(organizations_router)
api_v1_router.include_router(languages_router)
api_v1_router.include_router(references_router)
api_v1_router.include_router(hackathons_router)
api_v1_router.include_router(competitions_router)
api_v1_router.include_router(patents_router)
api_v1_router.include_router(jobs_router)
