#
# (c) Copyright Ascensio System SIA 2025
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

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
    return [_("Document"), _("Spreadsheet"), _("Presentation")]


def remove_extension(name):
    last_dot_index = name.rfind(".")

    if last_dot_index != -1:
        return name[:last_dot_index]
    else:
        return name


def get_extension_by_name(name):
    return name[name.rfind(".") + 1 :].lower()


def get_format_by_extension(name):
    with open(onlyoffice_docs_formats_path, "r") as onlyoffice_docs_formats:
        formats = json.load(onlyoffice_docs_formats)
    for format in formats:
        if name in format["name"]:
            return format


def get_extension_by_description(description):
    description = description.casefold()
    if description == _("Document").casefold():
        return "docx"
    if description == _("Spreadsheet").casefold():
        return "xlsx"
    if description == _("Presentation").casefold():
        return "pptx"
    if description == _("PDF form").casefold():
        return "pdf"

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
