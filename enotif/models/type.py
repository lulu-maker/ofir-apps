
from odoo import fields, models

class Type(models.Model):
    _description = 'External Notifications type model'
    _name = 'enotif.type'

    type = fields.Char(string='Type', help='Notification type')                 
    model_id = fields.Many2one('ir.model', ondelete='cascade', string='Model ID', help='ID number of the model that will be used to fetch notifications')               
    
    _sql_constraints = [
             ('unique_type', 'unique (type)', 'The notification type should be unique!')]
                 
                 
    def get_id(self, notification_type):
      return self.search([('type', '=', notification_type)], limit=1).id                 