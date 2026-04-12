"""
OS HubLine — Helpers de requêtes portables multi-moteur

Fournit des fonctions qui génèrent le SQL correct selon le dialecte :
  - case_insensitive_like() : ILIKE (PG) vs LOWER(col) LIKE LOWER(val) (autres)
  - array_contains()        : col @> ARRAY[val] (PG) vs JSON_CONTAINS/LIKE (autres)
  - array_overlap()         : col && ARRAY[vals] (PG) vs multi-LIKE/JSON (autres)
  - json_extract()          : col->>'key' (PG) vs JSON_VALUE (SQL Server) vs json_extract (SQLite/MySQL)
  - paginate()              : LIMIT/OFFSET vs OFFSET FETCH vs subquery
  - bulk_insert_batched()   : respecte la limite de paramètres par moteur
"""
import json
from typing import Any, Optional
from sqlalchemy import or_, and_, func, literal_column, case, cast, String, text
from sqlalchemy.sql import ClauseElement
from sqlalchemy.orm import Query
from app.core.database import get_dialect, get_capabilities, DatabaseDialect


# ══════════════════════════════════════════════════════════
# CASE-INSENSITIVE SEARCH
# ══════════════════════════════════════════════════════════

def case_insensitive_like(column, value: str) -> ClauseElement:
    """
    Recherche case-insensitive portable.

    PostgreSQL  : column ILIKE '%value%'
    SQL Server  : column LIKE '%value%' (case-insensitive par défaut avec collation CI)
    MySQL       : column LIKE '%value%' (case-insensitive par défaut)
    SQLite      : LOWER(column) LIKE LOWER('%value%')
    Oracle      : UPPER(column) LIKE UPPER('%value%')
    """
    dialect = get_dialect()
    pattern = f"%{value}%"

    if dialect == DatabaseDialect.POSTGRESQL:
        return column.ilike(pattern)
    elif dialect in (DatabaseDialect.SQLSERVER, DatabaseDialect.MYSQL, DatabaseDialect.MARIADB):
        # SQL Server et MySQL sont case-insensitive par défaut avec la plupart des collations
        return column.like(pattern)
    elif dialect == DatabaseDialect.SQLITE:
        return func.lower(column).like(func.lower(pattern))
    elif dialect == DatabaseDialect.ORACLE:
        return func.upper(column).like(func.upper(pattern))
    else:
        return func.lower(column).like(func.lower(pattern))


def case_insensitive_equals(column, value: str) -> ClauseElement:
    """Égalité case-insensitive portable."""
    dialect = get_dialect()

    if dialect in (DatabaseDialect.SQLSERVER, DatabaseDialect.MYSQL, DatabaseDialect.MARIADB):
        return column == value
    else:
        return func.lower(column) == value.lower()


# ══════════════════════════════════════════════════════════
# ARRAY OPERATIONS
# ══════════════════════════════════════════════════════════

def array_contains(column, value: str) -> ClauseElement:
    """
    Vérifie si un array contient une valeur spécifique.

    PostgreSQL  : column @> ARRAY['value']
    SQL Server  : column LIKE '%"value"%'  (JSON sérialisé dans NVARCHAR)
    MySQL       : JSON_CONTAINS(column, '"value"')
    SQLite      : column LIKE '%"value"%'  (JSON sérialisé dans TEXT)
    """
    dialect = get_dialect()

    if dialect == DatabaseDialect.POSTGRESQL:
        # ARRAY natif : utiliser l'opérateur @> (contains)
        from sqlalchemy.dialects.postgresql import array
        return column.contains([value])
    elif dialect in (DatabaseDialect.MYSQL, DatabaseDialect.MARIADB):
        return func.json_contains(column, json.dumps(value))
    else:
        # SQL Server, SQLite, Oracle : LIKE sur JSON sérialisé
        # ["tag1","tag2"] → recherche "value" dedans
        escaped = value.replace('"', '\\"')
        return column.like(f'%"{escaped}"%')


def array_overlap(column, values: list[str]) -> ClauseElement:
    """
    Vérifie si un array a au moins une valeur en commun (OR).

    PostgreSQL  : column && ARRAY['a','b']
    Autres      : column LIKE '%"a"%' OR column LIKE '%"b"%'
    """
    dialect = get_dialect()

    if dialect == DatabaseDialect.POSTGRESQL:
        from sqlalchemy.dialects.postgresql import array
        return column.overlap(values)
    elif dialect in (DatabaseDialect.MYSQL, DatabaseDialect.MARIADB):
        conditions = [func.json_contains(column, json.dumps(v)) for v in values]
        return or_(*conditions)
    else:
        conditions = [column.like(f'%"{v}"%') for v in values]
        return or_(*conditions)


def array_length(column) -> ClauseElement:
    """Longueur d'un array stocké."""
    dialect = get_dialect()

    if dialect == DatabaseDialect.POSTGRESQL:
        return func.array_length(column, 1)
    elif dialect in (DatabaseDialect.MYSQL, DatabaseDialect.MARIADB):
        return func.json_length(column)
    else:
        # Approximation pour SQLite/SQL Server : compter les virgules + 1
        # ou json_array_length pour SQLite
        if dialect == DatabaseDialect.SQLITE:
            return func.json_array_length(column)
        return literal_column("0")  # fallback


# ══════════════════════════════════════════════════════════
# JSON OPERATIONS
# ══════════════════════════════════════════════════════════

def json_extract_text(column, key: str) -> ClauseElement:
    """
    Extraire une valeur texte d'un champ JSON.

    PostgreSQL  : column->>'key'
    SQL Server  : JSON_VALUE(column, '$.key')
    MySQL       : JSON_UNQUOTE(JSON_EXTRACT(column, '$.key'))
    SQLite      : json_extract(column, '$.key')
    Oracle      : JSON_VALUE(column, '$.key')
    """
    dialect = get_dialect()

    if dialect == DatabaseDialect.POSTGRESQL:
        return column[key].astext
    elif dialect == DatabaseDialect.SQLSERVER:
        return func.json_value(column, f"$.{key}")
    elif dialect in (DatabaseDialect.MYSQL, DatabaseDialect.MARIADB):
        return func.json_unquote(func.json_extract(column, f"$.{key}"))
    elif dialect == DatabaseDialect.SQLITE:
        return func.json_extract(column, f"$.{key}")
    elif dialect == DatabaseDialect.ORACLE:
        return func.json_value(column, f"$.{key}")
    else:
        return func.json_extract(column, f"$.{key}")


def json_contains_key(column, key: str) -> ClauseElement:
    """Vérifie si un objet JSON contient une clé."""
    dialect = get_dialect()

    if dialect == DatabaseDialect.POSTGRESQL:
        return column.has_key(key)
    elif dialect == DatabaseDialect.SQLSERVER:
        return func.json_value(column, f"$.{key}").isnot(None)
    elif dialect in (DatabaseDialect.MYSQL, DatabaseDialect.MARIADB):
        return func.json_contains_path(column, "one", f"$.{key}")
    else:
        return func.json_extract(column, f"$.{key}").isnot(None)


# ══════════════════════════════════════════════════════════
# PAGINATION HELPERS
# ══════════════════════════════════════════════════════════

def build_raw_paginated_query(
    base_sql: str,
    page: int,
    page_size: int,
    order_by: str = "created_at DESC",
) -> str:
    """
    Construit une requête paginée en raw SQL selon le dialecte.
    Pour les cas où SQLAlchemy ORM n'est pas utilisé (requêtes complexes).

    Note : Préférer .limit().offset() de SQLAlchemy ORM qui traduit automatiquement.
    Ce helper est pour le raw SQL uniquement.
    """
    dialect = get_dialect()
    offset = (page - 1) * page_size

    if dialect == DatabaseDialect.SQLSERVER:
        # SQL Server 2012+ : ORDER BY obligatoire avant OFFSET/FETCH
        return (
            f"{base_sql} "
            f"ORDER BY {order_by} "
            f"OFFSET {offset} ROWS "
            f"FETCH NEXT {page_size} ROWS ONLY"
        )
    elif dialect == DatabaseDialect.ORACLE:
        # Oracle 12c+ supporte OFFSET/FETCH, sinon ROWNUM
        return (
            f"{base_sql} "
            f"ORDER BY {order_by} "
            f"OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY"
        )
    else:
        # PostgreSQL, MySQL, SQLite
        return (
            f"{base_sql} "
            f"ORDER BY {order_by} "
            f"LIMIT {page_size} OFFSET {offset}"
        )


# ══════════════════════════════════════════════════════════
# BULK INSERT HELPER
# ══════════════════════════════════════════════════════════

def compute_batch_size(columns_per_row: int) -> int:
    """
    Calcule la taille de batch optimale pour les INSERT en masse
    en respectant la limite de paramètres du moteur.

    SQL Server : max 2100 params → 2100 / nb_colonnes
    SQLite     : max 999 params  → 999 / nb_colonnes
    PG/MySQL   : plus souple, on chunk par 500 pour la mémoire
    """
    caps = get_capabilities()
    max_params = caps.max_parameters_per_query
    batch = max(1, max_params // max(columns_per_row, 1))
    # Plafonner pour ne pas exploser la mémoire
    return min(batch, 500)


# ══════════════════════════════════════════════════════════
# STRING / DATE HELPERS
# ══════════════════════════════════════════════════════════

def string_concat(*columns) -> ClauseElement:
    """Concaténation de colonnes portable."""
    dialect = get_dialect()

    if dialect in (DatabaseDialect.MYSQL, DatabaseDialect.MARIADB):
        return func.concat(*columns)
    elif dialect == DatabaseDialect.SQLSERVER:
        return func.concat(*columns)  # SQL Server 2012+ supporte CONCAT()
    else:
        # PostgreSQL, SQLite, Oracle : opérateur ||
        result = columns[0]
        for col in columns[1:]:
            result = result.concat(col)
        return result


def current_timestamp_func() -> ClauseElement:
    """Timestamp courant portable."""
    dialect = get_dialect()

    if dialect == DatabaseDialect.SQLSERVER:
        return func.getutcdate()
    elif dialect == DatabaseDialect.ORACLE:
        return func.sys_extract_utc(func.systimestamp())
    else:
        return func.now()


def date_diff_days(start_col, end_col) -> ClauseElement:
    """Différence en jours entre deux dates."""
    dialect = get_dialect()

    if dialect == DatabaseDialect.POSTGRESQL:
        return func.extract("epoch", end_col - start_col) / 86400
    elif dialect == DatabaseDialect.SQLSERVER:
        return func.datediff(literal_column("day"), start_col, end_col)
    elif dialect in (DatabaseDialect.MYSQL, DatabaseDialect.MARIADB):
        return func.datediff(end_col, start_col)
    elif dialect == DatabaseDialect.SQLITE:
        return func.julianday(end_col) - func.julianday(start_col)
    elif dialect == DatabaseDialect.ORACLE:
        return end_col - start_col  # Oracle retourne nativement en jours
    else:
        return func.datediff(end_col, start_col)
