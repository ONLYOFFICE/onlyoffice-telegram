import os

from config import PROJECT_ROOT

from .format_utils import get_supported_formats


def get_all_mime():
    return [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/pdf",
    ]


def get_file_type_by_name(name):
    return name[name.rfind(".") + 1 :].lower()


def get_document_type_by_name(name):
    file_type = get_file_type_by_name(name)
    for format in get_supported_formats():
        if format.file_type == file_type:
            return format.document_type

    return None


def get_document_type_by_format(format):
    if format == "document":
        return "word"
    if format == "spreadsheet":
        return "cell"
    if format == "presentation":
        return "slide"
    if format == "form":
        return "pdf"

    return None


def get_file_type_by_format(format):
    if format == "document":
        return "docx"
    if format == "spreadsheet":
        return "xlsx"
    if format == "presentation":
        return "pptx"
    if format == "form":
        return "pdf"

    return None


def get_file_by_file_type(file_type, lang="en"):
    locale_path = {
        "az": "az-Latn-AZ",
        "bg": "bg-BG",
        "cs": "cs-CZ",
        "de": "de-DE",
        "el": "el-GR",
        "en-gb": "en-GB",
        "en": "en-US",
        "es": "es-ES",
        "fr": "fr-FR",
        "it": "it-IT",
        "ja": "ja-JP",
        "ko": "ko-KR",
        "lv": "lv-LV",
        "nl": "nl-NL",
        "pl": "pl-PL",
        "pt-br": "pt-BR",
        "pt": "pt-PT",
        "ru": "ru-RU",
        "sk": "sk-SK",
        "sv": "sv-SE",
        "uk": "uk-UA",
        "vi": "vi-VN",
        "zh": "zh-CN",
    }
    locale = locale_path.get(lang)
    if locale is None:
        locale = locale_path.get("en")

    file_path = os.path.join(
        PROJECT_ROOT,
        "static",
        "assets",
        "document_templates",
        locale,
        "new." + file_type,
    )
    file = open(
        file_path,
        "rb",
    )
    try:
        file_data = file.read()
        return file_data
    finally:
        file.close()


def get_supported_convert_formats(name):
    file_type = get_file_type_by_name(name)
    for format in get_supported_formats():
        if format.file_type == file_type:
            return format.convert_to

    return None
