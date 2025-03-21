# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class Coupon(models.Model):
    _inherit = "coupon.coupon"

    def _check_coupon_code(self, order_date, partner_id, **kwargs):
        order = kwargs.get("order")
        message = super(Coupon, self)._check_coupon_code(
            order_date, partner_id, **kwargs
        )
        if message:
            return message
        if self.program_id.reward_type == "multiple_of" and (
            not order._is_reward_in_order_lines(self.program_id)
            and self.program_id.force_rewarded_product
        ):
            message = {
                "error": _(
                    "The reward products should be in the sales order lines to "
                    "apply the discount."
                )
            }
        return message
