import json
import os
import streamlit as st
from typing import Dict, Any, Optional

# Default language
DEFAULT_LANG = "en"

# Supported languages
LANGUAGES = {
    "en": "English",
    "zh_HK": "繁體中文 (廣東話)",
    "zh_TW": "繁體中文 (台灣)"
}

# Cache translations to avoid repeated file reads
_translation_cache: Dict[str, Dict[str, Any]] = {}

def load_translations(lang_code: str) -> Dict[str, Any]:
    """Load translation JSON for a given language code."""
    if lang_code in _translation_cache:
        return _translation_cache[lang_code]
    
    file_path = os.path.join("locales", lang_code, "translations.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            translations = json.load(f)
        _translation_cache[lang_code] = translations
        return translations
    except FileNotFoundError:
        # Fallback to English if file missing
        if lang_code != DEFAULT_LANG:
            return load_translations(DEFAULT_LANG)
        # If even English missing, return empty dict
        return {}

def get_translation(lang_code: str, key: str, default: Optional[str] = None) -> str:
    """
    Get a translation string for a given key.
    Keys use dot notation: e.g., "common.welcome", "exercises.1.name".
    """
    translations = load_translations(lang_code)
    parts = key.split(".")
    value = translations
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            break
    if isinstance(value, str):
        return value
    # If not found, return default or the key itself
    return default if default is not None else key

def get_text(key: str, **kwargs) -> str:
    """
    Get translated text with optional variable substitution.
    Usage: get_text("common.welcome", name="John") will replace {name} in the string.
    """
    lang = st.session_state.get("language", DEFAULT_LANG)
    text = get_translation(lang, key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            # If formatting fails, return as is
            pass
    return text

def get_language_selector():
    """Return a language selector widget."""
    return st.selectbox(
        label=get_text("common.language_selector"),
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        key="language_selector"
    )
