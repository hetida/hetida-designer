import datetime

from dtexp import parse_dtexp, parse_dtexp_interval

from hetdesrun.reference_context import get_exec_start_from_reproducibility_context
from hetdesrun.runtime.context import get_global_time_interval_info


def resolve_dtexp(
    dtexp_expression: str,
    to_utc: bool = True,
    default_unaware_timezone: datetime.timezone = datetime.UTC,
    max_iso_timestamp_length: int = 35,
    fixed_iso_timestamp_length: int | None = None,
    max_iter: int = 1000,
    allow_conditions: bool = True,
) -> datetime.datetime:
    """Use reproducibility context exec start to resolve now when resolving dtexp

    During designer trafo execution, this function should be used when parsing / resolving
    dtexp expression. It uses the exec_start_timestamp from the reproducibility context
    to resolve "now" in such expressions.

    Raises:
        DtexpParsingError
    """

    return parse_dtexp(
        dtexp_expression.strip(),
        to_utc=to_utc,
        now=get_exec_start_from_reproducibility_context(),
        default_unaware_timezone=default_unaware_timezone,
        max_iso_timestamp_length=max_iso_timestamp_length,
        fixed_iso_timestamp_length=fixed_iso_timestamp_length,
        max_iter=max_iter,
        allow_conditions=allow_conditions,
    )


def resolve_interval(
    start_expression: str | None,
    end_expression: str | None,
    to_utc: bool = True,
    default_unaware_timezone: datetime.timezone = datetime.UTC,
    max_iso_timestamp_length: int = 35,
    fixed_iso_timestamp_length: int | None = None,
    max_iter: int = 1000,
    allow_conditions: bool = True,
) -> tuple[datetime.datetime, datetime.datetime]:
    """Resolve interval from expressions as well as global time interval and now from context

    Resolves a time interval and parses start / end expressions into aware datetime objects.

    If provided expressions are None, it will try to use globally provided time interval
    start/end expressions from the runtime execution context. Furthermore possible "now"
    occuring in the expressions is resolved from reproducibility reference context.

    Returns:
        pair of start and end aware datetimes

    Raises:
        ValueError (or DtexpParsingError) if no valid interval could be parsed / inferred.
    """
    time_interval = get_global_time_interval_info()
    start_exp = start_expression or time_interval.timestampFrom
    end_exp = end_expression or time_interval.timestampTo

    if start_exp is None:
        raise ValueError(
            "No global time interval start and no start_expression. At least one must be provided."
        )
    if end_exp is None:
        raise ValueError(
            "No global time interval end and no end_expression. At least one must be provided."
        )

    # may raise DtexpParsingError:
    start, end = parse_dtexp_interval(
        start_exp.strip(),
        end_exp.strip(),
        to_utc=to_utc,
        now=get_exec_start_from_reproducibility_context(),
        default_unaware_timezone=default_unaware_timezone,
        max_iso_timestamp_length=max_iso_timestamp_length,
        fixed_iso_timestamp_length=fixed_iso_timestamp_length,
        max_iter=max_iter,
        allow_conditions=allow_conditions,
    )

    if end < start:
        msg = f"Invalid Interval: end {end.isoformat()} < start {start.isoformat()}"
        raise ValueError(msg)

    return (start, end)
