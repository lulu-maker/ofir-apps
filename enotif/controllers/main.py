import json
import requests
from odoo import http
from odoo.http import request

class Connection(http.Controller):
                     
    @http.route(['/enotif/init'], type='json', auth="user", website=True)
    def get_init_data(self):
        data = request.env['enotif.notification'].get_notifications_progress()
        return data


    @http.route(['/enotif/delete_notifications'], type='json', auth="user", website=True)
    def clear_notifications(self, **kw):  
        result = {}
        request.env['enotif.notification'].delete_processed_notifications(kw.get('type_id'), kw.get('item_ids'))        
        return result
        
        
    @http.route(['/enotif/toggle_state/'], type="json", methods=['POST', 'GET'], auth="public", website=True)
    def toggle_state(self, **kw):
        result = {}        
        result['active'] = request.env['enotif.notification'].toggle_state()      
        return result
               
        
    @http.route(['/enotif/get_new_notifications'], type="json", methods=['POST', 'GET'], auth="public", website=True)
    def pause_processing(self, **kw):       
        
        result = {}
         
        Notification = request.env['enotif.notification']
        
        count_old = Notification.search_count([])
        
        Notification.set_error_text('')
        
        Notification.fetch_notifications()
        
        error_text = Notification.get_error_text()
        if error_text:
          result['error'] = 1
          result['error_text'] = error_text
        else:
          count = Notification.search_count([])    
          result['notifications_number'] = count - count_old

        return result















        