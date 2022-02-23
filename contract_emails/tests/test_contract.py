from datetime import date, timedelta

from odoo import fields
from odoo.addons.contract.tests.test_contract import TestContractBase


def is_mail(message):
    return message.subtype_id.get_xml_id().values()[0] == "mail.mt_comment"


def get_model(object):
    return object.env['ir.model'].search([("model", "=", object._name)])


class ContractTemplateMailGenerator(TestContractBase):

    def create_mt(self, **kwargs):
        return self.env["mail.template"].create({
            "model_id": kwargs.get("model_id", get_model(self.contract).id),
            "name": kwargs.get("name", "Test template name"),
            "subject": kwargs.get("subject", "${object.name}"),
            "body_html": kwargs.get("body_html", u"Test body"),
            "user_signature": False,
        })

    def create_contract(self, date, template=None, **kwargs):
        date = fields.Date.to_string(date)
        kwargs["recurring_next_date"] = date
        kwargs["contract_template_id"] = (template or self.template).id
        kwargs["date_start"] = date
        return self.contract.copy(kwargs)

    def create_gen(self, interval_number, text=u"Test body", **kwargs):
        values = {
            "contract_id": self.template.id,
            "mail_template_id": self.create_mt(body_html=text).id,
            "interval_number": interval_number,
            "interval_type": "daily",
        }
        values.update(kwargs)
        return self.env['contract_emails.planned_mail_generator'].create(values)

    def test_cron(self):
        "Emails planned in the past must be sent"
        pmt_model = self.env["contract_emails.planned_mail_generator"]

        self.create_gen(0, text=u"Mail at contract start", max_delay_days=10)
        self.create_gen(6, text=u"Mail after 6 days", max_delay_days=10)
        g3 = self.create_gen(25, text=u"Mail after 25 days", max_delay_days=10)

        today = date.today()
        c1 = self.create_contract(today)
        c2 = self.create_contract(today - timedelta(days=7))
        c3 = self.create_contract(today - timedelta(days=30))
        c4 = self.create_contract(today - timedelta(days=30),
                                  date_end=fields.Date.to_string(today))

        pmt_model.cron_send_planned_mails()

        # Mails send from contracts in emission order
        c1_mails = c1.message_ids.filtered(is_mail).sorted("id")
        c2_mails = c2.message_ids.filtered(is_mail).sorted("id")
        c3_mails = c3.message_ids.filtered(is_mail).sorted("id")
        c4_mails = c4.message_ids.filtered(is_mail).sorted("id")

        self.assertEqual(
            c1_mails.mapped("body"),
            ["<p>Mail at contract start</p>"])
        self.assertEqual(
            c2_mails.mapped("body"),
            ["<p>Mail at contract start</p>", "<p>Mail after 6 days</p>"])
        self.assertEqual(
            c3_mails.mapped("body"),
            ["<p>Mail after 25 days</p>"])  # Other mails are too old
        self.assertFalse(c4_mails)

        # Check messages are not sent again and again
        pmt_model.cron_send_planned_mails()

        self.assertEqual(c1.message_ids.filtered(is_mail), c1_mails)
        self.assertEqual(c2.message_ids.filtered(is_mail), c2_mails)
        self.assertEqual(c3.message_ids.filtered(is_mail), c3_mails)
