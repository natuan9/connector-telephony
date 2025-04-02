import logging
import re

from odoo.exceptions import UserError

from odoo.addons.sms.tools.sms_api import SmsApi

_logger = logging.getLogger(__name__)

try:
    from twilio.base.exceptions import TwilioRestException
except ImportError:
    _logger.error("Cannot import twilio", exc_info=True)


class CustomSmsApi(SmsApi):
    def __init__(self, env, account=None):
        super().__init__(env, account)
        self.twilio_account = self._get_twilio_sms_account()

    def _get_twilio_sms_account(self):
        return self.env["iap.account"].search(
            [("provider", "=", "twilio"), ("service_name", "=", "sms")]
        )

    def _send_sms_with_twilio(self, number, message, sms_uuid):
        if not number:
            return "wrong_number_format"
        try:
            client = self.twilio_account.get_twilio_client(
                production=self.twilio_account.twilio_production_env
            )
            from_phone = self.twilio_account.twilio_number_id
            from_number = "+" + re.sub("[^0-9]", "", from_phone.phone_number)
            number = "+" + re.sub("[^0-9]", "", number)
            client.messages.create(to=number, from_=from_number, body=message)

            sms = self.env["sms.sms"].search([("uuid", "=", sms_uuid)])
            if sms:
                sms.error_detail = "Sent via Twilio"

        except TwilioRestException as e:
            sms = self.env["sms.sms"].search([("uuid", "=", sms_uuid)])
            if sms:
                sms.error_detail = e.msg
            raise UserError(e.msg) from e
        return "success"

    def _send_sms_batch(self, messages, delivery_reports_url=False):
        if self.twilio_account:
            results = []

            for message in messages:
                content = message["content"]
                for number_info in message["numbers"]:
                    uuid = number_info["uuid"]
                    number = number_info["number"]
                    try:
                        state = self._send_sms_with_twilio(number, content, uuid)
                    except UserError as e:
                        state = "error"
                        _logger.error(f"Failed to send SMS to {number}: {e}")

                    results.append({"uuid": uuid, "state": state, "credit": 0})
            return results
        else:
            return super()._send_sms_batch(messages, delivery_reports_url)
