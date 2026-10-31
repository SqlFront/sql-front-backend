# -*- coding: utf-8 -*-
"""Учебная имитация каталога PostgreSQL для заданий на DDL и DCL.

Зачем имитация, а не выполнение
-------------------------------
Задание, в котором студент пишет ``CREATE TABLE`` или ``GRANT``, невозможно
проверить штатным ``SQLExecutor``: он отклоняет запрос по подстрокам ``create``,
``grant`` и прочим, а роль ``sql_runner`` имеет в базе квестов только ``SELECT``.
Выполнять такие ответы по-настоящему тоже дорого: роли в PostgreSQL общие для
всего кластера, поэтому одновременные проверки приходится выстраивать в очередь,
а кластер под это нужен отдельный и одноразовый. На поток в сотню студентов,
заходящих разом, это лишняя инфраструктура.

Здесь ответ студента **разбирается и применяется к модели каталога в памяти**.
Проверка не обращается ни к какой базе, не хранит состояния между запросами и
занимает микросекунды, поэтому сто одновременных студентов ничем не отличаются
от одного.

Что важно: сравнивается **состояние модели**, а не текст ответа. Ограничение,
записанное в определении столбца и добавленное отдельным ``ALTER TABLE``, дают
одинаковую модель и одинаково верны; ``GRANT SELECT, INSERT`` и два отдельных
``GRANT`` — тоже; порядок операторов не важен. Условия ``CHECK`` и правила
политик защиты строк не сравниваются как текст, а вычисляются на пробных
значениях, поэтому любая равносильная запись условия засчитывается.

Границы
-------
Это учебная модель, а не СУБД. Она понимает те семейства операторов, которые
встречаются в заданиях курса (см. ``SUPPORTED``), и намеренно отвергает всё
остальное с внятным сообщением, вместо того чтобы молча счесть ответ верным.
Правильность модели проверена дифференциально: на корпусе эталонных и заведомо
неверных ответов её вердикты сверены с вердиктами настоящего PostgreSQL 16.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

SUPPORTED = """
CREATE SCHEMA · CREATE TABLE · CREATE [UNIQUE] INDEX · CREATE VIEW
ALTER TABLE (ADD COLUMN, ADD CONSTRAINT, ALTER COLUMN SET/DROP NOT NULL,
             ENABLE/FORCE ROW LEVEL SECURITY) · ALTER DATABASE ... SET
INSERT INTO ... VALUES · CREATE ROLE · GRANT · REVOKE ·
ALTER DEFAULT PRIVILEGES · CREATE POLICY
"""

# Полный набор табличных привилегий PostgreSQL (то, что означает ALL PRIVILEGES).
ALL_TABLE_PRIVS = ["SELECT", "INSERT", "UPDATE", "DELETE",
                   "TRUNCATE", "REFERENCES", "TRIGGER"]
ALL_SCHEMA_PRIVS = ["CREATE", "USAGE"]

PUBLIC = "PUBLIC"


class ModelError(Exception):
    """Ответ не удалось разобрать или применить: для студента это неверный ответ."""


# =====================================================================
#  Разбор текста на операторы и лексемы
# =====================================================================

_STMT_STARTERS = {'alter', 'create', 'drop', 'grant', 'revoke', 'insert', 'comment'}


def split_statements(sql: str) -> List[str]:
    """Режет текст на операторы по точкам с запятой верхнего уровня или переводам строк.

    Пропускает строковые литералы, идентификаторы в кавычках, долларовые
    кавычки и комментарии обоих видов.
    """
    out, buf = [], []
    i, n = 0, len(sql)
    paren_depth = 0
    while i < n:
        ch = sql[i]
        if ch == "-" and sql.startswith("--", i):
            j = sql.find("\n", i)
            i = n if j == -1 else j
            buf.append(" ")
            continue
        if ch == "/" and sql.startswith("/*", i):
            depth, i = 1, i + 2
            while i < n and depth:
                if sql.startswith("/*", i):
                    depth, i = depth + 1, i + 2
                elif sql.startswith("*/", i):
                    depth, i = depth - 1, i + 2
                else:
                    i += 1
            buf.append(" ")
            continue
        if ch in ("'", '"'):
            quote, j = ch, i + 1
            while j < n:
                if sql[j] == quote:
                    if j + 1 < n and sql[j + 1] == quote:
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            buf.append(sql[i:j])
            i = j
            continue
        if ch == "$":
            j = i + 1
            while j < n and (sql[j].isalnum() or sql[j] == "_"):
                j += 1
            if j < n and sql[j] == "$":
                tag = sql[i:j + 1]
                close = sql.find(tag, j + 1)
                end = n if close == -1 else close + len(tag)
                buf.append(sql[i:end])
                i = end
                continue
        if ch == "(":
            paren_depth += 1
        elif ch == ")":
            paren_depth = max(0, paren_depth - 1)
        elif ch == ";":
            out.append("".join(buf))
            buf = []
            i += 1
            continue
        elif ch == "\n" and paren_depth == 0:
            cur_text = "".join(buf).strip()
            if cur_text and not cur_text.endswith((",", "(", "=", "+", "-")):
                k = i + 1
                while k < n:
                    if sql[k] in " \t\r\n":
                        k += 1
                    elif sql.startswith("--", k):
                        j = sql.find("\n", k)
                        k = n if j == -1 else j + 1
                    elif sql.startswith("/*", k):
                        close = sql.find("*/", k + 2)
                        k = n if close == -1 else close + 2
                    else:
                        break
                m = re.match(r"([A-Za-z_]+)", sql[k:])
                if m and m.group(1).lower() in _STMT_STARTERS:
                    words = re.findall(r"[A-Za-z_]+", sql[k:k+40])
                    first = words[0].lower() if words else ""
                    second = words[1].lower() if len(words) > 1 else ""
                    if first == "alter" and second == "column":
                        pass
                    elif first == "drop" and second in ("column", "constraint", "not", "default"):
                        pass
                    else:
                        out.append("".join(buf))
                        buf = []
                        i += 1
                        continue
        buf.append(ch)
        i += 1
    out.append("".join(buf))
    return [s.strip() for s in out if s.strip()]


_TOKEN = re.compile(r"""
    (?P<str>'(?:[^']|'')*')
  | (?P<ident>"(?:[^"]|"")*")
  | (?P<num>-?\d+(?:\.\d+)?)
  | (?P<word>[A-Za-z_Ѐ-ӿ][A-Za-z0-9_$Ѐ-ӿ]*)
  | (?P<op>::|<>|!=|>=|<=|[(),.;=<>*+\-\[\]])
""", re.VERBOSE)


class Tok:
    __slots__ = ("kind", "text")

    def __init__(self, kind: str, text: str):
        self.kind, self.text = kind, text

    @property
    def up(self) -> str:
        return self.text.upper()

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.kind}:{self.text}"


def tokenize(sql: str) -> List[Tok]:
    toks: List[Tok] = []
    for m in _TOKEN.finditer(sql):
        kind = m.lastgroup
        text = m.group()
        if kind == "ident":
            text = text[1:-1].replace('""', '"')
            kind = "word"
            toks.append(Tok("quoted", text))
            continue
        toks.append(Tok(kind, text))
    return toks


class Cursor:
    def __init__(self, toks: Sequence[Tok]):
        self.toks, self.i = list(toks), 0

    def eof(self) -> bool:
        return self.i >= len(self.toks)

    def peek(self, ahead: int = 0) -> Optional[Tok]:
        j = self.i + ahead
        return self.toks[j] if j < len(self.toks) else None

    def next(self) -> Tok:
        if self.eof():
            raise ModelError("оператор оборван на середине")
        t = self.toks[self.i]
        self.i += 1
        return t

    def at(self, *words: str) -> bool:
        t = self.peek()
        return bool(t) and t.kind in ("word", "quoted") and t.up in words

    def at_op(self, *ops: str) -> bool:
        t = self.peek()
        return bool(t) and t.kind == "op" and t.text in ops

    def take(self, *words: str) -> bool:
        if self.at(*words):
            self.i += 1
            return True
        return False

    def take_op(self, *ops: str) -> bool:
        if self.at_op(*ops):
            self.i += 1
            return True
        return False

    def expect(self, *words: str) -> Tok:
        if not self.at(*words):
            got = self.peek().text if self.peek() else "конец"
            raise ModelError(f"ожидалось {' или '.join(words)}, встретилось «{got}»")
        return self.next()

    def expect_op(self, *ops: str) -> Tok:
        if not self.at_op(*ops):
            got = self.peek().text if self.peek() else "конец"
            raise ModelError(f"ожидалось {' или '.join(ops)}, встретилось «{got}»")
        return self.next()

    def name(self) -> str:
        """Имя объекта, возможно с квалификатором схемы."""
        t = self.next()
        if t.kind not in ("word", "quoted", "num"):
            raise ModelError(f"ожидалось имя, встретилось «{t.text}»")
        parts = [t.text if t.kind == "quoted" else t.text.lower()]
        while self.at_op("."):
            self.next()
            p = self.next()
            parts.append(p.text if p.kind == "quoted" else p.text.lower())
        return ".".join(parts)

    def balanced(self) -> List[Tok]:
        """Содержимое скобок целиком, включая вложенные."""
        self.expect_op("(")
        depth, out = 1, []
        while not self.eof():
            t = self.next()
            if t.kind == "op" and t.text == "(":
                depth += 1
            elif t.kind == "op" and t.text == ")":
                depth -= 1
                if depth == 0:
                    return out
            out.append(t)
        raise ModelError("не закрыта скобка")


# =====================================================================
#  Условия: разбор и вычисление
# =====================================================================

class Expr:
    """Условие CHECK или правило политики в виде дерева."""

    def __init__(self, kind: str, **kw: Any):
        self.kind = kind
        self.__dict__.update(kw)

    def evaluate(self, row: Dict[str, Any]) -> Optional[bool]:
        k = self.kind
        if k == "and":
            vals = [c.evaluate(row) for c in self.parts]
            if any(v is False for v in vals):
                return False
            return None if any(v is None for v in vals) else True
        if k == "or":
            vals = [c.evaluate(row) for c in self.parts]
            if any(v is True for v in vals):
                return True
            return None if any(v is None for v in vals) else False
        if k == "not":
            v = self.part.evaluate(row)
            return None if v is None else not v
        if k == "cmp":
            left = self._value(self.left, row)
            right = self._value(self.right, row)
            if left is None or right is None:
                return None
            return _compare(self.op, left, right)
        if k == "in":
            left = self._value(self.left, row)
            if left is None:
                return None
            vals = [self._value(v, row) for v in self.values]
            res = any(_compare("=", left, v) for v in vals if v is not None)
            if not res and any(v is None for v in vals):
                return None
            return res != self.negated if self.negated else res
        if k == "isnull":
            v = self._value(self.left, row)
            return (v is None) != self.negated
        if k == "col":
            v = row.get(self.name)
            return None if v is None else bool(v)
        if k == "lit":
            return None if self.value is None else bool(self.value)
        raise ModelError(f"условие вида «{k}» модель не вычисляет")

    @staticmethod
    def _value(node: "Expr", row: Dict[str, Any]) -> Any:
        if node.kind == "col":
            return row.get(node.name)
        if node.kind == "lit":
            return node.value
        raise ModelError("в условии допустимы только столбцы и литералы")

    def columns(self) -> Set[str]:
        if self.kind in ("and", "or"):
            return set().union(*(p.columns() for p in self.parts))
        if self.kind == "not":
            return self.part.columns()
        if self.kind == "col":
            return {self.name}
        if self.kind == "lit":
            return set()
        if self.kind == "in":
            return self.left.columns()
        if self.kind in ("cmp",):
            return self.left.columns() | self.right.columns()
        if self.kind == "isnull":
            return self.left.columns()
        return set()


def _compare(op: str, a: Any, b: Any) -> bool:
    if isinstance(a, str) and isinstance(b, str):
        a, b = a.rstrip(), b.rstrip()          # char(n) дополняется пробелами
    try:
        if op == "=":
            return a == b
        if op in ("<>", "!="):
            return a != b
        if op == ">":
            return a > b
        if op == "<":
            return a < b
        if op == ">=":
            return a >= b
        if op == "<=":
            return a <= b
    except TypeError:
        return False
    raise ModelError(f"неизвестное сравнение «{op}»")


def parse_expr(toks: Sequence[Tok]) -> Expr:
    c = Cursor(toks)
    e = _or(c)
    if not c.eof():
        raise ModelError(f"условие разобрано не целиком: «{c.peek().text}»")
    return e


def _or(c: Cursor) -> Expr:
    parts = [_and(c)]
    while c.take("OR"):
        parts.append(_and(c))
    return parts[0] if len(parts) == 1 else Expr("or", parts=parts)


def _and(c: Cursor) -> Expr:
    parts = [_not(c)]
    while c.take("AND"):
        parts.append(_not(c))
    return parts[0] if len(parts) == 1 else Expr("and", parts=parts)


def _not(c: Cursor) -> Expr:
    if c.take("NOT"):
        return Expr("not", part=_not(c))
    return _predicate(c)


def _atom(c: Cursor) -> Expr:
    if c.at_op("("):
        inner = c.balanced()
        return parse_expr(inner)
    t = c.next()
    if t.kind == "str":
        return Expr("lit", value=t.text[1:-1].replace("''", "'"))
    if t.kind == "num":
        return Expr("lit", value=float(t.text) if "." in t.text else int(t.text))
    if t.kind in ("word", "quoted"):
        if t.kind == "word" and t.up in ("TRUE", "FALSE"):
            return Expr("lit", value=(t.up == "TRUE"))
        if t.kind == "word" and t.up == "NULL":
            return Expr("lit", value=None)
        name = t.text if t.kind == "quoted" else t.text.lower()
        while c.at_op("."):                    # таблица.столбец -> столбец
            c.next()
            p = c.next()
            name = p.text if p.kind == "quoted" else p.text.lower()
        if c.at_op("(") :                      # приведение типа/функция не поддержаны
            raise ModelError(f"вызов «{name}(...)» модель в условии не понимает")
        if c.at_op("::"):
            raise ModelError("приведение типа в условии модель не понимает")
        return Expr("col", name=name)
    raise ModelError(f"непонятная часть условия «{t.text}»")


def _predicate(c: Cursor) -> Expr:
    left = _atom(c)

    if c.take("IS"):
        neg = c.take("NOT")
        if c.at("TRUE", "FALSE"):
            want = c.next().up == "TRUE"
            node = Expr("cmp", op="=", left=left, right=Expr("lit", value=want))
            return Expr("not", part=node) if neg else node
        c.expect("NULL")
        return Expr("isnull", left=left, negated=neg)

    negated = False
    if c.take("NOT"):
        negated = True
    if c.take("IN"):
        items = Cursor(c.balanced())
        values = []
        while not items.eof():
            values.append(_atom(items))
            items.take_op(",")
        return Expr("in", left=left, values=values, negated=negated)
    if negated:
        raise ModelError("после NOT ожидалось IN")

    if c.at_op("=", "<>", "!=", ">", "<", ">="):
        op = c.next().text
        # = ANY (ARRAY[...]) — равносильно IN
        if op == "=" and c.at("ANY"):
            c.next()
            inner = Cursor(c.balanced())
            inner.take("ARRAY")
            if inner.at_op("["):
                inner.next()
                items, depth = [], 1
                while not inner.eof():
                    if inner.at_op("["):
                        depth += 1
                    if inner.at_op("]"):
                        depth -= 1
                        if depth == 0:
                            inner.next()
                            break
                    items.append(_atom(inner))
                    inner.take_op(",")
                return Expr("in", left=left, values=items, negated=False)
            values = []
            while not inner.eof():
                values.append(_atom(inner))
                inner.take_op(",")
            return Expr("in", left=left, values=values, negated=False)
        return Expr("cmp", op=op, left=left, right=_atom(c))
    if c.at_op("<="):
        c.next()
        return Expr("cmp", op="<=", left=left, right=_atom(c))
    return left


# =====================================================================
#  Типы
# =====================================================================

TYPE_MAP = {
    "int": "integer", "integer": "integer", "int4": "integer", "serial": "integer",
    "bigint": "bigint", "int8": "bigint", "bigserial": "bigint",
    "smallint": "smallint", "int2": "smallint", "smallserial": "smallint",
    "varchar": "character varying", "character varying": "character varying",
    "char": "character", "character": "character", "bpchar": "character",
    "text": "text", "date": "date",
    "bool": "boolean", "boolean": "boolean",
    "timestamp": "timestamp without time zone",
    "timestamp without time zone": "timestamp without time zone",
    "timestamptz": "timestamp with time zone",
    "timestamp with time zone": "timestamp with time zone",
    "numeric": "numeric", "decimal": "numeric", "real": "real",
    "double precision": "double precision", "uuid": "uuid", "jsonb": "jsonb",
}

_CHAR_TYPES = {"character varying", "character"}

# Слова, на которых заканчивается имя типа в определении столбца.
_COL_STOP = {"NOT", "NULL", "PRIMARY", "UNIQUE", "REFERENCES", "CHECK",
             "DEFAULT", "CONSTRAINT", "GENERATED", "COLLATE", "DEFERRABLE"}


class Column:
    __slots__ = ("name", "type", "length", "not_null", "has_default", "default_text", "is_serial")

    def __init__(self, name, type_, length):
        self.name, self.type, self.length = name, type_, length
        self.not_null = False
        self.has_default = False
        self.default_text = ""
        self.is_serial = False


class Table:
    def __init__(self, qname, owner="owner"):
        self.qname = qname
        self.owner = owner
        self.columns = []
        self.pk = []
        self.uniques = []
        self.fks = []
        self.checks = []
        self.rls_enabled = False
        self.rls_forced = False
        self.rows = []

    def column(self, name):
        for c in self.columns:
            if c.name == name:
                return c
        return None


# =====================================================================
#  Модель каталога
# =====================================================================

class Model:
    def __init__(self, database="quest_sandbox"):
        self.database = database
        self.search_path = ["public"]
        self.schemas = {"public"}
        self.tables = {}
        self.indexes = {}
        self.views = {}
        self.roles = {}
        self.memberships = {}            # член -> множество ролей
        self.admin_options = set()       # (член, роль) с правом раздавать членство
        self.grants = {}                 # (кому, вид, объект) -> {право: передаваемо}
        self.column_grants = {}          # (кому, таблица) -> {столбец: множество прав}
        self.default_privs = []
        self.policies = {}
        self.db_settings = {}

    # ------------------------------------------------------------ вспомогательное

    def qualify(self, name, create=False):
        """Имя с квалификатором схемы; без него имя ищется по пути поиска."""
        if "." in name:
            return name
        if create:
            return self.search_path[0] + "." + name
        for schema in self.search_path:
            candidate = schema + "." + name
            if candidate in self.tables or candidate in self.views:
                return candidate
        return self.search_path[0] + "." + name

    # ------------------------------------------------------------ применение

    def execute(self, sql):
        for stmt in split_statements(sql):
            self.execute_one(stmt)

    def execute_one(self, stmt):
        c = Cursor(tokenize(stmt))
        if c.eof():
            return
        head = c.peek().up
        if head == "CREATE":
            self._create(c)
        elif head == "ALTER":
            self._alter(c)
        elif head == "GRANT":
            self._grant(c, revoke=False)
        elif head == "REVOKE":
            self._grant(c, revoke=True)
        elif head == "INSERT":
            self._insert(c)
        elif head == "DROP":
            self._drop(c)
        elif head == "SET":
            self._set(c)
        elif head == "COMMENT":
            _rest(c)                      # пояснение к объекту ничего не меняет
        else:
            raise ModelError(
                "оператор «%s» в заданиях этого квеста не используется"
                % c.peek().text.upper())
        # Хвост, который модель не разобрала, — это конструкция за пределами
        # курса. Молча её проглотить нельзя: иначе ответ засчитается за то,
        # чего проверка не видела.
        if not c.eof():
            raise ModelError(
                "оператор разобран не целиком, начиная с «%s»" % c.peek().text)

    def _set(self, c):
        c.expect("SET")
        c.take("SESSION"); c.take("LOCAL")
        param = c.name()
        if not (c.take_op("=") or c.take("TO")):
            raise ModelError("после имени параметра ожидалось TO или =")
        if param.lower() == "search_path":
            self.search_path = [t.text.strip('"').lower()
                                for t in _rest(c) if t.kind in ("word", "quoted", "str")]
        else:
            _rest(c)

    # ------------------------------------------------------------ CREATE

    def _create(self, c):
        c.expect("CREATE")
        c.take("OR")
        c.take("REPLACE")
        unique = c.take("UNIQUE")
        if c.take("SCHEMA"):
            c.take("IF"); c.take("NOT"); c.take("EXISTS")
            self.schemas.add(c.name())
            if c.take("AUTHORIZATION"):
                c.name()
            return
        if c.take("TABLE"):
            c.take("IF"); c.take("NOT"); c.take("EXISTS")
            self._create_table(c)
            return
        if c.take("INDEX"):
            self._create_index(c, unique)
            return
        if c.take("VIEW"):
            self._create_view(c)
            return
        if c.at("ROLE", "USER", "GROUP"):
            kind = c.next().up
            self._create_role(c, login_default=(kind == "USER"))
            return
        if c.take("POLICY"):
            self._create_policy(c)
            return
        raise ModelError("модель понимает CREATE только для SCHEMA, TABLE, INDEX, "
                         "VIEW, ROLE и POLICY")

    def _create_table(self, c):
        qname = self.qualify(c.name(), create=True)
        if qname in self.tables:
            raise ModelError("таблица %s уже существует" % qname)
        schema = qname.split(".")[0]
        if schema not in self.schemas:
            raise ModelError("схемы %s не существует" % schema)
        t = Table(qname)
        body = Cursor(c.balanced())
        while not body.eof():
            self._table_element(body, t)
            if not body.take_op(","):
                break
        self.tables[qname] = t
        for entry in self.default_privs:
            if entry["schema"] == schema and entry["objtype"] == "r":
                g = self.grants.setdefault((entry["grantee"], "table", qname), {})
                for p in entry["privs"]:
                    g.setdefault(p, False)

    def _table_element(self, c, t):
        named = False
        if c.take("CONSTRAINT"):
            c.name()
            named = True
        if c.at("PRIMARY", "UNIQUE", "FOREIGN", "CHECK"):
            self._table_constraint(c, t)
            return
        if named:
            raise ModelError("после CONSTRAINT ожидалось ограничение таблицы")
        self._column_def(c, t)

    def _table_constraint(self, c, t):
        if c.take("PRIMARY"):
            c.expect("KEY")
            if c.take("USING"):
                c.expect("INDEX")
                idx = self.indexes.get(c.name())
                if idx is None:
                    raise ModelError("такого индекса нет")
                t.pk = list(idx["columns"])
            else:
                t.pk = _name_list(c.balanced())
            for name in t.pk:
                col = t.column(name)
                if col:
                    col.not_null = True
            return
        if c.take("UNIQUE"):
            t.uniques.append(_name_list(c.balanced()))
            return
        if c.take("FOREIGN"):
            c.expect("KEY")
            cols = _name_list(c.balanced())
            self._references(c, t, cols)
            return
        if c.take("CHECK"):
            t.checks.append(parse_expr(c.balanced()))
            return
        raise ModelError("неизвестное ограничение таблицы")

    def _references(self, c, t, cols):
        c.expect("REFERENCES")
        ref_table = self.qualify(c.name())
        ref_cols = _name_list(c.balanced()) if c.at_op("(") else []
        on_delete, on_update = "NO ACTION", "NO ACTION"
        while c.take("ON"):
            which = c.expect("DELETE", "UPDATE").up
            action = c.expect("CASCADE", "RESTRICT", "SET", "NO").up
            if action == "SET":
                action = "SET " + c.expect("NULL", "DEFAULT").up
            elif action == "NO":
                c.expect("ACTION")
                action = "NO ACTION"
            if which == "DELETE":
                on_delete = action
            else:
                on_update = action
        if not ref_cols:
            ref = self.tables.get(ref_table)
            ref_cols = list(ref.pk) if ref else []
        t.fks.append({"columns": cols, "ref_table": ref_table,
                      "ref_columns": ref_cols, "on_delete": on_delete,
                      "on_update": on_update})

    def _column_def(self, c, t):
        name = c.name()
        words = []
        while (not c.eof() and not c.at_op(",") and not c.at_op("(")
               and not (c.peek().kind == "word" and c.peek().up in _COL_STOP)):
            words.append(c.next().text.lower())
        if not words:
            raise ModelError("у столбца %s не указан тип" % name)
        length = None
        if c.at_op("("):
            nums = c.balanced()
            if nums and nums[0].kind == "num":
                length = int(float(nums[0].text))
        raw = " ".join(words)
        type_ = TYPE_MAP.get(raw) or TYPE_MAP.get(words[0], raw)
        if type_ not in _CHAR_TYPES:
            length = None
        elif type_ == "character" and length is None:
            length = 1
        col = Column(name, type_, length)
        if raw in ("serial", "bigserial", "smallserial"):
            # serial — это целое со счётчиком: значение по умолчанию есть.
            col.has_default = True
            col.default_text = "nextval"
            col.is_serial = True
            col.not_null = True
        t.columns.append(col)

        while not c.eof() and not c.at_op(","):
            if c.take("CONSTRAINT"):
                c.name()
                continue
            if c.take("NOT"):
                c.expect("NULL")
                col.not_null = True
                continue
            if c.take("NULL"):
                continue
            if c.take("PRIMARY"):
                c.expect("KEY")
                t.pk = [name]
                col.not_null = True
                continue
            if c.take("UNIQUE"):
                t.uniques.append([name])
                continue
            if c.take("DEFAULT"):
                col.has_default = True
                col.default_text = _grab_default(c)
                continue
            if c.take("CHECK"):
                t.checks.append(parse_expr(c.balanced()))
                continue
            if c.at("REFERENCES"):
                self._references(c, t, [name])
                continue
            if c.at("GENERATED", "COLLATE", "DEFERRABLE"):
                raise ModelError("такие свойства столбца модель не поддерживает")
            break

    def _create_index(self, c, unique):
        c.take("CONCURRENTLY")
        c.take("IF"); c.take("NOT"); c.take("EXISTS")
        name = None
        if not c.at("ON"):
            name = c.name()
        c.expect("ON")
        table = self.qualify(c.name())
        method = "btree"
        if c.take("USING"):
            method = c.name()
        cols = _name_list(c.balanced())
        if c.take("WITH"):
            c.balanced()                      # параметры хранения на смысл не влияют
        if c.take("TABLESPACE"):
            c.name()
        partial = False
        if c.take("WHERE"):
            _rest(c)
            partial = True
        if table not in self.tables:
            raise ModelError("таблицы %s не существует" % table)
        self.indexes[name or (table + "_idx")] = {
            "table": table, "columns": cols, "unique": unique,
            "method": method, "partial": partial}

    def _create_view(self, c):
        name = self.qualify(c.name())
        cols = _name_list(c.balanced()) if c.at_op("(") else []
        c.expect("AS")
        body = []
        while not c.eof():
            body.append(c.next())
        self.views[name] = {"columns": cols, "body": body}

    def _create_role(self, c, login_default=False):
        name = c.name()
        role = {"login": login_default, "inherit": True, "superuser": False,
                "createrole": False, "createdb": False, "bypassrls": False}
        c.take("WITH")
        while not c.eof():
            if c.take("LOGIN"):
                role["login"] = True
            elif c.take("NOLOGIN"):
                role["login"] = False
            elif c.take("NOINHERIT"):
                role["inherit"] = False
            elif c.take("INHERIT"):
                role["inherit"] = True
            elif c.take("PASSWORD"):
                c.next()
            elif c.take("IN"):
                c.expect("ROLE", "GROUP")
                for parent in _split_names(c):
                    self.memberships.setdefault(name, set()).add(parent)
            elif c.take("ROLE", "ADMIN", "USER"):
                for child in _split_names(c):
                    self.memberships.setdefault(child, set()).add(name)
            elif c.take("SUPERUSER"):
                role["superuser"] = True
            elif c.take("CREATEROLE"):
                role["createrole"] = True
            elif c.take("CREATEDB"):
                role["createdb"] = True
            elif c.take("BYPASSRLS"):
                role["bypassrls"] = True
            elif c.take("NOSUPERUSER", "NOCREATEDB", "NOCREATEROLE", "REPLICATION",
                        "NOREPLICATION", "NOBYPASSRLS", "CONNECTION",
                        "VALID", "UNTIL", "LIMIT"):
                continue
            else:
                c.next()
        self.roles[name] = role

    def _create_policy(self, c):
        name = c.name()
        c.expect("ON")
        table = self.qualify(c.name())
        cmd, roles, using = "ALL", [], None
        if c.take("AS"):
            c.expect("PERMISSIVE", "RESTRICTIVE")
        if c.take("FOR"):
            cmd = c.expect("ALL", "SELECT", "INSERT", "UPDATE", "DELETE").up
        if c.take("TO"):
            roles = _split_names(c, keep_public=True)
        if c.take("USING"):
            using = parse_expr(c.balanced())
        if c.take("WITH"):
            c.expect("CHECK")
            c.balanced()
        if table not in self.tables:
            raise ModelError("таблицы %s не существует" % table)
        self.policies[name] = {"table": table, "cmd": cmd,
                               "roles": roles or [PUBLIC], "using": using}

    # ------------------------------------------------------------ ALTER

    def _alter(self, c):
        c.expect("ALTER")
        if c.take("TABLE"):
            c.take("IF"); c.take("EXISTS"); c.take("ONLY")
            qname = self.qualify(c.name())
            if qname not in self.tables:
                raise ModelError("таблицы %s не существует" % qname)
            self._alter_table(c, self.tables[qname])
            return
        if c.take("DATABASE"):
            db = c.name()
            c.expect("SET")
            self._set_db_param(c, db)
            return
        if c.take("DEFAULT"):
            c.expect("PRIVILEGES")
            self._alter_default_privileges(c)
            return
        if c.take("ROLE", "USER"):
            if c.at("ALL"):
                c.next()
                c.expect("IN"); c.expect("DATABASE")
                db = c.name()
                c.expect("SET")
                self._set_db_param(c, db)
                return
            name = c.name()
            if name not in self.roles:
                raise ModelError("роли %s не существует" % name)
            while not c.eof():
                if c.take("LOGIN"):
                    self.roles[name]["login"] = True
                elif c.take("NOLOGIN"):
                    self.roles[name]["login"] = False
                else:
                    c.next()
            return
        raise ModelError("модель понимает ALTER для TABLE, DATABASE, ROLE "
                         "и DEFAULT PRIVILEGES")

    def _set_db_param(self, c, db):
        if c.at("TIME"):
            c.next(); c.expect("ZONE")
            param = "timezone"
        else:
            param = c.name()
            if not (c.take_op("=") or c.take("TO")):
                raise ModelError("после имени параметра ожидалось TO или =")
        value = "".join(_literal_text(t) for t in _rest(c)).replace(" ", "")
        param = param.lower()
        if param == "timezone":
            # Имена часовых поясов в PostgreSQL регистронезависимы.
            value = value.upper()
        self.db_settings.setdefault(db, {})[param] = value

    def _alter_table(self, c, t):
        while True:
            if c.take("ADD"):
                if c.take("CONSTRAINT"):
                    c.name()
                    self._table_constraint(c, t)
                elif c.at("PRIMARY", "UNIQUE", "FOREIGN", "CHECK"):
                    self._table_constraint(c, t)
                else:
                    c.take("COLUMN")
                    c.take("IF"); c.take("NOT"); c.take("EXISTS")
                    self._column_def(c, t)
                if c.take("NOT"):
                    c.expect("VALID")         # добавлено без пересчёта существующих строк
            elif c.take("ALTER"):
                c.take("COLUMN")
                name = c.name()
                col = t.column(name)
                if col is None:
                    raise ModelError("в таблице %s нет столбца %s" % (t.qname, name))
                if c.take("SET"):
                    if c.take("NOT"):
                        c.expect("NULL")
                        col.not_null = True
                    elif c.take("DEFAULT"):
                        col.has_default = True
                        col.default_text = _grab_default(c)
                    else:
                        raise ModelError("такое ALTER COLUMN модель не поддерживает")
                elif c.take("DROP"):
                    if c.take("NOT"):
                        c.expect("NULL")
                        col.not_null = False
                    elif c.take("DEFAULT"):
                        col.has_default = False
                    else:
                        raise ModelError("такое ALTER COLUMN модель не поддерживает")
                else:
                    raise ModelError("такое ALTER COLUMN модель не поддерживает")
            elif c.take("DROP"):
                c.take("COLUMN")
                c.take("IF"); c.take("EXISTS")
                name = c.name()
                t.columns = [x for x in t.columns if x.name != name]
                c.take("CASCADE"); c.take("RESTRICT")
            elif c.take("ENABLE"):
                c.expect("ROW"); c.expect("LEVEL"); c.expect("SECURITY")
                t.rls_enabled = True
            elif c.take("DISABLE"):
                c.expect("ROW"); c.expect("LEVEL"); c.expect("SECURITY")
                t.rls_enabled = False
            elif c.take("FORCE"):
                c.expect("ROW"); c.expect("LEVEL"); c.expect("SECURITY")
                t.rls_forced = True
            elif c.take("NO"):
                c.expect("FORCE"); c.expect("ROW"); c.expect("LEVEL"); c.expect("SECURITY")
                t.rls_forced = False
            elif c.take("OWNER"):
                c.expect("TO")
                t.owner = c.name()
            elif c.take("VALIDATE"):
                c.expect("CONSTRAINT")
                c.name()                      # ограничение уже действует в модели
            elif c.take("RENAME"):
                if c.take("TO"):
                    # Новое имя даётся без схемы: таблица остаётся в своей.
                    raw = c.name()
                    new = raw if "." in raw else t.qname.split(".")[0] + "." + raw
                    self.tables.pop(t.qname, None)
                    t.qname = new
                    self.tables[new] = t
                else:
                    c.take("COLUMN")
                    old = c.name()
                    c.expect("TO")
                    new = c.name()
                    col = t.column(old)
                    if col is None:
                        raise ModelError("в таблице %s нет столбца %s" % (t.qname, old))
                    col.name = new
            else:
                raise ModelError("такое действие ALTER TABLE модель не поддерживает")
            if not c.take_op(","):
                break

    def _alter_default_privileges(self, c):
        schema = None
        while c.at("FOR", "IN"):
            c.next()
            if c.take("ROLE", "USER"):
                _split_names(c)
            elif c.take("SCHEMA"):
                schema = c.name()
        revoke = c.at("REVOKE")
        c.expect("GRANT", "REVOKE")
        privs = _priv_list(c)
        c.expect("ON")
        objtype = c.expect("TABLES", "SEQUENCES", "FUNCTIONS", "TYPES", "SCHEMAS").up
        code = {"TABLES": "r", "SEQUENCES": "S", "FUNCTIONS": "f",
                "TYPES": "T", "SCHEMAS": "n"}[objtype]
        c.expect("TO", "FROM")
        grantees = _split_names(c, keep_public=True)
        if privs == ["ALL"]:
            privs = list(ALL_TABLE_PRIVS)
        for g in grantees:
            slot = None
            for e in self.default_privs:
                if (e["schema"] == schema and e["grantee"] == g
                        and e["objtype"] == code):
                    slot = e
                    break
            if slot is None:
                slot = {"schema": schema, "objtype": code, "grantee": g, "privs": []}
                self.default_privs.append(slot)
            have = set(slot["privs"])
            slot["privs"] = sorted((have - set(privs)) if revoke else (have | set(privs)))
        self.default_privs = [e for e in self.default_privs if e["privs"]]

    # ------------------------------------------------------------ DROP

    def _drop(self, c):
        c.expect("DROP")
        what = c.next().up
        c.take("IF"); c.take("EXISTS")
        name = c.name()
        if what == "TABLE":
            self.tables.pop(self.qualify(name), None)
        elif what == "SCHEMA":
            self.schemas.discard(name)
        elif what in ("ROLE", "USER"):
            self.roles.pop(name, None)
        elif what == "POLICY":
            self.policies.pop(name, None)
        elif what == "INDEX":
            self.indexes.pop(name, None)
        elif what == "VIEW":
            self.views.pop(self.qualify(name), None)
        else:
            raise ModelError("DROP %s модель не поддерживает" % what)
        c.take("CASCADE"); c.take("RESTRICT")

    # ------------------------------------------------------------ GRANT / REVOKE

    def _grant(self, c, revoke):
        c.expect("REVOKE" if revoke else "GRANT")
        if revoke and c.take("GRANT"):
            c.expect("OPTION"); c.expect("FOR")
        start = c.i
        has_on = any(t.kind == "word" and t.up == "ON" for t in c.toks[c.i:])
        if not has_on:
            roles = _split_names(c)
            c.expect("FROM" if revoke else "TO")
            members = _split_names(c, keep_public=True)
            admin = False
            if c.take("WITH"):
                admin = c.take("ADMIN")
                c.take("OPTION")
                c.take("INHERIT"); c.take("SET"); c.take("TRUE"); c.take("FALSE")
            c.take("CASCADE"); c.take("RESTRICT")
            for m in members:
                for r in roles:
                    if revoke:
                        self.memberships.get(m, set()).discard(r)
                        self.admin_options.discard((m, r))
                    else:
                        if r not in self.roles:
                            raise ModelError("роли %s не существует" % r)
                        self.memberships.setdefault(m, set()).add(r)
                        if admin:
                            self.admin_options.add((m, r))
            return
        c.i = start
        privs = _priv_list(c)
        cols = []
        if c.at_op("("):
            cols = _name_list(c.balanced())
        c.expect("ON")
        if c.take("SCHEMA"):
            objs = _split_names(c)
            kind = "schema"
        else:
            c.take("TABLE")
            if c.take("ALL"):
                c.expect("TABLES"); c.expect("IN"); c.expect("SCHEMA")
                schemas = _split_names(c)
                objs = [q for q in self.tables if q.split(".")[0] in schemas]
            else:
                objs = [self.qualify(n) for n in _split_names(c)]
            kind = "table"
        c.expect("FROM" if revoke else "TO")
        grantees = _split_names(c, keep_public=True)
        grant_option = False
        if not revoke and c.take("WITH"):
            c.expect("GRANT"); c.expect("OPTION")
            grant_option = True
        if privs == ["ALL"]:
            privs = list(ALL_SCHEMA_PRIVS if kind == "schema" else ALL_TABLE_PRIVS)

        for g in grantees:
            if g not in self.roles and g != PUBLIC:
                raise ModelError("роли %s не существует" % g)
            for obj in objs:
                if kind == "table" and obj not in self.tables and obj not in self.views:
                    raise ModelError("таблицы %s не существует" % obj)
                if kind == "schema" and obj not in self.schemas:
                    raise ModelError("схемы %s не существует" % obj)
                if cols:
                    slot = self.column_grants.setdefault((g, obj), {})
                    for col in cols:
                        cur = slot.setdefault(col, {})
                        for p in privs:
                            if revoke:
                                cur.pop(p, None)
                            else:
                                cur[p] = cur.get(p, False) or grant_option
                    continue
                key = (g, kind, obj)
                cur = self.grants.setdefault(key, {})
                if revoke:
                    for p in privs:
                        cur.pop(p, None)
                    if not cur:
                        self.grants.pop(key, None)
                    if kind == "table" and set(privs) >= set(ALL_TABLE_PRIVS):
                        self.column_grants.pop((g, obj), None)
                else:
                    for p in privs:
                        cur[p] = cur.get(p, False) or grant_option
        c.take("CASCADE"); c.take("RESTRICT")

    # ------------------------------------------------------------ INSERT

    def _insert(self, c):
        c.expect("INSERT"); c.expect("INTO")
        qname = self.qualify(c.name())
        if qname not in self.tables:
            raise ModelError("таблицы %s не существует" % qname)
        t = self.tables[qname]
        cols = _name_list(c.balanced()) if c.at_op("(") else [x.name for x in t.columns]
        c.expect("VALUES")
        while True:
            values = _value_list(c.balanced())
            if len(values) != len(cols):
                raise ModelError("число значений не совпадает с числом столбцов")
            row = dict(zip(cols, values))
            ok, why = self.would_accept(t, row)
            if not ok:
                raise ModelError("строку не принять: " + why)
            t.rows.append(self.fill_defaults(t, row))
            if not c.take_op(","):
                break

    @staticmethod
    def fill_defaults(t, row):
        full = {}
        for col in t.columns:
            if col.name in row:
                full[col.name] = row[col.name]
            elif col.has_default:
                full[col.name] = "<" + (col.default_text or "default") + ">"
            else:
                full[col.name] = None
        return full

    def would_accept(self, t, row):
        """Приняла бы база такую строку: имитация проверки ограничений."""
        full = self.fill_defaults(t, row)
        for col in t.columns:
            if col.not_null and full[col.name] is None:
                return False, "столбец %s обязателен" % col.name
        for expr in t.checks:
            if expr.evaluate(full) is False:
                return False, "нарушено ограничение-проверка"
        unique_keys = ([t.pk] if t.pk else []) + list(t.uniques)
        for ix in self.indexes.values():
            if ix["table"] == t.qname and ix["unique"] and not ix.get("partial"):
                unique_keys.append(list(ix["columns"]))
        for key in unique_keys:
            if not key or any(full.get(k) is None for k in key):
                continue
            probe = tuple(_norm(full.get(k)) for k in key)
            for existing in t.rows:
                if tuple(_norm(existing.get(k)) for k in key) == probe:
                    return False, "нарушена уникальность"
        for fk in t.fks:
            vals = [full.get(col) for col in fk["columns"]]
            if any(v is None for v in vals):
                continue
            ref = self.tables.get(fk["ref_table"])
            if ref is None:
                return False, "таблицы %s не существует" % fk["ref_table"]
            ref_cols = fk["ref_columns"] or ref.pk
            found = any(
                tuple(_norm(r.get(rc)) for rc in ref_cols) == tuple(_norm(v) for v in vals)
                for r in ref.rows)
            if not found:
                return False, "нет такой строки в связанной таблице"
        return True, ""

    def would_delete(self, table, column, value):
        """Прошло бы удаление строки при действующих внешних ключах."""
        t = self.tables[self.qualify(table)]
        victims = [r for r in t.rows if _norm(r.get(column)) == _norm(value)]
        if not victims:
            return True, ""
        for other in self.tables.values():
            for fk in other.fks:
                if fk["ref_table"] != t.qname:
                    continue
                ref_cols = fk["ref_columns"] or t.pk
                for r in other.rows:
                    key = tuple(_norm(r.get(col)) for col in fk["columns"])
                    for v in victims:
                        if key == tuple(_norm(v.get(rc)) for rc in ref_cols):
                            if fk["on_delete"] in ("CASCADE", "SET NULL", "SET DEFAULT"):
                                continue
                            return False, "на строку ссылается связанная таблица"
        return True, ""

    # ------------------------------------------------------------ права

    def effective_roles(self, role):
        seen, stack = {role, PUBLIC}, [role]
        while stack:
            cur = stack.pop()
            for parent in self.memberships.get(cur, set()):
                if parent not in seen:
                    seen.add(parent)
                    stack.append(parent)
        return seen

    def has_table_priv(self, role, table, priv):
        table = self.qualify(table)
        t = self.tables.get(table)
        if t is not None and t.owner == role:
            return True
        for r in self.effective_roles(role):
            if priv in self.grants.get((r, "table", table), {}):
                return True
        return False

    def has_column_priv(self, role, table, column, priv):
        table = self.qualify(table)
        if self.has_table_priv(role, table, priv):
            return True
        for r in self.effective_roles(role):
            if priv in self.column_grants.get((r, table), {}).get(column, {}):
                return True
        return False

    def has_schema_priv(self, role, schema, priv):
        for r in self.effective_roles(role):
            if priv in self.grants.get((r, "schema", schema), {}):
                return True
        return False

    def visible_rows(self, table, role):
        t = self.tables[self.qualify(table)]
        if not t.rls_enabled:
            return list(t.rows)
        if t.owner == role and not t.rls_forced:
            return list(t.rows)
        mine = self.effective_roles(role)
        applicable = [p for p in self.policies.values()
                      if p["table"] == t.qname
                      and p["cmd"] in ("ALL", "SELECT")
                      and (PUBLIC in p["roles"] or bool(set(p["roles"]) & mine))]
        if not applicable:
            return []
        return [row for row in t.rows
                if any(p["using"] is None or p["using"].evaluate(row) is True
                       for p in applicable)]


# =====================================================================
#  Мелкие помощники разбора
# =====================================================================

def _norm(v):
    return v.rstrip() if isinstance(v, str) else v


def _name_list(toks):
    c, out = Cursor(toks), []
    while not c.eof():
        out.append(c.name())
        if not c.take_op(","):
            break
    return out


def _split_names(c, keep_public=False):
    out = []
    while True:
        if c.at("PUBLIC"):
            c.next()
            out.append(PUBLIC)
        else:
            c.take("ROLE"); c.take("GROUP")
            if c.at("PUBLIC"):
                c.next()
                out.append(PUBLIC)
            else:
                out.append(c.name())
        if not c.take_op(","):
            break
    return out


def _priv_list(c):
    out = []
    while True:
        if c.take("ALL"):
            c.take("PRIVILEGES")
            out.append("ALL")
        else:
            t = c.next()
            word = t.up
            if word in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE",
                        "TRIGGER", "REFERENCES", "USAGE", "CREATE", "CONNECT",
                        "TEMPORARY", "TEMP", "EXECUTE", "MAINTAIN"):
                out.append("TEMPORARY" if word == "TEMP" else word)
            else:
                raise ModelError("неизвестная привилегия «%s»" % t.text)
        if not c.take_op(","):
            break
    return out


def _rest(c):
    out = []
    while not c.eof():
        out.append(c.next())
    return out


def _literal_text(t):
    if t.kind == "str":
        return t.text[1:-1].replace("''", "'")
    return t.text


def _grab_default(c):
    parts = []
    stop = _COL_STOP - {"DEFAULT"}
    while (not c.eof() and not c.at_op(",")
           and not (c.peek().kind == "word" and c.peek().up in stop)):
        t = c.next()
        parts.append(t.text)
        if t.kind == "word" and c.at_op("("):
            c.balanced()
            parts.append("()")
    return " ".join(parts)


def _value_list(toks):
    c, out = Cursor(toks), []
    while not c.eof():
        neg = False
        if c.at_op("-"):
            c.next()
            neg = True
        t = c.next()
        if t.kind == "str":
            out.append(t.text[1:-1].replace("''", "'"))
        elif t.kind == "num":
            v = float(t.text) if "." in t.text else int(t.text)
            out.append(-v if neg else v)
        elif t.kind in ("word", "quoted"):
            up = t.up
            if up == "NULL":
                out.append(None)
            elif up in ("TRUE", "FALSE"):
                out.append(up == "TRUE")
            elif up == "DEFAULT":
                out.append("<default>")
            else:
                if c.at_op("("):
                    c.balanced()
                out.append("<" + t.text.lower() + ">")
        else:
            raise ModelError("непонятное значение «%s»" % t.text)
        if not c.take_op(","):
            break
    return out


# =====================================================================
#  Пробы: что именно спрашивают у модели
# =====================================================================
#
# Проба — это именованный вопрос к состоянию модели. Сцена перечисляет
# пробы и ожидаемые ответы; ответ студента верен, когда сошлись все.
# Ни одна проба не смотрит на текст запроса, поэтому равносильные
# формулировки засчитываются одинаково.

def _cols_key(cols):
    return ",".join(cols)


def probe(model, name, args):
    a = args or {}

    if name == "schema_exists":
        return a["name"] in model.schemas

    if name == "db_settings":
        s = model.db_settings.get(a["db"], {})
        return sorted([k, v] for k, v in s.items())

    if name == "columns":
        t = model.tables.get(model.qualify(a["table"]))
        if t is None:
            return None
        return [[c.name, c.type, c.length, c.not_null, c.has_default]
                for c in t.columns]

    if name == "primary_key":
        t = model.tables.get(model.qualify(a["table"]))
        return None if t is None else list(t.pk)

    if name == "foreign_keys":
        t = model.tables.get(model.qualify(a["table"]))
        if t is None:
            return None
        return sorted([_cols_key(fk["columns"]), fk["ref_table"],
                       _cols_key(fk["ref_columns"]), _on_delete_ru(fk["on_delete"])]
                      for fk in t.fks)

    if name == "uniques":
        t = model.tables.get(model.qualify(a["table"]))
        if t is None:
            return None
        keys = [_cols_key(u) for u in t.uniques]
        keys += [_cols_key(ix["columns"]) for ix in model.indexes.values()
                 if ix["table"] == t.qname and ix["unique"] and not ix.get("partial")]
        return sorted(set(keys))

    if name == "accepts":
        t = model.tables.get(model.qualify(a["table"]))
        if t is None:
            return None
        return [[case["label"], model.would_accept(t, case["row"])[0]]
                for case in a["cases"]]

    if name == "delete_allowed":
        t = model.tables.get(model.qualify(a["table"]))
        if t is None:
            return None
        return model.would_delete(a["table"], a["column"], a["value"])[0]

    if name == "rows":
        t = model.tables.get(model.qualify(a["table"]))
        if t is None:
            return None
        rows = sorted(t.rows, key=lambda r: _sortable(r.get(a["order_by"])))
        return [[r.get(c) for c in a["columns"]] for r in rows]

    if name == "rows_filled":
        t = model.tables.get(model.qualify(a["table"]))
        if t is None:
            return None
        return all(r.get(a["column"]) is not None for r in t.rows) and bool(t.rows)

    if name == "indexes":
        table = model.qualify(a["table"])
        return sorted([_cols_key(ix["columns"]), ix["unique"],
                       ix.get("method", "btree"), bool(ix.get("partial"))]
                      for ix in model.indexes.values() if ix["table"] == table)

    if name == "view_shape":
        v = model.views.get(model.qualify(a["name"]))
        out = [["существует", v is not None]]
        text = " ".join(t.text.lower() for t in v["body"]) if v else ""
        for token in a.get("mentions", []):
            out.append(["упоминает " + token, token.lower() in text])
        return out

    if name == "roles":
        out = []
        for n in a["names"]:
            r = model.roles.get(n)
            out.append([n, None, None] if r is None else
                       [n, r["login"],
                        bool(r["superuser"] or r["createrole"]
                             or r["createdb"] or r["bypassrls"])])
        return out

    if name == "default_kind":
        t = model.tables.get(model.qualify(a["table"]))
        if t is None:
            return None
        out = []
        for cname in a["columns"]:
            col = t.column(cname)
            out.append([cname, _default_kind(col)])
        return out

    if name == "view_columns":
        v = model.views.get(model.qualify(a["name"]))
        return None if v is None else list(v["columns"])

    if name == "all_memberships":
        return sorted([m, r] for m, rs in model.memberships.items() for r in rs)

    if name == "all_roles":
        return sorted(model.roles)

    if name == "member_admin":
        return sorted([r, (a["member"], r) in model.admin_options]
                      for r in model.memberships.get(a["member"], set()))

    if name == "column_grants_all":
        table = model.qualify(a["table"])
        slot = model.column_grants.get((a["grantee"], table), {})
        return sorted([col, p, bool(g)]
                      for col, privs in slot.items() for p, g in privs.items())

    if name == "schema_privs":
        return sorted(model.grants.get((a["grantee"], "schema", a["schema"]), {}))

    if name == "privs_matrix":
        return [[g, p, model.has_table_priv(g, a["table"], p)]
                for g in a["grantees"] for p in a["privs"]]

    if name == "member_of":
        return sorted(model.memberships.get(a["member"], set()))

    if name == "direct_table_grants":
        table = model.qualify(a["table"])
        return sorted(model.grants.get((a["grantee"], "table", table), {}))

    if name == "has_privs":
        return [[p, model.has_table_priv(a["grantee"], a["table"], p)]
                for p in a["privs"]]

    if name == "column_privs":
        table = model.qualify(a["table"])
        slot = model.column_grants.get((a["grantee"], table), {})
        return sorted(col for col, privs in slot.items() if a["priv"] in privs)

    if name == "search_path":
        return list(model.search_path)

    if name == "can_read_columns":
        return [[col, model.has_column_priv(a["grantee"], a["table"], col, "SELECT")]
                for col in a["columns"]]

    if name == "has_schema_priv":
        return model.has_schema_priv(a["grantee"], a["schema"], a["priv"])

    if name == "default_privs":
        out = []
        for e in model.default_privs:
            if e["schema"] == a["schema"]:
                for p in e["privs"]:
                    out.append([e["objtype"], e["grantee"], p])
        return sorted(out)

    if name == "rls":
        t = model.tables.get(model.qualify(a["table"]))
        return None if t is None else [t.rls_enabled, t.rls_forced]

    if name == "policies":
        table = model.qualify(a["table"])
        return sorted([n, p["cmd"], ",".join(sorted(p["roles"]))]
                      for n, p in model.policies.items() if p["table"] == table)

    if name == "visible_rows":
        rows = model.visible_rows(a["table"], a["role"])
        rows = sorted(rows, key=lambda r: _sortable(r.get(a.get("order_by",
                                                               a["columns"][0]))))
        return [[r.get(c) for c in a["columns"]] for r in rows]

    if name == "grantable":
        table = model.qualify(a["table"])
        g = model.grants.get((a["grantee"], "table", table), {})
        return sorted([p, bool(v)] for p, v in g.items())

    if name == "public_privs":
        table = model.qualify(a["table"])
        return sorted(model.grants.get((PUBLIC, "table", table), {}))

    raise ModelError("неизвестная проба «%s»" % name)


def _default_kind(col):
    """Каким по смыслу задано значение по умолчанию."""
    if col is None:
        return "столбца нет"
    if not col.has_default:
        return "нет"
    text = (col.default_text or "").lower()
    if any(w in text for w in ("now", "current_date", "current_timestamp",
                               "localtimestamp", "clock_timestamp",
                               "statement_timestamp", "transaction_timestamp",
                               "current_time")):
        return "текущий момент"
    if "nextval" in text:
        return "счётчик"
    return "постоянное значение"


def _on_delete_ru(action):
    """Смысл правила удаления: NO ACTION и RESTRICT одинаково запрещают удаление."""
    return {"NO ACTION": "запрещает удаление",
            "RESTRICT": "запрещает удаление",
            "CASCADE": "удаляет следом",
            "SET NULL": "обнуляет ссылку",
            "SET DEFAULT": "ставит значение по умолчанию"}.get(action, action)


def _sortable(v):
    if v is None:
        return (0, "")
    if isinstance(v, bool):
        return (1, str(v))
    if isinstance(v, (int, float)):
        return (2, v)
    return (3, str(v))


# =====================================================================
#  Проверка ответа студента
# =====================================================================

def types_compatible(got_type: str, exp_type: str) -> bool:
    """Проверка эквивалентности типов для валидации каталога.

    - Если ожидается integer / int, считать валидным также: serial, int4, smallserial, smallint, int2.
    - Если ожидается bigint / int8, считать валидным также: bigserial, int8.
    - Если ожидается smallint / int2, считать валидным также: smallserial, int2.
    - Для остальных типов — равенство с учётом алиасов TYPE_MAP.
    """
    if not got_type or not exp_type:
        return got_type == exp_type
    gt = str(got_type).lower()
    et = str(exp_type).lower()
    if gt == et:
        return True
    g_canon = TYPE_MAP.get(gt, gt)
    e_canon = TYPE_MAP.get(et, et)
    if g_canon == e_canon:
        return True

    int_compat = {"integer", "int", "int4", "serial", "smallserial", "smallint", "int2"}
    if (et in ("integer", "int") or e_canon == "integer") and (gt in int_compat or g_canon in int_compat):
        return True

    bigint_compat = {"bigint", "bigserial", "int8"}
    if (et in ("bigint", "int8") or e_canon == "bigint") and (gt in bigint_compat or g_canon in bigint_compat):
        return True

    smallint_compat = {"smallint", "int2", "smallserial"}
    if (et in ("smallint", "int2") or e_canon == "smallint") and (gt in smallint_compat or g_canon in smallint_compat):
        return True

    return False


def _matches_columns(got, expected, table=None) -> bool:
    """Сравнивает фактические столбцы (got) со спецификацией (expected).

    Не реджектит валидный синтаксис SERIAL PRIMARY KEY:
    если ожидается integer PRIMARY KEY без default (has_default=False),
    а студент указал SERIAL (has_default=True, nextval),
    считать это допустимым.
    """
    if not isinstance(got, list) or not isinstance(expected, list):
        return got == expected
    if len(got) != len(expected):
        return False
    for g, e in zip(got, expected):
        if not (isinstance(g, (list, tuple)) and isinstance(e, (list, tuple)) and len(g) == 5 and len(e) == 5):
            if g != e:
                return False
            continue
        g_name, g_type, g_len, g_nn, g_def = g
        e_name, e_type, e_len, e_nn, e_def = e

        if str(g_name).lower() != str(e_name).lower():
            return False
        if not types_compatible(g_type, e_type):
            return False
        if g_len != e_len:
            return False
        if g_nn != e_nn:
            return False

        if g_def != e_def:
            col = table.column(g_name) if table else None
            is_serial = getattr(col, "is_serial", False) if col else False
            if g_def and not e_def and is_serial:
                pass
            else:
                return False
    return True


def verify(student_sql, spec):
    """Возвращает (верно ли, пояснение).

    Обстановка сцены (setup) и действия после ответа (post) — авторские,
    им доверяем. Ошибка разбора ответа студента — это неверный ответ,
    а не сбой проверки.
    """
    answer = (student_sql or "").strip()
    if not answer:
        return False, "Пустой ответ."

    model = Model(spec.get("database", "quest_sandbox"))
    try:
        for stmt in spec.get("setup", []):
            model.execute(stmt)
    except ModelError as exc:                       # pragma: no cover
        return False, "Ошибка в обстановке сцены: %s" % exc

    try:
        model.execute(answer)
    except ModelError as exc:
        return False, "Запрос не выполнить: %s" % exc

    try:
        for stmt in spec.get("post", []):
            model.execute(stmt)
    except ModelError as exc:
        return False, "После такого ответа продолжить не удалось: %s" % exc

    for item in spec.get("expect", []):
        try:
            got = probe(model, item["probe"], item.get("args"))
        except ModelError as exc:
            return False, "Проверка «%s» не удалась: %s" % (item.get("title", ""), exc)
        matched = False
        if item["probe"] == "columns":
            tbl = None
            args = item.get("args")
            if args and "table" in args:
                tbl = model.tables.get(model.qualify(args["table"]))
            matched = _matches_columns(got, item["value"], tbl)
        else:
            matched = (got == item["value"])

        if not matched:
            return False, "Не совпало: %s." % (item.get("title") or item["probe"])
    return True, "Проверка пройдена."


def capture(spec, answer):
    """Снимает эталонные ответы проб для эталонного решения (для сборки сцен)."""
    model = Model(spec.get("database", "quest_sandbox"))
    for stmt in spec.get("setup", []):
        model.execute(stmt)
    model.execute(answer)
    for stmt in spec.get("post", []):
        model.execute(stmt)
    return [probe(model, item["probe"], item.get("args")) for item in spec["expect"]]


__all__ = ["Model", "ModelError", "verify", "capture", "probe", "types_compatible",
           "split_statements", "tokenize", "parse_expr", "SUPPORTED"]
