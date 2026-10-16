"""Database access. Both adapters expose the same methods, so service.py never knows which database runs.
get / list_page / create / update / remove / find_one / remove_where / clean / parse_id / ping / migrate / close"""
from .. import schema

if schema.SCHEMA["db"] == "mongodb":
    from .mongo import connect  # noqa: F401
else:
    from .sql import connect  # noqa: F401
