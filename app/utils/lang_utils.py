from aiogram.utils.i18n import I18n

from config import (
    I18N_DOMAIN,
    I18N_PATH,
)

i18n = I18n(path=I18N_PATH, domain=I18N_DOMAIN)
_ = i18n.gettext
__ = i18n.lazy_gettext
