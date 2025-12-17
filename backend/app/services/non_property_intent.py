import re

# Expand this list as you see more real user prompts
WEATHER_PATTERNS = [
    r"\bweather\b",
    r"\bforecast\b",
    r"\btemperature\b",
    r"\brain\b",
    r"\bsnow\b",
    r"\bwind\b",
    r"\bhumidity\b",
    r"\bstorm\b",
]

NON_PROPERTY_PATTERNS = [
    *WEATHER_PATTERNS,
    r"\btime\b",
    r"\bdate\b",
    r"\bwho are you\b",
    r"\bhelp\b",
    r"\bjoke\b",
    r"\bdefine\b",
    r"\bmeaning of\b",
    r"\btranslate\b",
    r"\bcalculator\b",
    r"\bwhat is\b",
]


def is_non_property_question(message: str) -> bool:
    text = (message or "").lower().strip()
    if not text:
        return False
    return any(re.search(p, text) for p in NON_PROPERTY_PATTERNS)


def is_weather_question(message: str) -> bool:
    text = (message or "").lower().strip()
    if not text:
        return False
    return any(re.search(p, text) for p in WEATHER_PATTERNS)
