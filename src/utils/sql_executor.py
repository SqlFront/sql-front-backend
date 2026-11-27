from datetime import date, datetime
from decimal import Decimal

import asyncpg
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

    @staticmethod
    def _clean_query(query: str) -> str:
        if not query:
            return ""
        cleaned = query.strip()
        while cleaned and (
            cleaned.endswith(";")
            or cleaned.endswith(" ")
            or cleaned.endswith("\n")
            or cleaned.endswith("\r")
            or cleaned.endswith("\t")
        ):
            cleaned = cleaned.rstrip("; \n\r\t").strip()
        return cleaned

    @staticmethod
    def _extract_operation_type(sql: str) -> str:
        if not sql:
            return "DDL"
        clean = sql.strip().lstrip(";").strip()
        patterns = [
            (
                r"^\s*CREATE\s+OR\s+REPLACE\s+(TABLE|VIEW|INDEX|SCHEMA|ROLE|USER|TYPE|SEQUENCE|FUNCTION|PROCEDURE|TRIGGER)\b",
                r"CREATE OR REPLACE \1",
            ),
            (
                r"^\s*CREATE\s+(?:UNIQUE\s+)?(TABLE|VIEW|INDEX|SCHEMA|ROLE|USER|TYPE|SEQUENCE|FUNCTION|PROCEDURE|TRIGGER|DATABASE)\b",
                r"CREATE \1",
            ),
            (
                r"^\s*ALTER\s+(TABLE|DATABASE|SCHEMA|ROLE|USER|SEQUENCE|SYSTEM)\b",
                r"ALTER \1",
            ),
            (
                r"^\s*DROP\s+(TABLE|VIEW|INDEX|SCHEMA|ROLE|USER|SEQUENCE|DATABASE|TRIGGER|FUNCTION|PROCEDURE)\b",
                r"DROP \1",
            ),
            (r"^\s*GRANT\b", "GRANT"),
            (r"^\s*REVOKE\b", "REVOKE"),
            (r"^\s*COMMENT\b", "COMMENT"),
            (r"^\s*INSERT\b", "INSERT"),
        ]
        import re

        for pat, repl in patterns:
            m = re.match(pat, clean, re.IGNORECASE)
            if m:
                if "\\" in repl:
                    return re.sub(pat, repl, m.group(0), flags=re.IGNORECASE).strip().upper()
                return repl.upper()
        words = clean.split()
        if len(words) >= 2 and words[0].upper() in ("CREATE", "ALTER", "DROP"):
            return f"{words[0].upper()} {words[1].upper()}"
        elif words:
            return words[0].upper()
        return "DDL"

    async def execute_sql(
        self,
        sql_query: str,
        allow_star: bool = False,
        allow_ddl_simulation: bool = False,
    ) -> dict:
        sql_query = self._clean_query(sql_query)
        self._validate_sql(
            sql_query, allow_star=allow_star, allow_ddl=allow_ddl_simulation
        )
        if allow_ddl_simulation:
            try:
                async with self.transaction_engine.begin() as conn:
                    await conn.execute(text("SET statement_timeout TO 5000"))
                    raw_conn = await conn.get_raw_connection()
                    if hasattr(raw_conn, "driver_connection") and hasattr(raw_conn.driver_connection, "execute"):
                        await raw_conn.driver_connection.execute(sql_query)
                    else:
                        from src.utils.catalog_model import split_statements
                        for stmt in split_statements(sql_query):
                            if stmt.strip():
                                await conn.execute(text(stmt))
                    op_type = self._extract_operation_type(sql_query)
                    await conn.rollback()
                    return {
                        "columns": ["Статус операции"],
                        "data": [
                            [
                                f"Команда успешно выполнена: {op_type} (симуляция завершена успешно)"
                            ]
                        ],
                        "row_count": 1,
                    }
            except QueryCanceledError:
                raise HTTPException(
                    status_code=400, detail="Время выполнения запроса превышено"
                )
            except StatementError as e:
                raise HTTPException(
                    status_code=400, detail=f"Ошибка выполнения: {str(e.orig)}"
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Непредвиденная ошибка базы данных: {str(e)}",
                )
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

    async def simulate_update(
        self, sql_query: str, allowed_tables: list[str] = None
    ) -> dict:
        """Безопасное выполнение UPDATE в изолированной транзакции с ROLLBACK и возвратом количества измененных строк."""
        sql_query = self._clean_query(sql_query)
        self._validate_sql(sql_query, allow_update=True, allowed_tables=allowed_tables)
        try:
            from src.utils.catalog_model import split_statements

            statements = split_statements(sql_query)
            if not statements:
                statements = [sql_query]

            async with self.transaction_engine.begin() as conn:
                await conn.execute(text("SET statement_timeout TO 5000"))
                total_rowcount = 0
                for stmt in statements:
                    stmt_clean = self._clean_query(stmt)
                    if stmt_clean:
                        result = await conn.execute(text(stmt_clean))
                        if result.rowcount is not None and result.rowcount > 0:
                            total_rowcount += result.rowcount
                await conn.rollback()
                return {
                    "columns": ["Статус операции", "Затронуто строк"],
                    "data": [["Симуляция UPDATE успешно выполнена", total_rowcount]],
                    "row_count": 1,
                    "affected_rows": total_rowcount,
                }
        except QueryCanceledError:
            raise HTTPException(
                status_code=400, detail="Время выполнения запроса превышено"
            )
        except StatementError as e:
            raise HTTPException(
                status_code=400, detail=f"Ошибка выполнения: {str(e.orig)}"
            )
        except HTTPException:
            raise
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
        ddl_query = self._clean_query(ddl_query)
        self._validate_sql(ddl_query, allow_ddl=True)

        if isinstance(test_query, str):
            from src.utils.catalog_model import split_statements
            test_statements = split_statements(test_query)
        else:
            test_statements = [s.strip() for s in test_query if s.strip()]

        async with self.transaction_engine.begin() as conn:
            await conn.execute(text("SET statement_timeout TO 5000"))

            # Фаза 1: Компиляция DDL пользователя
            try:
                raw_conn = await conn.get_raw_connection()
                if hasattr(raw_conn, "driver_connection") and hasattr(raw_conn.driver_connection, "execute"):
                    await raw_conn.driver_connection.execute(ddl_query)
                else:
                    from src.utils.catalog_model import split_statements
                    for stmt in split_statements(ddl_query):
                        if stmt.strip():
                            await conn.execute(text(stmt))
            except Exception as e:
                await conn.rollback()
                orig = getattr(e, "orig", e)
                raise HTTPException(
                    status_code=400,
                    detail=f"Ошибка выполнения DDL: {orig}",
                )

            # Фаза 2: Выполнение проверочного скрипта (test_query)
            try:
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
                    op_type = self._extract_operation_type(ddl_query)
                    res = {
                        "columns": ["Статус операции"],
                        "data": [
                            [
                                f"Команда успешно выполнена: {op_type} (симуляция завершена успешно)"
                            ]
                        ],
                        "row_count": 1,
                    }

                await conn.rollback()
                return res

            except QueryCanceledError:
                raise HTTPException(
                    status_code=400, detail="Время выполнения запроса превышено"
                )
            except StatementError as e:
                orig = e.orig
                if expect_error:
                    is_raise_exception = (
                        isinstance(orig, asyncpg.exceptions.RaiseError)
                        or getattr(orig, "sqlstate", None) == "P0001"
                        or getattr(orig, "pgcode", None) == "P0001"
                        or isinstance(getattr(orig, "__cause__", None), asyncpg.exceptions.RaiseError)
                    )
                    if is_raise_exception:
                        await conn.rollback()
                        return {
                            "columns": ["Результат"],
                            "data": [["Исключение успешно перехвачено: " + str(orig)]],
                            "row_count": 1,
                            "error_caught": True,
                        }
                    await conn.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Ожидалась ошибка валидации триггера (RAISE EXCEPTION), но возникла другая ошибка: {orig}",
                    )
                raise HTTPException(
                    status_code=400, detail=f"Ошибка выполнения: {str(orig)}"
                )
            except HTTPException:
                raise
            except Exception as e:
                orig = getattr(e, "orig", e)
                if expect_error:
                    is_raise_exception = (
                        isinstance(orig, asyncpg.exceptions.RaiseError)
                        or getattr(orig, "sqlstate", None) == "P0001"
                        or getattr(orig, "pgcode", None) == "P0001"
                        or isinstance(getattr(orig, "__cause__", None), asyncpg.exceptions.RaiseError)
                    )
                    if is_raise_exception:
                        await conn.rollback()
                        return {
                            "columns": ["Результат"],
                            "data": [["Исключение успешно перехвачено: " + str(orig)]],
                            "row_count": 1,
                            "error_caught": True,
                        }
                    await conn.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Ожидалась ошибка валидации триггера (RAISE EXCEPTION), но возникла другая ошибка: {orig}",
                    )
                raise HTTPException(
                    status_code=400, detail=f"Непредвиденная ошибка базы данных: {str(orig)}"
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
            r"\bdrop\s+database\b",
            r"\balter\s+system\b",
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
                r"^\s*(?:CREATE|ALTER|DROP|GRANT|REVOKE|COMMENT)\b",
                clean_query,
                re.IGNORECASE,
            )
            if ddl_match:
                return

        try:
            statements = [
                s for s in sqlglot.parse(clean_query, read="postgres") if s is not None
            ]
        except sqlglot.errors.ParseError as e:
            raise HTTPException(status_code=400, detail=f"Ошибка синтаксиса: {str(e)}")

        if not statements:
            raise HTTPException(status_code=400, detail="Пустой запрос")

        allowed_keys = ["select", "with", "except", "union", "intersect"]
        if allow_update:
            allowed_keys.append("update")

        for parsed in statements:
            if parsed.key not in allowed_keys:
                raise HTTPException(
                    status_code=400, detail=f"Запрещенная операция: {parsed.key.upper()}"
                )

            forbidden_ast_nodes = [exp.Delete, exp.Insert, exp.Drop]
            if not allow_update:
                forbidden_ast_nodes.append(exp.Update)

            for forbidden_node in forbidden_ast_nodes:
                if list(parsed.find_all(forbidden_node)):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Запрещенная модифицирующая операция ({forbidden_node.__name__.upper()}) в запросе",
                    )

            for func in parsed.find_all(exp.Anonymous, exp.Func):
                func_name = (
                    func.name
                    if isinstance(func, exp.Anonymous)
                    else (func.sql_name() if hasattr(func, "sql_name") else func.key)
                )
                func_name = (func_name or "").lower()
                if func_name.startswith("pg_") or func_name in ("current_setting", "query_to_xml", "dblink"):
                    if func_name not in ("pg_sleep",):
                        raise HTTPException(
                            status_code=400,
                            detail=f"Вызов системной функции ({func_name}) запрещен",
                        )

            if not allow_star:
                for node in parsed.find_all(exp.Star):
                    if not isinstance(node.parent, exp.Count):
                        raise HTTPException(
                            status_code=400,
                            detail="Использование SELECT * запрещено при финальной отправке, перечислите столбцы явно",
                        )

            for table in parsed.find_all(exp.Table):
                table_name = table.name.lower()
                if (
                    table_name.startswith("pg_")
                    or table_name in ("user", "users")
                    or table_name.startswith("information_schema")
                ):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Доступ к системной или запрещенной таблице ({table.name}) запрещен",
                    )

                if allow_update and allowed_tables and parsed.key == "update":
                    if table_name not in [t.lower() for t in allowed_tables]:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Обновление таблицы {table.name} не разрешено в этой задаче",
                        )
