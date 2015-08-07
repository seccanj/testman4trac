(function($) {
    $(function() {
        window.tm_loadDialog = function(base_url, dialogName, inparams, minWidth) {
            var params = inparams != null ? inparams : {};
            var width = minWidth ? minWidth : 500;
            
            params['type'] = "load_dialog";
            params['dialog'] = dialogName;
            
            doAjaxCall(base_url+"/testajax", "GET", params, true, function(data) {
                    var dialogMarkup = data;
                    
                    $("#tm_dialog_anchor").html(dialogMarkup);
                    
                    $( "#tm_dialog_anchor" ).dialog({ minWidth: width, modal: true, autoOpen: true });
                });
        }
    });        
})(jQuery_testmanager);

