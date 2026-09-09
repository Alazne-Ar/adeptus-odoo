{
    'name': 'Adeptus Calvastres',
    'version': '1.0',
    'category': 'Association',
    'summary': 'Association member, game and finance management',
    'depends': ['base'],
    'application': True,

    'data': [
    'security/ir.model.access.csv',
    'views/adeptus_partner_views.xml',
    'views/adeptus_table_views.xml',
    'views/adeptus_booking_views.xml',
    'views/adeptus_menu.xml',
    ],

    'installable': True,
}