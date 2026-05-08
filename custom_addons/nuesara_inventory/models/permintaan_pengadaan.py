# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PermintaanPengadaan(models.Model):
    _name = 'permintaan.pengadaan'
    _description = 'Permintaan Pengadaan ke Supplier'
    _order = 'tanggal_permintaan desc, id desc'

    name = fields.Char(string="Nomor Permintaan", default="Draft", readonly=True, copy=False)
    tanggal_permintaan = fields.Date(string="Tanggal Permintaan", default=fields.Date.today, required=True)
    supplier_id = fields.Many2one(
        'res.partner',
        string="Supplier",
        domain=[('is_company', '=', True)],
        required=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Terkirim'),
    ], string="Status", default='draft', required=True)
    tanggal_kirim = fields.Datetime(string="Tanggal Kirim", readonly=True)
    dokumen_permintaan = fields.Text(string="Dokumen Permintaan", readonly=True)
    line_ids = fields.One2many('permintaan.pengadaan.line', 'permintaan_id', string="Daftar Bahan")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record.name = "REQ/%s/%04d" % (
                fields.Date.to_string(record.tanggal_permintaan).replace('-', ''),
                record.id,
            )
        return records

    @api.constrains('supplier_id')
    def _check_registered_supplier(self):
        for record in self:
            if record.supplier_id and not record.supplier_id.is_company:
                raise ValidationError("Supplier harus dipilih dari daftar perusahaan terdaftar.")

    def action_send_to_supplier(self):
        for record in self:
            if record.state != 'draft':
                continue
            if not record.line_ids:
                raise ValidationError("Minimal satu bahan baku harus dimasukkan ke permintaan.")
            for line in record.line_ids:
                if line.jumlah <= 0:
                    raise ValidationError("Jumlah permintaan untuk %s harus lebih dari 0." % line.bahan_id.display_name)

            record.write({
                'state': 'sent',
                'tanggal_kirim': fields.Datetime.now(),
                'dokumen_permintaan': record._generate_document_text(),
            })
            self.env['nuesara.activity.log'].sudo().log_action(
                action='send',
                model_name=record._description,
                record_name=record.name,
                note="Dokumen permintaan pengadaan dibuat dan ditandai terkirim ke supplier %s." % record.supplier_id.display_name,
            )
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Permintaan Pengadaan',
                    'message': 'Dokumen permintaan pengadaan berhasil dibuat dan ditandai terkirim ke supplier.',
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                },
            }
        return True

    def _generate_document_text(self):
        self.ensure_one()
        lines = [
            "DOKUMEN PERMINTAAN PENGADAAN",
            "Nomor: %s" % self.name,
            "Tanggal Permintaan: %s" % self.tanggal_permintaan,
            "Supplier: %s" % self.supplier_id.display_name,
            "",
            "Daftar Bahan:",
        ]
        satuan_labels = dict(self.env['bahan.baku']._fields['satuan'].selection)
        for idx, line in enumerate(self.line_ids, start=1):
            lines.append(
                "%s. %s - %.2f %s" % (
                    idx,
                    line.bahan_id.display_name,
                    line.jumlah,
                    satuan_labels.get(line.satuan, line.satuan or ''),
                )
            )
        return "\n".join(lines)


class PermintaanPengadaanLine(models.Model):
    _name = 'permintaan.pengadaan.line'
    _description = 'Line Permintaan Pengadaan'

    permintaan_id = fields.Many2one('permintaan.pengadaan', string="Permintaan", required=True, ondelete='cascade')
    bahan_id = fields.Many2one('bahan.baku', string="Bahan Baku", required=True)
    jumlah = fields.Float(string="Jumlah Diminta", required=True)
    satuan = fields.Selection(related='bahan_id.satuan', string="Satuan", readonly=True)

    @api.constrains('jumlah')
    def _check_positive_quantity(self):
        for record in self:
            if record.jumlah <= 0:
                raise ValidationError("Jumlah diminta harus lebih dari 0.")
