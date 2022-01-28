import math
import time
import logging
import requests
from odoo import fields, models
from datetime import datetime, timedelta
from traceback import format_exception_only

MAX_NUMBER_OF_RECORDS_TO_PROCESS = 10
MAX_EXECUTION_TIME = 50

_logger = logging.getLogger(__name__)

_cron_scheduled = False
_error_text = ''

class Notification(models.Model):
    _description = 'Update WooCommerce notification model'
    _name = 'enotif.notification'
    
    type_id = fields.Many2one('enotif.type', ondelete='cascade', string='Type ID', help='Type ID')    
    item_id = fields.Integer(string='Item ID', help='Item ID')    
    priority = fields.Integer(string='Priority', default=5, help='The priority of the notification, as an integer: 0 means higher priority, 10 means lower priority.')
    
    _sql_constraints = [
             ('unique_notification_key', 'unique (type_id, item_id)', 'A notification with the same type_id, item_id already exists')]

         
    def fetch_notifications(self):
      global _cron_scheduled
            
      models = self.env['enotif.connection'].search([]).mapped('model_id')
      if models:
        for model_id in models:
          self.env[model_id.model].fetch_notifications()
      
      count = self.search_count([])
      if count > 0:  
        self.schedule_process_data_cron_job()
           
      _cron_scheduled = False   
      

    def save_notifications(self, notifications, priority=5):            
      record = self.search([], limit=1)
      for type_id, item_ids in notifications.items():
        if record.id:
          ids = [str(id) if id == 0 else id for id in item_ids]
          duplicate_ids = set(self.search([('type_id','=',type_id),('item_id','in',ids)]).mapped('item_id'))
          item_ids = [id for id in item_ids if id not in duplicate_ids]  
        if item_ids:
          data = [];
          for id in item_ids:
            data.append({'type_id': type_id, 'item_id': id, 'priority':priority});    
          self.create(data);
 

    def save_notifications_for_type(self, type, item_ids, priority=5):
      type_id = self.env['enotif.type'].get_id(type)
      if type_id:
        self.save_notifications({type_id:item_ids}, priority)
 
          
    def process_data(self):

      if not self.env['enotif.settings'].get('process_notifications'):
        return
    
      models = {}
      type_by_id = {}                  
      records = self.search([], order='priority,type_id,item_id desc', limit=MAX_NUMBER_OF_RECORDS_TO_PROCESS)
      for r in records:      
        models.setdefault(r.type_id.model_id.model, []).append({'type_id': r.type_id.id, 'item_id': r.item_id})
        type_by_id[r.type_id.id] = r.type_id.type
        
      start_time = time.time()
      
      for m_name, items in models.items():
  
        Model = self.env[m_name]
    
        types = {}
        for item in items:
          types.setdefault(item['type_id'], []).append(item['item_id'])              
      
        for type_id, item_ids in types.items():
        
          notification_type = type_by_id[type_id]
          
          end_time = time.time()
          if end_time - start_time > MAX_EXECUTION_TIME:           
            break 
                                       
          try:          
            processed_ids = Model.process_notifications(notification_type, item_ids)
            self.delete_processed_notifications(type_id, processed_ids);
          except Exception as e:
            _logger.error("ERROR: External Notifications module cannot pocess notifications for type: %s \n item_ids: %s  \n error text: %s", notification_type, item_ids, format_exception_only(type(e), e))
       
        else:
            continue
        break                                
 
 
    def get_notifications_progress(self):
     
      items = []
      
      types = {} 
      type_by_id = {}                   
      records = self.search([], order='priority,type_id')
      for r in records:      
        types.setdefault(r.type_id.id, []).append(r.item_id)
        type_by_id[r.type_id.id] = r.type_id.type
        
      for type_id, item_ids in types.items():
        notification_type = type_by_id[type_id]
        number = len(item_ids)
        ids_str = ','.join(str(e) for e in item_ids)
        if number > 10:
          ids_str = ','.join(str(e) for e in item_ids[0:10]) + '...'
        if number > MAX_NUMBER_OF_RECORDS_TO_PROCESS:
          time_seconds = int(math.ceil(number / MAX_NUMBER_OF_RECORDS_TO_PROCESS)) * 3 * 60
          time = self.display_time(time_seconds)
        else:
          time = "3 minutes"
                       
        items.append({'type_id':type_id, 'type':notification_type, 'number':number, 'item_ids_str':ids_str, 'time':time})
      
      process_notifications = 1 if self.env['enotif.settings'].get('process_notifications') else 0
      
      return {'items':items, 'itemIdsByTypeId':types, 'process_notifications':process_notifications}


    def display_time(self, seconds):
      result = []

      intervals = (
          ('days', 86400),    # 60 * 60 * 24
          ('hours', 3600),    # 60 * 60
          ('minutes', 60)
          )

      for name, count in intervals:
          value = seconds // count
          if value:
              seconds -= value * count
              if value == 1:
                  name = name.rstrip('s')
              result.append("{} {}".format(value, name))
      return ', '.join(result)
      
      
    def delete_processed_notifications(self, type_id, item_ids):
      ids = [str(id) if id == 0 else id for id in item_ids] # cannot find item with id 0 only works with string type '0'
      self.search([('type_id','=',type_id),('item_id','in',ids)]).unlink()
 
               
    def toggle_state(self):
      Settings = self.env['enotif.settings']
      new_state = not Settings.get('process_notifications')
      Settings.set('process_notifications', new_state)
      if new_state:
        count = self.search_count([])
        if count > 0:
          self.schedule_process_data_cron_job()
      else:
        self.stop_process_data_cron_job()    
      return new_state
 

    def set_error_text(self, text):
       global _error_text
       _error_text = text;
         
         
    def get_error_text(self):
       global _error_text    
       return _error_text                
                  
                  
    def schedule_fetch_notifications_cron_job(self):
      global _cron_scheduled
      
      if _cron_scheduled:
        return       
      _cron_scheduled = True
                
      cron_record = self.env.ref('enotif.enotif_cron_fetch_notifications')
      if not cron_record:
        return 
             
      now = fields.Datetime.context_timestamp(self, datetime.now())
      nextcall = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(cron_record['nextcall']))           
      if nextcall < now:
        return 
      
      cron_record.try_write({'nextcall':fields.Datetime.now()})

      
    def schedule_process_data_cron_job(self):
    
      if not self.env['enotif.settings'].get('process_notifications'):
        return
              
      cron_record = self.env.ref('enotif.enotif_cron_process_data')
      if not cron_record or cron_record.active:
        return
                  
      count = self.search_count([])       
      if count == 1: #don't start cron just for one record. Save one minute
        self.process_data()
        return
      
      numbercall = 1;
      if count > MAX_NUMBER_OF_RECORDS_TO_PROCESS:
        numbercall = int(math.ceil(float(count) / MAX_NUMBER_OF_RECORDS_TO_PROCESS ))
        
      cron_record.try_write({'interval_number':3, 'interval_type': 'minutes', 'numbercall': numbercall, 'active': True, 'nextcall':fields.Datetime.now()})      
        
        
    def stop_process_data_cron_job(self):        
      cron_record = self.env.ref('enotif.enotif_cron_process_data')
      if not cron_record or not cron_record.active:
        return        
      cron_record.try_write({'active': False})  
        
        
        
        
        