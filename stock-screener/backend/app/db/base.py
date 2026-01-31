
# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.user import User  # noqa
from app.models.stock import Stock  # noqa
from app.models.fundamentals import Fundamentals  # noqa
from app.models.financials import Financials  # noqa
from app.models.portfolio import Portfolio  # noqa
from app.models.alert import Alert  # noqa
from app.models.screeener_run import UserQuery # noqa
