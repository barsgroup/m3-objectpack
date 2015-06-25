Ext.apply(win, {

    initMultiSelect:function(selectedItems) {
        var grid = Ext.getCmp('{{ component.grid.client_id }}');
        this.checkedItems = this.extractSelectedData(selectedItems);
        this.grid = grid;

        grid.getStore().on('load', this.onGridStoreLoad, this);
        grid.getSelectionModel().on('rowselect', this.onCheckBoxSelect, this);
        grid.getSelectionModel().on('rowdeselect', this.onCheckBoxDeselect, this);
    },

    extractSelectedData:function(selectedItems) {
        var i = 0, result = {};
        for(; i < selectedItems.length; i++) {
            result[selectedItems[i].data.id] = selectedItems[i].copy();
        }
        return result;
    },

    onGridStoreLoad:function(store, records, options) {
        var i = 0, j = 0, recordsToSelect = [];
        for (;i< records.length;i++) {
            if (this.checkedItems[records[i].data.id]) {
                recordsToSelect.push(records[i]);
            }
        }
        this.grid.getSelectionModel().selectRecords(recordsToSelect);
    },

    onCheckBoxSelect:function(selModel, rowIndex, record) {
        if (!this.checkedItems[record.data.id] ) {
            this.checkedItems[record.data.id] = record.copy();
        }
    },

    onCheckBoxDeselect:function(selModel, rowIndex, record) {
        if (this.checkedItems[record.data.id]) {
            this.checkedItems[record.data.id] = undefined;
        }
    }
});

function isGridSelected(grid, title, message){
    var res = true;
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

function selectValue() {
    var records = [], win, v;
    win = Ext.getCmp('{{ component.client_id }}');
    var grid = Ext.getCmp('{{ component.grid.client_id }}');

    if (!isGridSelected(grid, 'Выбор элемента', 'Выберите элемент из списка') ) {
        return;
    }

    for (v in win.checkedItems) {
        if (win.checkedItems.hasOwnProperty(v) && win.checkedItems[v] !== undefined) {
            records.push(win.checkedItems[v]);
        }
    };
    win = Ext.getCmp('{{ component.client_id}}');
    win.fireEvent('closed_ok', records);
    win.close();
};
