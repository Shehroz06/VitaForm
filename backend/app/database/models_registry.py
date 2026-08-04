"""Importing this module registers every feature's models on Base.metadata.

Required by Alembic autogenerate and by test fixtures that call
Base.metadata.create_all/drop_all. Add new feature model modules here as
they're built.
"""

from features.auth import models as auth_models  # noqa: F401
from features.education import models as education_models  # noqa: F401
from features.experience import models as experience_models  # noqa: F401
from features.profiles import models as profiles_models  # noqa: F401
from features.projects import models as projects_models  # noqa: F401
from features.skills import models as skills_models  # noqa: F401
