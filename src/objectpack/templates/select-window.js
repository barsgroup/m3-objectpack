function isGridSelected(grid, title, message){
    res = true;
    if (!grid.getSelectionModel().hasSelection() ) {
        Ext.Msg.show({
           title: title,
           msg: message,
           buttons: Ext.Msg.OK,
           icon: Ext.MessageBox.INFO
        });
        res = false;
    };
    return res;
}

function selectValue(){
    var id, displayText;
    {%if component.grid %}
        var grid = Ext.getCmp('{{ component.grid.client_id}}');
        if (!isGridSelected(grid, 'Выбор элемента', 'Выберите элемент из списка') ) {
            return;
        }
        
        id = grid.getSelectionModel().getSelected().id;
        displayText = grid.getSelectionModel().getSelected().get("{{ component.column_name_on_select }}");          
    {% else %}
        var tree = Ext.getCmp('{{ component.tree.client_id}}');
        if (!isTreeSelected(tree, 'Новый', 'Выберите элемент в дереве!') ) {
            return;
        }
        
        id = tree.getSelectionModel().getSelectedNode().id;
        displayText = tree.getSelectionModel().getSelectedNode().attributes.{{ component.column_name_on_select }};
    {% endif %}
    var win = Ext.getCmp('{{ component.client_id}}');
    if (id!=undefined && displayText!=undefined){
        win.fireEvent('select_value', id, displayText); // deprecated
        win.fireEvent('closed_ok', id, displayText); 
    };
    win.close();
}