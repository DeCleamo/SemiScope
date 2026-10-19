"""
Chemical formula typography module for SemiScope.
Provides reusable utilities to render chemical formulas with correct
scientific subscript typography (e.g. In5CuS8 -> In₅CuS₈ / In<sub>5</sub>CuS<sub>8</sub>)
without mutating underlying data or misformatting identifiers, ranks, or scores.
"""

import re
from typing import Optional, Union, Any


def format_formula_html(formula: Union[str, Any]) -> str:
    """
    Renders a chemical formula into HTML with stoichiometric numbers subscripted.

    Rules & guarantees:
    - Digits immediately following element symbols, closing parentheses ')',
      or closing brackets ']' are converted into <sub>...</sub>.
    - Decimals in stoichiometry (e.g. Ag0.5Ge1Pb1.75S4, La1Se0.14S1.86)
      are preserved and fully subscripted (<sub>0.5</sub>, <sub>1.75</sub>).
    - Parentheses and complex groupings (e.g. Ag(AuS)2, V3Bi(PbO4)3) are preserved.
    - Non-formula strings, ranks (e.g. '#2', 'Rank #1'), scores ('0.9996'),
      and empty/invalid inputs are safely returned unchanged.
    - Plain text copyability: stripping <sub> and </sub> perfectly recovers
      the canonical formula string without data corruption.

    Examples:
        'TlAsSe2' -> 'TlAsSe<sub>2</sub>'
        'K2Gd2Sb2Se9' -> 'K<sub>2</sub>Gd<sub>2</sub>Sb<sub>2</sub>Se<sub>9</sub>'
        'In5CuS8' -> 'In<sub>5</sub>CuS<sub>8</sub>'
        'Cs3Bi2Br9' -> 'Cs<sub>3</sub>Bi<sub>2</sub>Br<sub>9</sub>'
        'GaAs' -> 'GaAs'
        'SiO2' -> 'SiO<sub>2</sub>'
        'Ag(AuS)2' -> 'Ag(AuS)<sub>2</sub>'
        'Ag0.5Ge1Pb1.75S4' -> 'Ag<sub>0.5</sub>Ge<sub>1</sub>Pb<sub>1.75</sub>S<sub>4</sub>'
        '#2' -> '#2'
        '0.9996' -> '0.9996'
    """
    if formula is None:
        return ""
    if not isinstance(formula, str):
        return str(formula)

    s = formula.strip()
    if not s:
        return ""

    # Safe validation check: chemical formulas only contain alphanumeric chars,
    # decimals, parentheses, brackets, or +/- charge signs, without whitespace.
    # If the string contains spaces, hash symbols, or unexpected punctuation,
    # return it unchanged to avoid formatting identifiers, prose, or ranks.
    if not re.match(r"^[A-Za-z0-9.()\[\]+-]+$", s):
        return formula

    # If the string starts with a digit or punctuation (like a score '0.9996' or '.5'),
    # it is not a chemical formula; return unchanged.
    if s[0].isdigit() or s[0] in ".-+":
        return formula

    # Must contain at least one uppercase letter (chemical elements always start with uppercase)
    if not any(c.isupper() for c in s):
        return formula

    # Match digits (including decimals like 0.14, 1.75) that immediately follow an element
    # symbol character (letter) or a closing group delimiter ')' or ']'.
    # Uses positive lookbehind (?<=[A-Za-z)\]]) so only stoichiometric numbers are converted.
    formatted = re.sub(r"(?<=[A-Za-z)\]])(\d+(?:\.\d+)?)", r"<sub>\1</sub>", s)
    return formatted


UNICODE_SUBSCRIPTS = {
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
    "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
    ".": "․",
}


def format_formula_unicode(formula: str) -> str:
    """
    Converts a chemical formula into unicode subscript characters where HTML is unavailable.
    (e.g. for pure-text exports or tooltips).
    """
    if not formula or not isinstance(formula, str):
        return str(formula) if formula is not None else ""

    s = formula.strip()
    if not re.match(r"^[A-Za-z0-9.()\[\]+-]+$", s) or not any(c.isupper() for c in s) or s[0].isdigit():
        return formula

    def _sub_repl(m):
        num_str = m.group(1)
        return "".join(UNICODE_SUBSCRIPTS.get(c, c) for c in num_str)

    return re.sub(r"(?<=[A-Za-z)\]])(\d+(?:\.\d+)?)", _sub_repl, s)
