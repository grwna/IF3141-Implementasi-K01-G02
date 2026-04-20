# -*- coding: utf-8 -*-
from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    user_role = fields.Selection([
        ('admin', 'Admin'),
        ('head', 'Head Divisi'),
        ('staf', 'Staf Bar & Kitchen'),
        ('finance', 'Divisi Finance'),
    ], string="Role", default='admin')
    two_factor_auth = fields.Boolean(string="Two Factor Authentication", default=False)
    notification_type = fields.Selection([
        ('none', 'None'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
    ], string="Notification Type", default='email')
    alert_stock_low = fields.Boolean(string="Alert Stock Low", default=True)
    password_last_updated = fields.Datetime(string="Password Last Updated", readonly=True)

    def action_change_password(self):
        # Opens the standard Odoo "Change Password" wizard for this user.
        return {
            'name': 'Change Password',
            'type': 'ir.actions.act_window',
            'res_model': 'change.password.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_user_ids': [(4, self.id)]},
        }

    def action_logout(self):
        # Redirects to the standard Odoo logout URL
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/session/logout',
            'target': 'self',
        }
