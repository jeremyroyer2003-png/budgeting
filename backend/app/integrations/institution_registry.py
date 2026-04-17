"""
institution_registry.py — Master list of supported financial institutions.

Each entry defines which provider handles that institution and whether a
fallback provider should be tried if the primary fails.

provider:  "plaid" | "flinks" | "wealthica"
fallback:  optional secondary provider

Usage:
    from .institution_registry import get_institution, search_institutions
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Institution:
    id: str                     # internal slug  e.g. "td_ca"
    name: str                   # display name
    country: str                # "CA" or "US"
    provider: str               # primary provider
    fallback: Optional[str]     # secondary provider (None if N/A)
    logo_key: Optional[str]     # key for a future logo CDN
    category: str               # "bank" | "credit_union" | "investment" | "neobank"


# ── Canadian institutions ──────────────────────────────────────────────────────

_CA = [
    # Big Six banks — Flinks primary (better OAuth support), Plaid fallback
    Institution("td_ca",       "TD Bank",                  "CA", "flinks",   "plaid",    "td",          "bank"),
    Institution("rbc_ca",      "RBC Royal Bank",           "CA", "flinks",   "plaid",    "rbc",         "bank"),
    Institution("bmo_ca",      "BMO Bank of Montreal",     "CA", "flinks",   "plaid",    "bmo",         "bank"),
    Institution("cibc_ca",     "CIBC",                     "CA", "flinks",   "plaid",    "cibc",        "bank"),
    Institution("scotiabank",  "Scotiabank",               "CA", "flinks",   "plaid",    "scotiabank",  "bank"),
    Institution("nbc_ca",      "National Bank",            "CA", "flinks",   "plaid",    "nbc",         "bank"),

    # Desjardins — Flinks only (Plaid coverage is unreliable)
    Institution("desjardins",  "Desjardins",               "CA", "flinks",   None,       "desjardins",  "credit_union"),

    # Other credit unions & regional banks
    Institution("meridian",    "Meridian Credit Union",    "CA", "flinks",   None,       None,          "credit_union"),
    Institution("coast_cap",   "Coast Capital Savings",    "CA", "flinks",   None,       None,          "credit_union"),
    Institution("atb",         "ATB Financial",            "CA", "flinks",   None,       None,          "bank"),
    Institution("simplii",     "Simplii Financial",        "CA", "flinks",   "plaid",    None,          "neobank"),
    Institution("tangerine",   "Tangerine",                "CA", "plaid",    "flinks",   None,          "neobank"),
    Institution("hsbc_ca",     "HSBC Canada",              "CA", "plaid",    "flinks",   "hsbc",        "bank"),
    Institution("laurentian",  "Laurentian Bank",          "CA", "flinks",   None,       None,          "bank"),
    Institution("eq_bank",     "EQ Bank",                  "CA", "plaid",    None,       None,          "neobank"),
    Institution("motusbank",   "Motus Bank",               "CA", "flinks",   None,       None,          "neobank"),

    # Investment platforms — Wealthica primary (richer portfolio data)
    Institution("wealthsimple","Wealthsimple",             "CA", "wealthica","plaid",    "wealthsimple","investment"),
    Institution("questrade",   "Questrade",                "CA", "wealthica", None,      "questrade",   "investment"),
    Institution("rbc_di",      "RBC Direct Investing",     "CA", "wealthica","flinks",   "rbc",         "investment"),
    Institution("td_di",       "TD Direct Investing",      "CA", "wealthica","flinks",   "td",          "investment"),
    Institution("bmo_il",      "BMO InvestorLine",         "CA", "wealthica","flinks",   "bmo",         "investment"),
    Institution("cibc_ii",     "CIBC Investor's Edge",     "CA", "wealthica","flinks",   "cibc",        "investment"),
    Institution("disnat",      "Disnat (Desjardins)",      "CA", "wealthica", None,      "desjardins",  "investment"),
    Institution("mackenzie",   "Mackenzie Investments",    "CA", "wealthica", None,      None,          "investment"),
    Institution("manulife_inv","Manulife Investments",     "CA", "wealthica", None,      None,          "investment"),
    Institution("sunlife",     "Sun Life",                 "CA", "wealthica", None,      None,          "investment"),
    Institution("ia_financial","iA Financial Group",       "CA", "wealthica", None,      None,          "investment"),
    Institution("fidelity_ca", "Fidelity Canada",          "CA", "wealthica", None,      None,          "investment"),
    Institution("nbdb",        "National Bank Direct Brokerage","CA","wealthica","flinks",None,         "investment"),
]

# ── US institutions ────────────────────────────────────────────────────────────

_US = [
    # Major banks — Plaid only
    Institution("chase",       "Chase",                    "US", "plaid",    None, "chase",       "bank"),
    Institution("bofa",        "Bank of America",          "US", "plaid",    None, "bofa",        "bank"),
    Institution("wells_fargo", "Wells Fargo",              "US", "plaid",    None, "wellsfargo",  "bank"),
    Institution("citi",        "Citi",                     "US", "plaid",    None, "citi",        "bank"),
    Institution("us_bank",     "U.S. Bank",                "US", "plaid",    None, "usbank",      "bank"),
    Institution("capital_one", "Capital One",              "US", "plaid",    None, "capitalone",  "bank"),
    Institution("ally",        "Ally Bank",                "US", "plaid",    None, "ally",        "neobank"),
    Institution("pnc",         "PNC Bank",                 "US", "plaid",    None, None,          "bank"),
    Institution("truist",      "Truist",                   "US", "plaid",    None, None,          "bank"),
    Institution("td_us",       "TD Bank (US)",             "US", "plaid",    None, "td",          "bank"),
    Institution("hsbc_us",     "HSBC US",                  "US", "plaid",    None, "hsbc",        "bank"),
    Institution("citizens",    "Citizens Bank",            "US", "plaid",    None, None,          "bank"),
    Institution("suntrust",    "SunTrust",                 "US", "plaid",    None, None,          "bank"),
    Institution("regions",     "Regions Bank",             "US", "plaid",    None, None,          "bank"),
    Institution("fifth_third", "Fifth Third Bank",         "US", "plaid",    None, None,          "bank"),
    Institution("huntington",  "Huntington Bank",          "US", "plaid",    None, None,          "bank"),
    Institution("key_bank",    "KeyBank",                  "US", "plaid",    None, None,          "bank"),
    Institution("sofi",        "SoFi",                     "US", "plaid",    None, None,          "neobank"),
    Institution("chime",       "Chime",                    "US", "plaid",    None, None,          "neobank"),

    # US investment platforms
    Institution("schwab",      "Charles Schwab",           "US", "plaid",    None, "schwab",      "investment"),
    Institution("fidelity_us", "Fidelity",                 "US", "plaid",    None, "fidelity",    "investment"),
    Institution("vanguard",    "Vanguard",                 "US", "plaid",    None, "vanguard",    "investment"),
    Institution("etrade",      "E*TRADE",                  "US", "plaid",    None, None,          "investment"),
    Institution("td_ameritrade","TD Ameritrade",           "US", "plaid",    None, "td",          "investment"),
    Institution("robinhood",   "Robinhood",                "US", "plaid",    None, None,          "investment"),
    Institution("merrill",     "Merrill Lynch",            "US", "plaid",    None, "bofa",        "investment"),
]

# ── Build lookup tables ────────────────────────────────────────────────────────

_ALL: list[Institution] = _CA + _US
_BY_ID: dict[str, Institution] = {inst.id: inst for inst in _ALL}


def get_institution(institution_id: str) -> Optional[Institution]:
    """Return the Institution for a given id, or None if unknown."""
    return _BY_ID.get(institution_id)


def search_institutions(query: str, country: str = None) -> list[Institution]:
    """
    Case-insensitive substring search on institution name.
    Optionally filter by country ("CA" or "US").
    """
    q = query.lower().strip()
    results = [
        inst for inst in _ALL
        if q in inst.name.lower()
        and (country is None or inst.country == country.upper())
    ]
    return results


def list_institutions(country: str = None) -> list[Institution]:
    """Return all institutions, optionally filtered by country."""
    if country:
        return [i for i in _ALL if i.country == country.upper()]
    return _ALL
