import json
import os
import streamlit as st

DEFAULT_LANG = "en"
LANGUAGES = {
    "en": "English",
    "zh_HK": "繁體中文 (廣東話)",
    "zh_TW": "繁體中文 (台灣)"
}

_translation_cache = {}

def load_translations(lang_code):
    if lang_code in _translation_cache:
        return _translation_cache[lang_code]
    
    file_path = os.path.join("locales", lang_code, "translations.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            translations = json.load(f)
        _translation_cache[lang_code] = translations
        return translations
    except FileNotFoundError:
        if lang_code != DEFAULT_LANG:
            return load_translations(DEFAULT_LANG)
        return {}

def get_translation(lang_code, key, default=None):
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
    return default if default is not None else key

def get_text(key, **kwargs):
    lang = st.session_state.get("language", DEFAULT_LANG)
    text = get_translation(lang, key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text

def get_language_selector():
    return st.selectbox(
        label=get_text("common.language_selector"),
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        key="lang_selector"
    )
