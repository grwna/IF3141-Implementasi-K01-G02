# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.modules.registry import Registry

class ResUsers(models.Model):
    _inherit = 'res.users'

    user_role = fields.Selection([
        ('admin', 'Admin'),
        ('head', 'Head Divisi'),
        ('staf', 'Staf Bar & Kitchen'),
        ('finance', 'Divisi Finance'),
        ('owner', 'Owner'),
    ], string="Role", default='admin')
    two_factor_auth = fields.Boolean(string="Two Factor Authentication", default=False)
    notification_type = fields.Selection([
        ('none', 'None'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
    ], string="Notification Type", default='email')
    alert_stock_low = fields.Boolean(string="Alert Stock Low", default=True)
    password_last_updated = fields.Datetime(string="Password Last Updated", readonly=True)

    @classmethod
    def _login(cls, db, *args, **kwargs):
        uid = super()._login(db, *args, **kwargs)
        if uid:
            cls._log_successful_login(db, uid)
        return uid

    @classmethod
    def _log_successful_login(cls, db, uid):
        registry = Registry(db)
        with registry.cursor() as cr:
            env = api.Environment(cr, uid, {})
            user = env['res.users'].browse(uid)
            env['nuesara.activity.log'].sudo().log_action(
                action='login',
                model_name='Autentikasi',
                record_name=user.display_name,
                note='Pengguna berhasil login melalui autentikasi bawaan Odoo.',
            )
            cr.commit()

    def action_change_password(self):
        self.env['nuesara.activity.log'].sudo().log_action(
            action='change_password',
            model_name='Profil & Pengaturan',
            record_name=self.display_name,
            note='Pengguna membuka wizard ubah password.',
        )
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
        self.env['nuesara.activity.log'].sudo().log_action(
            action='logout',
            model_name='Profil & Pengaturan',
            record_name=self.display_name,
            note='Pengguna logout dari menu profil.',
        )
        # Redirects to the standard Odoo logout URL
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/session/logout',
            'target': 'self',
        }
