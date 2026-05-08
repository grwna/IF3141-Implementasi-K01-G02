# -*- coding: utf-8 -*-
{
    'name': "Nuesara Inventory",
    'summary': "Inventory management for Bar & Kitchen - IF3141 Sistem Informasi",
    'description': """
        Custom Odoo module for hospitality inventory tracking including:
        - Master Data Bahan Baku
        - Stok Masuk (Supplier deliveries)
        - Stok Keluar (Daily usage)
        - Stock reporting
    """,
    'author': "G02-K01",
    'category': 'Inventory',
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/bahan_baku_views.xml',
        'views/stok_masuk_views.xml',
        'views/stok_keluar_views.xml',
        'views/laporan_stok_views.xml',
        'views/permintaan_pengadaan_views.xml',
        'views/activity_log_views.xml',
        'views/res_users_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
}
