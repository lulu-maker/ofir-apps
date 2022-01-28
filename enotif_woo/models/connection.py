import logging
import requests
from odoo import fields, models
from traceback import format_exception_only

FLAG_FILE_PATH = '/wp-content/plugins/notify-odoo/pub/static/new_notifications_flag.txt'
REQUEST_NOTIFICATIONS_URL = '/wp-admin/admin-ajax.php?action=notifyodoo_get_notifications'
URLOPEN_TIMEOUT = 30

_logger = logging.getLogger(__name__)

class Connection(models.AbstractModel):
    _description = 'Enotif WooCommerce - connection model'
    _name = 'enotif_woo.connection'

    def fetch_notifications(self):
      
      if self.check_flag_file(): # there are new notifications on the remote website
        
        notifications = self.get_new_notifications()
        if notifications:          
          
          records = self.env['enotif.type'].search([])
          if records:
            id_by_type = {r.type:r.id for r in records}
            for n_type, item_ids in notifications.items():
              if n_type in id_by_type:
                type_id = id_by_type[n_type]            
                self.env['enotif.notification'].save_notifications({type_id : item_ids})
        
    
    def get_new_notifications(self):    
      """
        url = 'http://localhost/wordpress/wp-admin/admin-ajax.php?action=notifyodoo_get_notifications'
        result = {'new_order': [503, 501, 500, 502], 'test_notification': [0]}
      """
      
      woocommerce_url = self.env['enotif_woo.keys'].search([], limit=1).woocommerce_url
      if not woocommerce_url:
        error_text = "Enotif WooCommerce module cannot access the notifications flag on the WooCommerce website because the WooCommerce URL is not specified. Please set WooCommerce URL in Odoo admin panel -> Menu -> External Notifications -> WooCommerce Keys"
        _logger.warning(error_text)
        self.env['enotif.notification'].set_error_text(error_text)
        return {}
       
      result = {};

      url = woocommerce_url.rstrip("/") + REQUEST_NOTIFICATIONS_URL
      
      try: 
        # The other website expects request from 'User-Agent': 'odoo_enotif_request' to delete all notifications after responding to this request. 
        # For debugging you can change the user agent to make the other website not delete notifications 
        r = requests.get(url, headers={'User-Agent': 'odoo_enotif_request'}, timeout=URLOPEN_TIMEOUT, verify=False)
        r.raise_for_status()
        result = r.json()
      except Exception as e:
        error_text = "ERROR: Enotif WooCommerce module cannot get notifications with URL %s \n error text : %s" % (url, format_exception_only(type(e), e))
        _logger.error(error_text)            
        self.env['enotif.notification'].set_error_text(error_text)      
      
      return result;
              
                        
    def check_flag_file(self):
      """          
        http://localhost/wordpress/wp-content/plugins/notify-odoo/pub/static/new_notifications_flag.txt
        The flag file has '1' when there are new notifications otherwise it is empty 
      """
      
      woocommerce_url = self.env['enotif_woo.keys'].search([], limit=1).woocommerce_url
      if not woocommerce_url:
        error_text = "Enotif WooCommerce module cannot access the notifications flag on the WooCommerce website because the WooCommerce URL is not specified. Please set WooCommerce URL in Odoo admin panel -> Menu -> External Notifications -> WooCommerce Keys"
        _logger.warning(error_text)
        self.env['enotif.notification'].set_error_text(error_text)
        return False

      url = woocommerce_url.rstrip("/") + FLAG_FILE_PATH
      
      file_content = ''
      try:     
        r = requests.get(url, headers={'User-Agent': 'odoo_enotif_request'}, timeout=URLOPEN_TIMEOUT, verify=False)
        r.raise_for_status()
        file_content = r.text
      except Exception as e:
        error_text = "ERROR: Enotif WooCommerce module cannot access the notifications flag file with URL %s \n error text : %s" % (url, format_exception_only(type(e), e))
        _logger.error(error_text)                
        self.env['enotif.notification'].set_error_text(error_text)
      
      return file_content == '1'

        
        
        