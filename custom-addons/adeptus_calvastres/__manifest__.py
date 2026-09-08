{
    'name': 'Adeptus Calvastres',
    'version': '1.0',
    'category': 'Association',
    'summary': 'Association member, game and finance management',
    'depends': [
        'base'
    ],
    'data': [
    'security/ir.model.access.csv',
    'views/booking_views.xml',
    'views/partner_views.xml',
    'views/menus.xml',
    ],
    'installable': True,
    'application': True,
}