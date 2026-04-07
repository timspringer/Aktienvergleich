"""Data normalization utilities."""

import re
import logging
from typing import Any, Optional, Union
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

# Placeholder for invalid/missing data
NOT_VALID = 'NV'


def is_valid_value(value: Any) -> bool:
    """Check if a value is valid (not None, not empty string, not just dashes)."""
    if value is None:
        return False
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or stripped in ('—', '-', '–', ''):
            return False
    return True


def normalize_to_number(value: Any) -> Optional[Union[float, Decimal]]:
    """
    Normalize a value to a number (float or Decimal).

    Handles:
    - German format: "1.234,56" → 1234.56
    - English format: "1,234.56" → 1234.56
    - Percentages: "5,5%" → 5.5
    - Scientific notation: "1,5e6" → 1500000

    Returns:
        float, Decimal, or None if conversion fails
    """
    if not is_valid_value(value):
        return None

    # Convert to string and clean up
    value_str = str(value).strip()

    # Remove whitespace
    value_str = value_str.replace(' ', '')

    # Handle percentage signs
    is_percentage = '%' in value_str
    value_str = value_str.replace('%', '')

    # Try direct float conversion first (handles scientific notation)
    try:
        return float(value_str)
    except ValueError:
        pass

    # Detect German vs English format
    # If last comma is after last period, it's German (1.234,56)
    # If last period is after last comma, it's English (1,234.56)
    last_comma = value_str.rfind(',')
    last_period = value_str.rfind('.')

    if last_comma > last_period:
        # German format: 1.234,56 → 1234.56
        value_str = value_str.replace('.', '').replace(',', '.')
    elif last_period > last_comma:
        # English format: 1,234.56 → keep as is
        value_str = value_str.replace(',', '')
    elif last_comma >= 0:
        # Only comma present - assume decimal separator if followed by 1-2 digits
        if len(value_str) - last_comma <= 3:
            value_str = value_str.replace(',', '.')
        else:
            value_str = value_str.replace(',', '')

    try:
        result = float(value_str)
        return result
    except ValueError:
        logger.warning(f'Could not normalize value: {value}')
        return None


def normalize_to_int(value: Any) -> Optional[int]:
    """Normalize value to integer."""
    num = normalize_to_number(value)
    if num is not None:
        return int(num)
    return None


def normalize_revenue(value: Any) -> Optional[float]:
    """
    Normalize revenue value (in millions).

    Assumes value is already in millions.
    """
    return normalize_to_number(value)


def normalize_dividend(value: Any) -> Optional[float]:
    """Normalize dividend per share."""
    return normalize_to_number(value)


def normalize_dividend_yield(value: Any) -> Optional[float]:
    """Normalize dividend yield (as percentage 0-100)."""
    num = normalize_to_number(value)
    if num is not None and 0 <= num <= 1000:  # Sanity check
        return num
    return None


def normalize_eps(value: Any) -> Optional[float]:
    """Normalize earnings per share."""
    return normalize_to_number(value)


def normalize_pe_ratio(value: Any) -> Optional[float]:
    """Normalize P/E ratio."""
    num = normalize_to_number(value)
    if num is not None:
        # P/E ratio should be positive (or very close to zero for special cases)
        if num > 0 or abs(num) < 0.01:
            return num
    return None


def normalize_price_target(value: Any) -> Optional[float]:
    """Normalize price target."""
    return normalize_to_number(value)


def normalize_fiscal_year(value: Any) -> Optional[int]:
    """Normalize fiscal year."""
    year = normalize_to_int(value)
    if year and 1900 < year < 3000:
        return year
    return None


def normalize_estimate_field(
    field_name: str, value: Any
) -> Optional[Union[float, int]]:
    """
    Normalize an estimate field based on its name.

    Args:
        field_name: Name of the field (e.g., 'pe_ratio', 'revenue')
        value: Raw value to normalize

    Returns:
        Normalized value or None
    """
    normalizers = {
        'revenue': normalize_revenue,
        'dividend': normalize_dividend,
        'dividend_yield': normalize_dividend_yield,
        'eps': normalize_eps,
        'pe_ratio': normalize_pe_ratio,
        'price_target': normalize_price_target,
        'fiscal_year': normalize_fiscal_year,
    }

    normalizer = normalizers.get(field_name.lower())
    if normalizer:
        return normalizer(value)
    return normalize_to_number(value)


def format_as_nv_if_invalid(value: Any) -> Union[str, float, int]:
    """Return 'NV' if value is invalid, otherwise return normalized value."""
    if not is_valid_value(value):
        return NOT_VALID

    # Try to normalize
    num = normalize_to_number(value)
    return num if num is not None else NOT_VALID


def extract_text_between_tags(html: str, tag: str) -> Optional[str]:
    """Extract text content between HTML tags."""
    pattern = f'<{tag}[^>]*>([^<]+)</{tag}>'
    match = re.search(pattern, html)
    return match.group(1).strip() if match else None


def clean_whitespace(text: str) -> str:
    """Clean excessive whitespace from text."""
    return ' '.join(text.split())
