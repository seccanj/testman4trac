(function($) {
    $(function() {
        window.tm_loadDialog = function(base_url, actionName, inParams, minWidth) {
            var params = inParams != null ? inParams : {};
            var width = minWidth ? minWidth : 500;
            
            doAjaxCall(base_url+"/action/testmanager.actions!"+actionName, "GET", inParams, true, function(data) {
                    var dialogMarkup = data;
                    
                    $("#tm_dialog_anchor").html(dialogMarkup);
                    $("#tm_dialog_anchor").dialog({minWidth: width, modal: true, autoOpen: true});
                });
        };

        window.tm_attachDialogEvents = function(base_url, dialogName, actionName, parameterName, inParams, handlerFunction) {
            var params = inParams != null ? inParams : {};

            $("#tm_"+dialogName+"_button_ok").button({
              text: true,
              icons: {
                primary: "ui-icon-check"
              }
            })
            .click(function() {
              var parameterValue = $("#tm_"+dialogName+"_parameter").val();
              console.info(parameterValue);

              var okButton = $(this);
              okButton.prop("disabled", true);

              params[parameterName] = parameterValue;

              doAjaxCall(base_url+"/action/testmanager.actions!"+actionName, "GET", params, true, function(data) {
                    var resultJson = data;
                    console.info(resultJson);

                    var output = $.parseJSON(resultJson);
                    
                    if (output.result === "OK") {
                        $("#tm_dialog_anchor").dialog("destroy");
                        handlerFunction(output);
                    } else {
                        /* Show error within dialog */
                    	$("#tm_"+dialogName+"_message_holder").addClass("ui-state-error");
                    	$("#tm_"+dialogName+"_message_holder").html(output.message);
                    	okButton.prop("disabled", false);
                    }
                });
            });

            $("#tm_"+dialogName+"_button_cancel").button({
              text: true,
              icons: {
                primary: "ui-icon-close"
              }
            })
            .click(function() {
                $("#tm_dialog_anchor").dialog("destroy");
            });
        };
        
        window.tm_selectArtifactInTree = function(selectType, selectId) {
	        if (selectType && selectId) {
	            $('.tm_'+selectType+'_node[data-id="'+selectId+'"]').click();
	        }
        };
        
        window.tm_toggleTreeNode = function(treeNode) {
	        if (treeNode.hasClass('expanded')) {
	            treeNode.removeClass('expanded');
	            treeNode.addClass('collapsed');
	            treeNode.children('i').removeClass('fa-minus-square-o');
	            treeNode.children('i').addClass('fa-plus-square-o');
	            treeNode.children('ul, li').hide();
	        } else {
	            treeNode.removeClass('collapsed');
	            treeNode.addClass('expanded');
	            treeNode.children('i').removeClass('fa-plus-square-o');
	            treeNode.children('i').addClass('fa-minus-square-o');
	            treeNode.children('ul, li').show();
	        }
        };
        
    });        
})(jQuery_testmanager);


