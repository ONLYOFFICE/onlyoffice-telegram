#
# (c) Copyright Ascensio System SIA 2026
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

"""Smoke: the data the bot depends on (submodules, locales) is present and usable."""

import pytest

from app.utils.file_utils import (
    get_extension_by_description,
    get_extension_by_name,
    get_file_by_file_type,
    get_format_by_extension,
)
from app.utils.lang_utils import _, i18n

# Known translation defects, tracked outside the repository. strict=True: when a translation
# is fixed the test starts passing and xfail turns red — then remove the entry here.
KNOWN_ISSUE = pytest.mark.xfail(strict=True, reason="known translation issue, tracked separately")


def locales(known_broken=()):
    return [pytest.param(lang, marks=KNOWN_ISSUE) if lang in known_broken else lang
            for lang in sorted(i18n.available_locales)]  # fmt: skip


@pytest.mark.parametrize("ext", ["docx", "xlsx", "pptx", "pdf"])
def test_creatable_formats_are_editable_and_convertible(ext):
    f = get_format_by_extension(ext)
    assert f is not None
    assert "edit" in f["actions"]
    assert f["convert"], f"{ext} must have conversion targets"


def test_unknown_extension_is_not_supported():
    assert get_format_by_extension("definitely-not-a-format") is None


def test_extension_parsing_is_case_insensitive():
    assert get_extension_by_name("My.Report.DOCX") == "docx"


@pytest.mark.parametrize("ext", ["docx", "xlsx", "pptx"])
def test_blank_templates_exist_and_fall_back_to_default(ext):
    default = get_file_by_file_type(ext, "default")
    assert default.startswith(b"PK"), "templates are OOXML zip files"
    # A language without its own template folder must fall back to "default".
    assert get_file_by_file_type(ext, "xx") == default


@pytest.mark.parametrize("lang", sorted(i18n.available_locales))
def test_every_locale_has_a_template_folder(lang):
    assert get_file_by_file_type("docx", lang).startswith(b"PK")


def test_all_bot_languages_are_compiled():
    assert {"de", "en", "es", "fr", "it", "ja", "pt", "ru", "zh"} <= set(i18n.available_locales)


@pytest.mark.parametrize("lang", locales(known_broken={"pt"}))
def test_menu_button_translations_match_their_lowercase_filters(lang):
    # Handlers match buttons with F.text.lower() == __("create") etc. while the buttons are
    # rendered from _("Create"). The two msgids must stay in sync in every language,
    # otherwise the menu silently stops working in that language.
    pairs = [("Create", "create"), ("Open", "open"), ("🔄 Convert", "🔄 convert"), ("⬅️ Back", "⬅️ back"),
             ("❌ Cancel", "❌ cancel")]  # fmt: skip
    for button, filter_text in pairs:
        assert _(button, locale=lang).lower() == _(filter_text, locale=lang), (lang, button)


@pytest.mark.parametrize("lang", locales(known_broken={"zh"}))
def test_create_menu_descriptions_map_to_extensions(lang):
    with i18n.use_locale(lang):
        assert get_extension_by_description(_("Document")) == "docx"
        assert get_extension_by_description(_("Spreadsheet")) == "xlsx"
        assert get_extension_by_description(_("Presentation")) == "pptx"
