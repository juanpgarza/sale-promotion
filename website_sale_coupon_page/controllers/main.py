# Copyright 2021 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import http
from odoo.http import request


class WebsiteSale(http.Controller):
    @http.route(["""/promotions"""], type="http", auth="public", website=True)
    def promotion(self, **post):
        all_promos = (
            request.env["coupon.program"]
            .sudo()
            .search(
                [
                    ("is_published", "=", True),
                    "|",
                    ("website_id", "=", False),
                    ("website_id", "=", request.env.context.get("website_id")),
                ]
            )
        )
        values = {"promos": []}
        for promo in all_promos:
            if promo._is_valid_partner(request.env.user.partner_id):
                values["promos"].append(
                    {
                        "id": promo.id,
                        "image_1920": promo.image_1920,
                        "public_name": promo.public_name,
                    }
                )
        return request.render("website_sale_coupon_page.promotion_layout", values)
