
from odoo import fields, models

class Settings(models.Model):
    _description = 'External Notifications settings model'
    _name = 'enotif.settings'

    process_notifications = fields.Boolean(default=True, string='Process notifications', help='Specifies whether the process notifications job is active"')                 
                 

    def set(self, field, value):
      data = {field:value}     
      record = self.search([], limit=1)
      if record:
        record.write(data)
      else:
        self.create(data)  
      
                       
    def get(self, key):
      record = self.env['enotif.settings'].search([], limit=1)
      if not record:
        self.create({})
      elif key in record:
        return record[key]
      return None
      
                        