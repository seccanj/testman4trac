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

        window.tm_attachDialogEvents = function(base_url, dialogName, actionName, parameterNames, inParams, handlerFunction, valueGetterFunction) {
            var params = inParams != null ? inParams : {};

            $("#tm_"+dialogName+"_button_ok").button({
              text: true,
              icons: {
                primary: "ui-icon-check"
              }
            })
            .click(function(e) {
            	  e.preventDefault();
            	  e.stopPropagation();
            	
	              var okButton = $(this);
	              okButton.prop("disabled", true);
	
	              if (parameterNames) {
		              for (var i = 0; i < parameterNames.length; i++) {
		                  parameterName = parameterNames[i];
	    	              var parameterValue = $("#tm_"+dialogName+"_"+parameterName).val();
	    	              console.info(parameterName+'='+parameterValue);

	    	              params[parameterName] = parameterValue;
	            	  }
	              }
            	  
            	  if (valueGetterFunction) {
            		  $.extend(params, valueGetterFunction());
            	  }
	
            	  console.info("params: ");
            	  console.dir(params);
            	  
	              doAjaxCall(base_url+"/action/testmanager.actions!"+actionName, "GET", params, true, function(data) {
	                    var resultJson = data;
	                    console.info(resultJson);
	
	                    var output = $.parseJSON(resultJson);
	                    
	                    if (output.result === "OK") {
	                        $("#tm_dialog_anchor").dialog("destroy");
	                        if (handlerFunction) {
		                        handlerFunction(output);
	                        }
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
	        	tm_collapseTreeNode(treeNode);
	        } else {
	        	tm_expandTreeNode(treeNode);
	        }
        };
        
        window.tm_collapseTreeNode = function(treeNode) {
	        if (treeNode.hasClass('expanded')) {
	            treeNode.removeClass('expanded');
	            treeNode.addClass('collapsed');
	            treeNode.children('i').removeClass('fa-minus-square-o');
	            treeNode.children('i').addClass('fa-plus-square-o');
	            treeNode.children('ul, li').hide();
	        }
        };
        
        window.tm_expandTreeNode = function(treeNode) {
	        if (treeNode.hasClass('collapsed')) {
	            treeNode.removeClass('collapsed');
	            treeNode.addClass('expanded');
	            treeNode.children('i').removeClass('fa-plus-square-o');
	            treeNode.children('i').addClass('fa-minus-square-o');
	            treeNode.children('ul, li').show();
	        }
        };
        
        window.tm_collapseAllTreeNodes = function() {
        	$('#tm_tree').find('ul').each(
        			function() {
        				tm_collapseTreeNode($(this));
        			});
        };
        
        window.tm_expandAllTreeNodes = function() {
        	$('#tm_tree').find('ul').each(
        			function() {
        				tm_expandTreeNode($(this));
        			});
        };
        
        window.tm_stripLessSpecialChars = function(str) {
            return str.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/[;#&\?]/g, '');
        };

        
    });        
})(jQuery_testmanager);


