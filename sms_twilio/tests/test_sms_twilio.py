from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestSmsTwilio(BaseCommon):
    @classmethod
    def setUpClass(cls):
        res = super().setUpClass()
        cls.iap_account = cls.env["iap.account"].create(
            {
                "provider": "twilio",
                "service_id": cls.env.ref("sms.iap_service_sms").id,
                "twilio_test_account_sid": "test",
                "twilio_test_auth_token": "test",
                "twilio_account_sid": "test",
                "twilio_auth_token": "test",
                "twilio_production_env": False,
            }
        )

        return res

    def test_compute_balance_twilio(self):
        mock_balance = MagicMock()
        mock_balance.currency = "USD"
        mock_balance.balance = "100.00"

        mock_client = MagicMock()
        mock_client.api.balance.fetch.return_value = mock_balance

        with patch.object(
            self.iap_account.__class__, "get_twilio_client", return_value=mock_client
        ):
            self.iap_account._compute_balance_twilio()

            self.assertEqual(self.iap_account.twilio_balance_account, "USD: 100.00")
            mock_client.api.balance.fetch.assert_called_once()

    def test_retrieve_number_iap_twilio_account(self):
        mock_phone_numbers = [
            type(
                "PhoneNumber",
                (object,),
                {
                    "sid": "PN1234567890",
                    "phone_number": "+1234567890",
                    "friendly_name": "Test Number",
                    "capabilities": {"voice": True, "sms": True, "mms": False},
                },
            )()
        ]

        with patch(
            "twilio.rest.Client.incoming_phone_numbers"
        ) as mock_incoming_phone_numbers:
            mock_incoming_phone_numbers.list.return_value = mock_phone_numbers
            self.iap_account.retrieve_phone_numbers()

            phone_number = self.env["twilio.phone.number"].search(
                [("name", "=", "Test Number")]
            )
            self.assertEqual(len(phone_number), 1)
            self.assertEqual(phone_number.phone_number, "+1234567890")
            self.assertEqual(phone_number.sid, "PN1234567890")

            test_number = self.env["twilio.phone.number"].search(
                [("name", "=", "TEST Phone")]
            )
            self.assertEqual(len(test_number), 1)
            self.assertEqual(test_number.phone_number, "+15005550006")

    def test_onchange_test_number_with_form(self):
        mock_balance = MagicMock()
        mock_balance.currency = "USD"
        mock_balance.balance = "100.00"

        mock_client = MagicMock()
        mock_client.api.balance.fetch.return_value = mock_balance

        with patch.object(
            self.iap_account.__class__, "get_twilio_client", return_value=mock_client
        ):
            test_number = self.env["twilio.phone.number"].create(
                {
                    "name": "Test Phone",
                    "sid": "test",
                    "phone_number": "+12345678900",
                    "has_sms_enabled": True,
                }
            )
            with Form(self.iap_account) as form:
                form.twilio_number_id = test_number
                with self.assertRaises(UserError):
                    form.twilio_production_env = True
