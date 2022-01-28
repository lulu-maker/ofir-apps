odoo.define('enotif_woo.keys', function (require) {
'use strict';

  var core = require('web.core');
  var qweb = core.qweb;
  var AbstractAction = require('web.AbstractAction');
  
  var MenuAction = AbstractAction.extend({
    xmlDependencies: ['/enotif_woo/static/src/xml/form.xml'],  
    events: {
        'click #uw_check_connection': 'checkConnection'               
    },     
        
        
    willStart: function () {
      var self = this;
      var def = this._rpc({route: '/enotif_woo/init'}).then(function (data) {
         $.extend(self, data);
      });

      return $.when(this._super.apply(this, arguments), def);
    },
    
    
    start: function() {

      var data = {
        woocommerce_url : this.woocommerceUrl ? this.woocommerceUrl : '',
        woocommerce_api_key : this.woocommerceApiKey ? this.woocommerceApiKey : '',
        woocommerce_api_secret : this.woocommerceApiSecret ? this.woocommerceApiSecret : ''
      }
      
      this.$el.prepend(qweb.render("enotif_woo_template_keys", {data: data}));
      
      this.connectionResultDiv = this.$('#uw_connection_result');     
                  
      this._super.apply(this, arguments);
    },
   
      
        
    checkConnection: function() {
    
      this.connectionResultDiv.html('');
                     
      var woocommerceUrl = this.$('#woocommerce_url').val();
      var woocommerceApiKey = this.$('#woocommerce_api_key').val();
      var woocommerceApiSecret = this.$('#woocommerce_api_secret').val();    
    
      if (!woocommerceUrl || !woocommerceApiKey || !woocommerceApiSecret){
        this.connectionResultDiv.html('<span class="error-message">The URL, API key and API secret key fields should not be empty.</span>');
        return;
      }
      
      if (woocommerceUrl.lastIndexOf('https://', 0) !== 0){
        this.connectionResultDiv.html('<span class="error-message">The URL should start with https://</span>');
        return;
      }
            
      var params = {
        woocommerce_url : woocommerceUrl,
        woocommerce_api_key : woocommerceApiKey,
        woocommerce_api_secret : woocommerceApiSecret
      }    
      
      var self = this;   
         
      this._rpc({route: '/enotif_woo/check_connection', params: params}).then(function (data) {
      
         if (data){
         
           if (!data.error){
           
              if (data.products && data.products instanceof Array && (data.products.length == 0 || data.products[0].id)){
               self.connectionResultDiv.html('<span class="success-message">Connection is good.</span>');
 
              } else {
               var responseStr = JSON.stringify(data.products);
               self.connectionResultDiv.html('<span class="error-message">Cannot use this connection.</span><br/><br/>The WooCommerce response does not contain data about products.<br/><br/>Response data:<br/><textarea style="resize:both">' + responseStr + '</textarea><br/>Valid response data should be like this:<br/>[{"id":132,"sku":"test_sku11","stock_quantity":null,"in_stock":true}]');
              }

           } else {

              var message = '';
              
              message += '<span class="error-message">ERROR: Cannot connect.</span><br/>';
              
              message += '<br/>';      
              message += '<b>Debugging tips:</b><br/><br/>';
              
              if (data.history_lines && data.history_lines.length){
                message += 'The request has beed redirected to another URL: ' + _.escape(data.history_lines.join(' ')) + '<br/><br/>';       
              }              
              
              message += 'Requested URL:<br/><a href="'+data.url+'" target="_blank">'+data.url+'</a><br/><br/>';
              
              if (data.status_code){
                message += 'Server response code: '+data.status_code+'<br/><br/>';       
              }
                           
              if (data.headers){
                message += 'Response headers:<br><textarea style="resize:both">' + JSON.stringify(data.headers) + '</textarea><br/><br/>';       
              } 
                            
              if (data.error_text || data.error_text_lines){
                message += 'Server error message:<br><textarea style="resize:both">' + (data.error_text ? data.error_text : data.error_text_lines.join("\n")) + '</textarea><br/><br/>';       
              } 
               
              if (data.response_content != undefined){
                message += 'Response text ' + (data.response_content == '' ? '(is empty)' : '') + ':<br><textarea style="resize:both">' + _.escape(data.response_content) + '</textarea><br/>';       
              }
                                                     
              message += '<br/>';
              if (data.status_code == 401){ 
                message += 'The 401 Unauthorized response means that you should check your API keys.<br/>';   
              } else if (data.status_code == 403){
                message += 'Try to open the requested URL in your web browser:<br/>';
                message += 'If you can open it with browser it is possible that your WooCommerce website blocks all requests from bots and scripts.<br/>';
                message += 'Contact your hosting support and ask how to enable access for WooCommerce API from remote Python script.<br/>';               
              } else if (data.response_json && (data.response_json.errors || data.response_json.code)) {
                message += 'The response means that you can access the API but the API version is old.<br/>';
                message += 'This module requires WooCommerce API v3.<br/>'; 
                message += 'It is available on WooCommerce 3.5.x or later and WordPress 4.4 or later.<br/>';                                                                         
                message += 'Please upgrade your WordPress and WooCommerce to the latest version.<br/>';
              } 
              
              message += '<br/>';                              
              message += 'A sample URL of the demo website with WooCommerce API v3 enabled for testing:<br/>https://hottons.com/demo/wp/odp/<br/>With this URL you should receive the 401 Unauthorized response.<br/>It will mean that the connection is good but the keys are wrong.<br/><br/>';
              
              self.connectionResultDiv.html(message);         
           }
         }
      }).catch(function(){ 
         self.connectionResultDiv.html('<span class="error-message">Odoo error before trying to connect.</span><br/>Try to enable the debugging mode and check server logs.');
      });                          
    }  
      
  });
  
  core.action_registry.add('enotif-woo-action', MenuAction);    

  return MenuAction;
});