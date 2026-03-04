from app.core.config import get_settings
from app.core.database import (
    Base, get_db, init_db, check_db_connection,
    get_dialect, get_capabilities, DatabaseDialect, DialectCapabilities,
)
from app.core.types import GUID, ArrayField, JSONField, LargeText
from app.core.query_helpers import (
    case_insensitive_like, case_insensitive_equals,
    array_contains, array_overlap, array_length,
    json_extract_text, json_contains_key,
    build_raw_paginated_query, compute_batch_size,
    string_concat, current_timestamp_func, date_diff_days,
)
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    get_current_user, require_roles,
)

__all__ = [
    # Config
    "get_settings",
    # Database
    "Base", "get_db", "init_db", "check_db_connection",
    "get_dialect", "get_capabilities", "DatabaseDialect", "DialectCapabilities",
    # Types portables
    "GUID", "ArrayField", "JSONField", "LargeText",
    # Query helpers
    "case_insensitive_like", "case_insensitive_equals",
    "array_contains", "array_overlap", "array_length",
    "json_extract_text", "json_contains_key",
    "build_raw_paginated_query", "compute_batch_size",
    "string_concat", "current_timestamp_func", "date_diff_days",
    # Security
    "hash_password", "verify_password",
    "create_access_token", "create_refresh_token",
    "get_current_user", "require_roles",
]
