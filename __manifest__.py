{
    'name': 'Rental product',
    'category': 'Sale',
    'summary': 'Define products as rental products',
    'version': '10.0.1.0.0',
    'description': """Rental products have a fixed deposit and recurring price, displayed on the product page""",
    'author': "Commown SCIC SAS",
    'license': "AGPL-3",
    'website': "https://commown.fr",
    'depends': ['website_sale'],
    'external_dependencies': {},
    'data': [
        'views/product_template.xml',
        'views/website_portal_sale_templates.xml',
    ],
    'installable': True,
}
