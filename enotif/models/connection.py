
from odoo import fields, models

class Connection(models.Model):
    _description = 'External Notifications connection model'
    _name = 'enotif.connection'
    
    model_id = fields.Many2one('ir.model', ondelete='cascade', string='Model ID', help='ID number of the model that will be used to fetch notifications')               
    
        