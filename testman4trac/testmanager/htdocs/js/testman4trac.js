(function($) {
    $(function() {
        window.tm_loadDialog = function(base_url, actionName, inParams, minWidth) {
            var params = inParams != null ? inParams : {};
            var width = minWidth ? minWidth : 500;
            
            doAjaxCall(base_url+"/action/testmanager.actions.Actions!"+actionName, "GET", inParams, true, function(data) {
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
            	  
	              doAjaxCall(base_url+"/action/testmanager.actions.Actions!"+actionName, "GET", params, true, function(data) {
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
        
        window.tm_attachCustomFieldsEvents = function(baseUrlParam, artifactParam, idParam) {
        	var base_url = baseUrlParam
        	var artifact = artifactParam;
        	var id = idParam;
        	
        	$('#tm_custom_fields_section').on('click', '.tm_button', function(event) {
        		var node = $(this);
    			var fieldName = node.closest('tr').data('fieldname');
    			var fieldType = node.closest('tr').data('fieldtype');

    			if (node.hasClass('tm_custom_field_edit_button')) {
    				$('#custom_field_value_'+fieldName).hide();
    				$('#container_custom_field_'+fieldName).show();
        			node.parent().children().show();
        			node.hide();
        		} else if (node.hasClass('tm_custom_field_save_button')) {
        			var value = null;
  
					if (fieldType == 'radio') {
						value = $("input:radio[name=custom_field_"+fieldName+"]:checked").val();
					} else if (fieldType == 'checkbox'){
						value = $('#custom_field_'+fieldName).prop("checked") ? '1' : '0';
					} else {
						value = $('#custom_field_'+fieldName).val();
					}
        			
					var params = {
						artifact: artifact,
						id: id,
						field_name: fieldName,
						field_type: fieldType,
						value: value
					};
        			
					doAjaxCall(base_url+"/action/testmanager.actions.Actions!change_custom_field", "GET", params, true, function(data) {
	                    var resultJson = data;
	                    console.info(resultJson);
	
	                    var output = $.parseJSON(resultJson);
	                    
	                    if (output.result === "OK") {
	        				$('#custom_field_value_'+fieldName).html(output.value ? output.value : value).show();
	        				$('#container_custom_field_'+fieldName).hide();
	            			node.parent().children().hide();
	            			node.parent().children('.tm_custom_field_edit_button').show();

	                    } else {
	                    	$("#tm_artifact_message_holder").addClass("ui-state-error");
	                    	$("#tm_artifact_message_holder").html(output.message);
	                    }
	                });
        			
        		} else if (node.hasClass('tm_custom_field_cancel_button')) {
    				$('#container_custom_field_'+fieldName).hide();
        			node.parent().children().hide();
        			node.parent().children('.tm_custom_field_edit_button').show();
        		}
        	});
        	
        }
        
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


