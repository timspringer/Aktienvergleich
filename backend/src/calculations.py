"""CAGR and other financial calculations."""

import logging
import math
from typing import Optional, List, Tuple
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

NOT_VALID = 'NV'


def calculate_cagr(
    start_value: float,
    end_value: float,
    periods: int,
    decimal_places: int = 2,
) -> Optional[str]:
    """
    Calculate Compound Annual Growth Rate (CAGR).

    Formula: CAGR = (End Value / Start Value) ^ (1 / Periods) - 1

    Args:
        start_value: Starting value (from earliest year)
        end_value: Ending value (from latest year)
        periods: Number of years between start and end
        decimal_places: Decimal places in percentage output

    Returns:
        CAGR as percentage string (e.g., "5.23" for 5.23%)
        Returns NOT_VALID if calculation not possible
    """
    # Validate inputs
    if not all(isinstance(x, (int, float)) for x in [start_value, end_value, periods]):
        return NOT_VALID

    if start_value <= 0 or end_value <= 0:
        logger.debug(f'CAGR: Invalid values - start={start_value}, end={end_value}')
        return NOT_VALID

    if periods <= 0:
        return NOT_VALID

    try:
        # Calculate CAGR
        cagr = (end_value / start_value) ** (1 / periods) - 1

        # Convert to percentage and format
        cagr_percent = cagr * 100

        # Round to specified decimal places
        rounded = Decimal(str(cagr_percent)).quantize(
            Decimal(10) ** -decimal_places, rounding=ROUND_HALF_UP
        )

        return str(rounded)
    except (ValueError, ZeroDivisionError) as e:
        logger.debug(f'CAGR calculation error: {e}')
        return NOT_VALID


def get_valid_values_for_period(
    values_by_year: dict[int, Optional[float]],
) -> Tuple[Optional[float], Optional[float], Optional[int], Optional[int]]:
    """
    Get first and last valid values from a dictionary of year -> value.

    Args:
        values_by_year: Dictionary mapping fiscal years to values

    Returns:
        Tuple of (first_value, last_value, first_year, last_year)
        Returns (None, None, None, None) if less than 2 valid values
    """
    # Filter out None values
    valid_items = [
        (year, value) for year, value in values_by_year.items() if value is not None
    ]

    if len(valid_items) < 2:
        return None, None, None, None

    # Sort by year
    valid_items.sort(key=lambda x: x[0])

    first_year, first_value = valid_items[0]
    last_year, last_value = valid_items[-1]

    return first_value, last_value, first_year, last_year


def calculate_cagr_for_metric(
    values_by_year: dict[int, Optional[float]], decimal_places: int = 2
) -> Optional[str]:
    """
    Calculate CAGR for a metric given yearly values.

    Args:
        values_by_year: Dictionary mapping fiscal years to values
        decimal_places: Decimal places in output

    Returns:
        CAGR as percentage string or NOT_VALID
    """
    first_value, last_value, first_year, last_year = get_valid_values_for_period(
        values_by_year
    )

    if first_value is None or last_value is None or first_year is None or last_year is None:
        return NOT_VALID

    periods = last_year - first_year
    return calculate_cagr(first_value, last_value, periods, decimal_places)


def check_data_completeness(
    values_by_year: dict[int, Optional[float]],
) -> Tuple[bool, int, int]:
    """
    Check if a metric has complete data.

    Returns:
        Tuple of (is_complete, total_years, years_with_data)
    """
    total_years = len(values_by_year)
    years_with_data = sum(1 for v in values_by_year.values() if v is not None)

    is_complete = total_years > 0 and years_with_data == total_years

    return is_complete, total_years, years_with_data


def get_min_max_values(
    values: List[Optional[float]],
) -> Tuple[Optional[float], Optional[float]]:
    """
    Get minimum and maximum values from a list.

    Args:
        values: List of values (may contain None)

    Returns:
        Tuple of (min_value, max_value), excluding None values
    """
    valid_values = [v for v in values if v is not None]

    if not valid_values:
        return None, None

    return min(valid_values), max(valid_values)


def calculate_growth_rate(
    start_value: float, end_value: float
) -> Optional[str]:
    """
    Calculate simple growth rate (not CAGR).

    Formula: Growth Rate = (End Value - Start Value) / Start Value

    Args:
        start_value: Starting value
        end_value: Ending value

    Returns:
        Growth rate as percentage string or NOT_VALID
    """
    if start_value <= 0:
        return NOT_VALID

    try:
        growth = (end_value - start_value) / start_value
        growth_percent = growth * 100
        rounded = Decimal(str(growth_percent)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        return str(rounded)
    except (ValueError, ZeroDivisionError):
        return NOT_VALID
