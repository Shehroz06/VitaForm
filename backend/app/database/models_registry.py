"""Importing this module registers every feature's models on Base.metadata.

Required by Alembic autogenerate and by test fixtures that call
Base.metadata.create_all/drop_all. Add new feature model modules here as
they're built.
"""

from features.achievements import models as achievements_models  # noqa: F401
from features.ai import models as ai_models  # noqa: F401
from features.audit_log import models as audit_log_models  # noqa: F401
from features.auth import models as auth_models  # noqa: F401
from features.awards import models as awards_models  # noqa: F401
from features.certifications import models as certifications_models  # noqa: F401
from features.companion import models as companion_models  # noqa: F401
from features.competitions import models as competitions_models  # noqa: F401
from features.cv_import import models as cv_import_models  # noqa: F401
from features.education import models as education_models  # noqa: F401
from features.experience import models as experience_models  # noqa: F401
from features.files import models as files_models  # noqa: F401
from features.hackathons import models as hackathons_models  # noqa: F401
from features.interests import models as interests_models  # noqa: F401
from features.jobs import models as jobs_models  # noqa: F401
from features.languages import models as languages_models  # noqa: F401
from features.leadership_roles import models as leadership_roles_models  # noqa: F401
from features.organizations import models as organizations_models  # noqa: F401
from features.patents import models as patents_models  # noqa: F401
from features.portfolio import models as portfolio_models  # noqa: F401
from features.profiles import models as profiles_models  # noqa: F401
from features.projects import models as projects_models  # noqa: F401
from features.references import models as references_models  # noqa: F401
from features.research import models as research_models  # noqa: F401
from features.resumes import models as resumes_models  # noqa: F401
from features.skills import models as skills_models  # noqa: F401
from features.volunteer_experience import models as volunteer_experience_models  # noqa: F401
