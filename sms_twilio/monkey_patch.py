import importlib

from odoo.addons.sms.models import sms_sms

# Patch the original SmsApi with our custom implementation
from odoo.addons.sms.tools import sms_api

from .tools.sms_api import CustomSmsApi

sms_api.SmsApi = CustomSmsApi
importlib.reload(sms_sms)
