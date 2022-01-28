odoo.define('enotif.general', function (require) {
'use strict';

  var core = require('web.core');
  var qweb = core.qweb;
  var AbstractAction = require('web.AbstractAction');
  
  var MenuAction = AbstractAction.extend({
    xmlDependencies: ['/enotif/static/src/xml/form.xml'],  
    events: {
        'click button.delete-notifications': 'deleteNotifications',
        'click button.toggle-state': 'toggleState',       
        'click #enotif_get_new_notifications': 'getNewNotifications'                                    
    },
    
       
      
    willStart: function () {

      var self = this;
      var def = this._rpc({route: '/enotif/init'}).then(function (data) {
         $.extend(self, data);
      });

      return $.when(this._super.apply(this, arguments), def);
    },
  
    
    start: function() {
    
      var data = {
        items : this.items,
        process_notifications : this.process_notifications
      }
      
      this.$el.prepend(qweb.render("enotif_template_progress", {data: data}));
        
      this.resultDiv = this.$('#enotif_get_notifications_result');   
                 
      this._super.apply(this, arguments);
    },
    
    
    deleteNotifications: function(e) {
   
      var confirmed = confirm("Are you sure you would like to delete these notifications?");    
      if (!confirmed)
        return

      var resultDiv = this.$('#enotif_delete_notifications_result');
        
      var button = $(e.target);
      var type = button.data('type');      
      var typeId = parseInt(button.data('type_id'));    
      var itemIds = this.itemIdsByTypeId[typeId]
      
      var params = {'type_id': typeId, 'item_ids': itemIds}     
      console.log(params)
      
      var self = this;
               
      this._rpc({route: '/enotif/delete_notifications', params: params}).then(function (data) {
      
         if (data){         
           if (!data.error){              
              resultDiv.html('The notifications of type "' + type + '" were deleted.');
              button.closest('tr').hide();                                         
           } else {           
              resultDiv.html('There was some error. Check server logs.');                
           }
         }
      }).catch(function(){ 
         self.connectionResultDiv.html('<span class="error-message">ERROR: check if the Odoo server is running. Check server logs.</span>');
      });
          
    },
    
    
    toggleState: function() {
      var self = this;
         
      var resultDiv = this.$('#enotif_toggle_state_result');
               
      this._rpc({route: '/enotif/toggle_state'}).then(function (data) {
      
         if (data){         
           if (!data.error){
              if (data.active){
                $('.state-stopped').hide();
                $('.state-active').show();
                resultDiv.html('The processing is active now.');
                $('#enotif_progress').show();
              } else {              
                $('.state-active').hide();
                $('.state-stopped').show();
                resultDiv.html('The processing is stopped.');
                $('#enotif_progress').hide();
              }                                         
           } else {           
              resultDiv.html('There was some error. Check server logs.');                
           }
         }
      }).catch(function(){ 
         resultDiv.html('<span class="error-message">ERROR: check if the Odoo server is running. Check server logs.</span>');
      });
          
    },
    
           
    getNewNotifications: function() {
      
      var resultDiv = this.$('#enotif_get_new_notifications_result');
      
      var self = this;   
         
      this._rpc({route: '/enotif/get_new_notifications'}).then(function (data) {
      
         if (data){      
            
           if (!data.error){
           
              if (data.notifications_number > 0){
               resultDiv.html('There are new notifications. Reload this page to see the updated information.');
              } else {              
               resultDiv.html('There are no new notifications.');
              }     
                                                  
           } else {       
            
              var message = 'Server error message:<br><textarea style="resize:both;height:100px">' + data.error_text + '</textarea><br/>';
              
              message += 'Check connection in the "WooCommerce Keys" section. And check if the Notify Odoo plugin is enabled on the WooCommerce website.';
              
              resultDiv.html(message);                             
           }
         }
      }).catch(function(){ 
         resultDiv.html('<span class="error-message">ERROR: check if the Odoo server is running. Check server logs.</span>');
      });
          
    } 
      
  });
  
  core.action_registry.add('enotif-action', MenuAction);    

  return MenuAction;
});