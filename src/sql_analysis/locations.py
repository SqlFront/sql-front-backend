"""Поиск позиции AST-фрагмента в исходном SQL для подсказок редактора."""

from src.sql_analysis.findings import SourceLocation


def locate_fragment(source: str, fragment: str | None) -> SourceLocation | None:
    """Возвращает первую позицию фрагмента без учёта регистра.

    SQLGlot 20.8 не сохраняет координаты AST-узлов, поэтому позиция
    восстанавливается по исходному тексту. Для учебных подсказок этого
    достаточно, а отсутствие совпадения безопасно выражается через None.
    """
    if not fragment:
        return None

    start = source.casefold().find(fragment.casefold())
    if start < 0:
        return None

    end = start + len(fragment)
    before = source[:start]
    matched = source[start:end]
    line = before.count("\n") + 1
    column = start - before.rfind("\n")
    end_line = line + matched.count("\n")
    if "\n" in matched:
        end_column = len(matched.rsplit("\n", maxsplit=1)[-1]) + 1
    else:
        end_column = column + len(matched)

    source_line = source.splitlines()[line - 1] if source.splitlines() else source
    return SourceLocation(
        line=line,
        column=column,
        end_line=end_line,
        end_column=end_column,
        snippet=source_line.strip(),
    )
