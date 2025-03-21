# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form

from odoo.addons.coupon_multi_gift.tests.coupon_multi_gift_case import (
    CouponMultiGiftCase,
)


class TestSaleCouponMultiGift(CouponMultiGiftCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_1
            line_form.product_uom_qty = 2
        cls.sale = sale_form.save()

    def test_sale_coupon_test_multi_gift(self):
        """As we fulfill the proper product qties, we get the proper free product"""
        line = self.sale.order_line
        self.sale.recompute_coupon_lines()
        # As set up, we should one discount line for every reward line in the promotion
        discount_line_product_2 = self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_2 and x.is_reward_line
        )
        discount_line_product_3 = self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_3 and x.is_reward_line
        )
        self.assertEqual(2, discount_line_product_2.product_uom_qty)
        self.assertEqual(3, discount_line_product_3.product_uom_qty)
        self.assertEqual(0, discount_line_product_2.price_reduce)
        self.assertEqual(0, discount_line_product_3.price_reduce)
        self.assertEqual(60, discount_line_product_2.price_unit)
        self.assertEqual(70, discount_line_product_3.price_unit)
        line_form = Form(line, view="sale.view_order_line_tree")
        line_form.product_uom_qty = 7
        line_form.save()
        self.sale.recompute_coupon_lines()
        discount_line_product_2 = self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_2 and x.is_reward_line
        )
        discount_line_product_3 = self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_3 and x.is_reward_line
        )
        # The promotion will only be applied once whatever the min quantity
        self.assertEqual(2, discount_line_product_2.product_uom_qty)
        self.assertEqual(3, discount_line_product_3.product_uom_qty)
        self.assertEqual(0, discount_line_product_2.price_reduce)
        self.assertEqual(0, discount_line_product_3.price_reduce)
        # Now it can't be applied anymore so the discount lines will dissapear
        line_form.product_uom_qty = 1
        line_form.save()
        self.sale.recompute_coupon_lines()
        discount_line = self.sale.order_line.filtered("is_reward_line")
        # The discount goes away
        self.assertFalse(bool(discount_line))
        # Optional rewards
        line_form.product_uom_qty = 2
        line_form.save()
        reward_line_options = {
            self.coupon_program.coupon_multi_gift_ids[1].id: self.product_4.id
        }
        self.sale.with_context(
            reward_line_options=reward_line_options
        ).recompute_coupon_lines()
        discount_line_product_2 = self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_2 and x.is_reward_line
        )
        discount_line_product_3 = self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_3 and x.is_reward_line
        )
        discount_line_product_4 = self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_4 and x.is_reward_line
        )
        self.assertEqual(2, discount_line_product_2.product_uom_qty)
        self.assertEqual(3, discount_line_product_4.product_uom_qty)
        self.assertFalse(discount_line_product_3)
        # The original gift options are kept
        self.sale.recompute_coupon_lines()
        discount_line_product_4 = self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_4 and x.is_reward_line
        )
        self.assertEqual(3, discount_line_product_4.product_uom_qty)
        self.assertEqual(
            discount_line_product_4.multi_gift_reward_line_id_option_product_id,
            self.product_4,
            "The product should be kept after updating recomputing the promotions",
        )
        # The regular options are ok as well
        discount_line_product_2 = self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_2 and x.is_reward_line
        )
        discount_line_product_3 = self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_3 and x.is_reward_line
        )
        self.assertEqual(2, discount_line_product_2.product_uom_qty)
        self.assertEqual(3, discount_line_product_4.product_uom_qty)

    def test_sale_coupon_multi_gift_count(self):
        """We have to count the orders in a different manner than the core method"""
        self.assertEqual(self.coupon_program.order_count, 0)
        self.sale.recompute_coupon_lines()
        self.sale.action_confirm()
        self.coupon_program._compute_order_count()
        self.assertEqual(self.coupon_program.order_count, 1)
        # Let's place a second order
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product_1
            line_form.product_uom_qty = 2
        sale_2 = sale_form.save()
        sale_2.recompute_coupon_lines()
        sale_2.action_confirm()
        self.coupon_program._compute_order_count()
        self.assertEqual(self.coupon_program.order_count, 2)
        # We should get our order when we click in the orders smart button
        action_domain = self.coupon_program.action_view_sales_orders()["domain"]
        self.assertEqual(
            self.env["sale.order"].search(action_domain), self.sale + sale_2
        )
