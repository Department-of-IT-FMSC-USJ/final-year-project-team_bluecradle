import math

# WHO LMS reference tables (abbreviated).
# L = Box-Cox power, M = Median, S = Coefficient of variation
# Source: WHO Child Growth Standards (2006)
# Full tables to be loaded from WHO reference CSV files.

def classify_who(whz, muac_mm=None, oedema=False):
    """
    Apply WHO thresholds to return SAM / MAM / NORMAL.
    Oedema overrides everything.
    """
    if oedema:
        return 'SAM'
    if muac_mm is not None:
        if muac_mm < 115:
            return 'SAM'
        if 115 <= muac_mm < 125:
            return 'MAM'
    if whz is not None:
        if whz < -3:
            return 'SAM'
        if -3 <= whz < -2:
            return 'MAM'
    return 'NORMAL'