from datetime import datetime
import calendar
from datetime import datetime, date
from typing import Union


def datefield_now() -> date:
    return datetime.now().date()

def _to_date(dt: Union[str, date, datetime]) -> date:
    """Converte input para date (aceita str 'YYYY-MM-DD', date ou datetime)."""
    if isinstance(dt, str):
        return datetime.strptime(dt, "%Y-%m-%d").date()
    if isinstance(dt, datetime):
        return dt.date()
    return dt


def add_months(dt: Union[str, date, datetime], months: int) -> date:
    """Adiciona meses reutilizando a mesma lógica de ajuste de dia final do mês."""
    d = _to_date(dt)
    total_months = d.month - 1 + months
    year = d.year + (total_months // 12)
    month = (total_months % 12) + 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(d.day, last_day)
    return date(year, month, day)


def one_month_more(dt: Union[str, date, datetime]) -> date:
    """Retorna a data com um mês a mais."""
    return add_months(dt, 1)


def one_year_more(dt: Union[str, date, datetime]) -> date:
    """Retorna a data com um ano a mais (12 meses)."""
    return add_months(dt, 12)