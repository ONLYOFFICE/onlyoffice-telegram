import json
import os

from app.utils.lang_utils import _
from config import PROJECT_ROOT

onlyoffice_docs_formats_path = os.path.join(
    PROJECT_ROOT,
    "static",
    "assets",
    "document-formats",
    "onlyoffice-docs-formats.json",
)


def get_format_descriptions():
    return [
        _("Document"),
        _("Spreadsheet"),
        _("Presentation"),
        _("PDF form"),
    ]


def remove_extension(name):
    last_dot_index = name.rfind(".")

    if last_dot_index != -1:
        return name[:last_dot_index]
    else:
        return name


def get_extension_by_name(name):
    return name[name.rfind(".") + 1 :].lower()


def get_format_by_mime(mime):
    with open(onlyoffice_docs_formats_path, "r") as onlyoffice_docs_formats:
        formats = json.load(onlyoffice_docs_formats)
    for format in formats:
        if mime in format["mime"]:
            return format


def get_mime_by_format_description(format):
    format = format.casefold()
    if format == _("Document").casefold():
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if format == _("Spreadsheet").casefold():
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if format == _("Presentation").casefold():
        return (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
    if format == _("PDF form").casefold():
        return "application/pdf"

    return None


def get_file_by_file_type(file_type, lang="default"):
    templates_path = os.path.join(
        PROJECT_ROOT, "static", "assets", "document-templates"
    )

    template = os.path.join(
        templates_path,
        lang
        if os.path.exists(os.path.join(templates_path, lang, "new." + file_type))
        else "default",
        "new." + file_type,
    )

    with open(template, "rb") as file:
        return file.read()
