"""Токены процедурного тела и локальные эвристики качества PL/pgSQL."""

from collections.abc import Iterator

from sqlglot.dialects.postgres import Postgres
from sqlglot.tokens import Token, TokenType


class _BodyTokenizer(Postgres.Tokenizer):
    # В обычном SQL SQLGlot читает целиком хвост команды BEGIN или DECLARE.
    COMMANDS = set()
    SINGLE_TOKENS = {**Postgres.Tokenizer.SINGLE_TOKENS, "$": TokenType.PARAMETER}
    KEYWORDS = {**Postgres.Tokenizer.KEYWORDS, "$": TokenType.PARAMETER}

    def _scan_string(self, start: str) -> bool:
        # Dollar quote и позиционный параметр $1 начинаются одинаково.
        if start == "$" and self._peek.isascii() and self._peek.isdigit():
            return False
        return super()._scan_string(start)


def body_tokens(body: str) -> list[Token]:
    return _BodyTokenizer().tokenize(body)


def token_spelling(body: str, token: Token) -> str:
    return body[token.start:token.end + 1]


def referenced_names(tokens: list[Token]) -> set[str]:
    """Консервативно считает совпадения имён вне строк и комментариев."""
    return {
        token.text.casefold()
        for token in tokens
        if token.token_type in (TokenType.VAR, TokenType.IDENTIFIER)
    }


def unused_declarations(body: str, tokens: list[Token]) -> Iterator[Token]:
    """Ищет имена верхнего DECLARE, не встречающиеся после объявления."""
    words = [token_spelling(body, token).upper() for token in tokens]
    if words[:1] != ["DECLARE"] or "BEGIN" not in words:
        return
    end = words.index("BEGIN")
    last_reference = {
        token.text.casefold(): index
        for index, token in enumerate(tokens)
        if token.token_type in (TokenType.VAR, TokenType.IDENTIFIER)
    }
    for index in range(1, end):
        token = tokens[index]
        if words[index - 1] not in {"DECLARE", ";"} or token.token_type not in (
            TokenType.VAR, TokenType.IDENTIFIER,
        ):
            continue
        if last_reference[token.text.casefold()] == index:
            yield token


def empty_control_blocks(body: str, tokens: list[Token]) -> Iterator[tuple[str, Token]]:
    """Находит пустые ветки IF и тела циклов. NULL считается явным действием."""
    words = [token_spelling(body, token).upper() for token in tokens]
    for index, word in enumerate(words):
        following = words[index + 1:index + 3]
        if word == "LOOP" and following == ["END", "LOOP"]:
            yield "loop", tokens[index]
        elif word in {"THEN", "ELSE"} and (
            following == ["END", "IF"]
            or (word == "THEN" and following[:1] in (["ELSE"], ["ELSIF"]))
        ):
            yield "branch", tokens[index]
