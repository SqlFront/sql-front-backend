from datetime import date, datetime
from decimal import Decimal

from asyncpg.exceptions import QueryCanceledError
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import StatementError
from sqlalchemy.ext.asyncio import create_async_engine
import sqlglot
import sqlglot.expressions as exp

from config import settings


class SQLExecutor:
    def __init__(self, db_url: str = settings.GAME_DATABASE_URL):
        self.engine = create_async_engine(db_url, isolation_level="AUTOCOMMIT")
        self.transaction_engine = create_async_engine(db_url) # For simulating updates

    async def execute_sql(self, sql_query: str, allow_star: bool = False) -> dict:
        sql_query = sql_query.rstrip(";").strip()
        self._validate_sql(sql_query, allow_star=allow_star)
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SET statement_timeout TO 5000"))
                result = await conn.execute(text(sql_query))
                if result.returns_rows:
                    columns = list(result.keys())
                    data = []
                    for row in result.fetchall():
                        processed_row = []
                        for value in row:
                            if isinstance(value, (date, datetime)):
                                processed_row.append(value.isoformat())
                            elif isinstance(value, Decimal):
                                processed_row.append(float(value))
                            else:
                                processed_row.append(value)
                        data.append(processed_row)
                    return {"columns": columns, "data": data, "row_count": len(data)}
                return {"columns": [], "data": [], "row_count": result.rowcount}
        except QueryCanceledError:
            raise HTTPException(
                status_code=400, detail="Время выполнения запроса превышено"
            )
        except StatementError as e:
            raise HTTPException(
                status_code=400, detail=f"Ошибка выполнения: {str(e.orig)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Непредвиденная ошибка базы данных: {str(e)}"
            )

    async def simulate_update(self, sql_query: str, allowed_tables: list[str] = None) -> int:
        """Безопасное выполнение UPDATE с помощью транзакции и отката"""
        sql_query = sql_query.rstrip(";").strip()
        self._validate_sql(sql_query, allow_update=True, allowed_tables=allowed_tables)
        try:
            async with self.transaction_engine.begin() as conn:
                await conn.execute(text("SET statement_timeout TO 5000"))
                result = await conn.execute(text(sql_query))
                rowcount = result.rowcount
                await conn.rollback()
                return rowcount
        except QueryCanceledError:
            raise HTTPException(
                status_code=400, detail="Время выполнения запроса превышено"
            )
        except StatementError as e:
            raise HTTPException(
                status_code=400, detail=f"Ошибка выполнения: {str(e.orig)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Непредвиденная ошибка базы данных: {str(e)}"
            )

    async def simulate_ddl(
        self,
        ddl_query: str,
        test_query: str | list[str],
        expect_error: bool = False,
    ) -> dict:
        """Безопасное выполнение DDL (функции/процедуры/триггеры) и тестового запроса в изолированной транзакции с ROLLBACK"""
        ddl_query = ddl_query.rstrip(";").strip()
        self._validate_sql(ddl_query, allow_ddl=True)

        if isinstance(test_query, str):
            test_statements = [s.strip() for s in test_query.split(";") if s.strip()]
        else:
            test_statements = [s.strip() for s in test_query if s.strip()]

        try:
            async with self.transaction_engine.begin() as conn:
                await conn.execute(text("SET statement_timeout TO 5000"))
                await conn.execute(text(ddl_query))

                last_result = None
                for stmt in test_statements:
                    last_result = await conn.execute(text(stmt))

                if expect_error:
                    await conn.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail="Ожидалась ошибка валидации (RAISE EXCEPTION), но запрос выполнился без ошибок",
                    )

                if last_result and last_result.returns_rows:
                    columns = list(last_result.keys())
                    data = []
                    for row in last_result.fetchall():
                        processed_row = []
                        for value in row:
                            if isinstance(value, (date, datetime)):
                                processed_row.append(value.isoformat())
                            elif isinstance(value, Decimal):
                                processed_row.append(float(value))
                            else:
                                processed_row.append(value)
                        data.append(processed_row)
                    res = {"columns": columns, "data": data, "row_count": len(data)}
                elif last_result:
                    res = {"columns": [], "data": [], "row_count": last_result.rowcount}
                else:
                    res = {"columns": [], "data": [], "row_count": 0}

                await conn.rollback()
                return res

        except QueryCanceledError:
            raise HTTPException(
                status_code=400, detail="Время выполнения запроса превышено"
            )
        except StatementError as e:
            if expect_error:
                return {
                    "columns": ["Результат"],
                    "data": [["Исключение успешно перехвачено: " + str(e.orig)]],
                    "row_count": 1,
                    "error_caught": True,
                }
            raise HTTPException(
                status_code=400, detail=f"Ошибка выполнения: {str(e.orig)}"
            )
        except HTTPException:
            raise
        except Exception as e:
            if expect_error:
                return {
                    "columns": ["Результат"],
                    "data": [["Исключение успешно перехвачено: " + str(e)]],
                    "row_count": 1,
                    "error_caught": True,
                }
            raise HTTPException(
                status_code=400, detail=f"Непредвиденная ошибка базы данных: {str(e)}"
            )

    def _validate_sql(
        self,
        sql_query: str,
        allow_update: bool = False,
        allowed_tables: list[str] = None,
        allow_star: bool = False,
        allow_ddl: bool = False,
    ):
        """AST и лексическая проверка SQL-запроса на безопасность"""
        import re

        if not sql_query or not sql_query.strip():
            raise HTTPException(status_code=400, detail="Пустой запрос")

        clean_query = sql_query.strip()

        # Check for forbidden system/admin operations
        forbidden_patterns = [
            r"\bdrop\s+(database|schema|role|user)\b",
            r"\balter\s+(system|database|role|user)\b",
            r"\bpg_shadow\b",
            r"\bpg_authid\b",
            r"\bpg_user\b",
            r"\binformation_schema\b",
            r"\bpassword_hashes\b",
            r"\buser_refresh_tokens\b",
        ]
        for pat in forbidden_patterns:
            if re.search(pat, clean_query, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail="Запрещенная операция или доступ к системной таблице",
                )

        forbidden_tables = {"users", "password_hashes", "user_refresh_tokens", "user_events"}
        for tbl in forbidden_tables:
            if re.search(r"\b" + tbl + r"\b", clean_query, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail=f"Доступ к системной или запрещенной таблице ({tbl}) запрещен",
                )

        if allow_ddl:
            ddl_match = re.match(
                r"^\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:FUNCTION|PROCEDURE|TRIGGER)\b",
                clean_query,
                re.IGNORECASE,
            )
            if ddl_match:
                return

        try:
            parsed = sqlglot.parse_one(clean_query, read="postgres")
        except sqlglot.errors.ParseError as e:
            raise HTTPException(status_code=400, detail=f"Ошибка синтаксиса: {str(e)}")

        if not parsed:
            raise HTTPException(status_code=400, detail="Пустой запрос")

        allowed_keys = ["select", "with", "except", "union", "intersect"]
        if allow_update:
            allowed_keys.append("update")

        if parsed.key not in allowed_keys:
            raise HTTPException(status_code=400, detail=f"Запрещенная операция: {parsed.key.upper()}")

        if not allow_star:
            for node in parsed.find_all(exp.Star):
                if not isinstance(node.parent, exp.Count):
                    raise HTTPException(status_code=400, detail="Использование SELECT * запрещено при финальной отправке, перечислите столбцы явно")

        for table in parsed.find_all(exp.Table):
            table_name = table.name.lower()
            if table_name.startswith("pg_") or table_name in ("user", "users") or table_name.startswith("information_schema"):
                raise HTTPException(status_code=400, detail=f"Доступ к системной или запрещенной таблице ({table.name}) запрещен")

            if allow_update and allowed_tables and parsed.key == "update":
                if table_name not in [t.lower() for t in allowed_tables]:
                    raise HTTPException(status_code=400, detail=f"Обновление таблицы {table.name} не разрешено в этой задаче")
