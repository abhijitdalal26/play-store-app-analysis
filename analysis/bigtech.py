"""
Big-tech / pre-installed developer detection — reused from app_opportunity_research's
methodology. These publishers ship apps that arrive on the phone before day one (or ride an
existing billion-user platform), so they aren't real competition for a new developer and are
excluded from every competition/opportunity metric in the report. They're kept in the raw
data and shown separately, for context.

Matching is whole-word / whole-phrase, not raw substring — plain substring matching produced
real false positives against this dataset: 'opera' matched every "...Operations"/"...Operating"
company, 'x corp' matched "Vertex Corporation" and "Cognex Corporation", 'amazon' matched a
Brazilian tax agency ("...do Amazonas"), and 'google' matched "BoldGoogleApps".
"""
import re

BIG_TECH_PATTERNS = [
    'google', 'meta platforms', 'facebook', 'instagram', 'whatsapp',
    'microsoft', 'amazon', 'netflix', 'spotify', 'twitter', 'x corp',
    'tiktok', 'bytedance', 'snapchat', 'linkedin', 'adobe', 'apple inc',
    'samsung', 'huawei', 'xiaomi', 'alibaba', 'tencent', 'baidu',
    'mozilla', 'opera', 'yahoo', 'uber', 'airbnb', 'paypal', 'ebay',
    'booking.com', 'expedia', 'tripadvisor',
]

_PATTERN_BODY = "|".join(re.escape(p) for p in BIG_TECH_PATTERNS)
_REGEX = re.compile(r"\b(" + _PATTERN_BODY + r")\b", re.IGNORECASE)


def is_big_tech(dev_name):
    if dev_name is None:
        return False
    try:
        if dev_name != dev_name:  # NaN check without importing pandas
            return False
    except Exception:
        pass
    return bool(_REGEX.search(str(dev_name)))


def sql_match_clause(column="developer"):
    """True when the developer IS big tech — whole-word regex match on the lowercased name."""
    return rf"regexp_matches(lower({column}), '\b({_PATTERN_BODY})\b')"


def sql_exclude_clause(column="developer"):
    """True when the developer is NOT big tech (i.e. indie)."""
    return f"NOT ({sql_match_clause(column)})"
