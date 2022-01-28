odoo.define('enotif_woo_order.order', function (require) {
'use strict';

  var core = require('web.core');
  var qweb = core.qweb;
  var AbstractAction = require('web.AbstractAction');
  
  var MenuAction = AbstractAction.extend({
    xmlDependencies: ['/enotif_woo_order/static/src/xml/form.xml'],  
    events: {
        'click #enotif_woo_order_import_orders': 'importOrders',
        'click #enotif_woo_order_import_customers': 'importCustomers',
        'click #enotif_woo_order_import_products': 'importProducts',
    },
   
    
    start: function() {
      this.$el.prepend(qweb.render("enotif_woo_template_order", {}));
      this.resultDiv = this.$('#enotif_woo_order_result');
      this.resultCustomersDiv = this.$('#enotif_woo_customer_result');
      this.resultProductsDiv = this.$('#enotif_woo_products_result');
      this._super.apply(this, arguments);
    },   
      
        
    importOrders: function() {
      
      var self = this;   
         
      this._rpc({route: '/enotif_woo_order/import_orders'}).then(function (data) {
      
         if (data){
         
           if (!data.error){
           
              var message = '';
              
              if (data.number_of_orders > 0){
                message += 'Number of orders to import <b>' + data.number_of_orders + '</b></br></br>';
                
                message += 'The importing process will start in three minutes.</br></br>';
                
                message += 'You can view the process status in the "Progress" section.</br></br>';
                                                             
              } else {
                message += 'There are no new orders on the remote website. Or orders with the same email already exist.</br></br>';                                             
              }
              
              self.resultDiv.html(message);
              
           } else {
           
              var message = 'Server error message:<br><textarea style="resize:both">' + data.error_text + '</textarea><br/>';
              
              message += 'Check connection in the "WooCommerce Keys" section';
              
              self.resultDiv.html(message);                
           }
         }
      }).catch(function(){ 
         self.connectionResultDiv.html('<span class="error-message">ERROR: check if the Odoo server is running. Check server logs.</span>');
      });                          
    },

    importCustomers: function() {

      var self = this;

      this._rpc({route: '/enotif_woo_order/import_customers'}).then(function (data) {

        console.log("=================import_customers==================",data)
        if (data){

           if (!data.error){

              var message = '';

              if (data.number_of_customers > 0){
                message += 'Number of customers to import <b>' + data.number_of_customers + '</b></br></br>';
              } else {
                message += 'There are no new customers on the remote website. Or customers with the same email already exist.</br></br>';
              }

              self.resultCustomersDiv.html(message);

           } else {

              var message = 'Server error message:<br><textarea style="resize:both">' + data.error_text + '</textarea><br/>';

              message += 'Check connection in the "WooCommerce Keys" section';

              self.resultDiv.html(message);
           }
         }
      }).catch(function(){
         self.connectionResultDiv.html('<span class="error-message">ERROR: check if the Odoo server is running. Check server logs.</span>');
      });
    },

    importProducts: function() {

      var self = this;

      this._rpc({route: '/enotif_woo_order/import_products'}).then(function (data) {

        console.log("=================import_customers==================",data)
        if (data){

           if (!data.error){
              var message = '';
              if (data.number_of_products > 0){
                message += 'Number of Products to import <b>' + data.number_of_products + '</b></br></br>';
              } else {
                message += 'There are no new customers on the remote website. Or customers with the same email already exist.</br></br>';
              }
              self.resultProductsDiv.html(message);
           } else {

              var message = 'Server error message:<br><textarea style="resize:both">' + data.error_text + '</textarea><br/>';

              message += 'Check connection in the "WooCommerce Keys" section';

              self.resultDiv.html(message);
           }
         }
      }).catch(function(){
         self.connectionResultDiv.html('<span class="error-message">ERROR: check if the Odoo server is running. Check server logs.</span>');
      });
    },
      
  });
  
  core.action_registry.add('enotif-woo-order-action', MenuAction);    

  return MenuAction;
});