/**
 * Окно множественного выбора из справочника
 */
Ext.define('Ext.objectpack.MultiSelectWindow', {
    extend: 'Ext.m3.Window',
    xtype: 'objectpack-multi-select-window',

    multiSelect: false,
    columnNameOnSelect: null,

    callbackUrl: null,

    grid: null,

    initComponent: function(){
        this.callParent();
        this.grid = this.findByItemId(this.gridItemId);

        this.grid.un('dblclick', this.grid.onEditRecord);
        this.grid.on('rowdblclick', function(cmp, rowIndex, e){
            this.selectValue();
        }, this);

        this.on('loadselected', this.onLoad, this);
        this.grid.getStore().on('datachanged', function(){
            this.fireEvent('loadselected');
        }, this);
    },

    onLoad: function(item){

        var recordIds = [],
            store = this.grid.getStore();

        Ext.each(store.data.items, function(value, index){
            if (value.json['selected']){
                recordIds.push(index);
            }
        }, this);

        this.grid.getSelectionModel().selectRows(recordIds);
    },

    isGridSelected: function (grid, title, message) {
        var res = true;
        if (!grid.getSelectionModel().hasSelection()) {
            Ext.Msg.show({
                title: title,
                msg: message,
                buttons: Ext.Msg.OK,
                icon: Ext.MessageBox.INFO
            });
            res = false;
        }
        return res;
    },

    selectValue: function () {
        var id, displayText;

        var grid = this.grid;
        if (!this.isGridSelected(grid, 'Выбор элемента', 'Выберите элемент из списка')) {
            return;
        }

        if (this.multiSelect) {
            var selections = grid.selModel.getSelections(),
                len = selections.length,
                ids = [],
                displayTexts = [];

            for (var i = 0; i < len; i += 1) {
                ids.push(selections[i].id);
                displayTexts.push(selections[i].get(this.columnNameOnSelect));
            }
            id = ids.join(',');
            displayText = displayTexts.join(', ');
        } else {
            id = grid.getSelectionModel().getSelected().id;
            displayText = grid.getSelectionModel().getSelected().get(this.columnNameOnSelect);
        }

        if (this.callbackUrl) {
            // NR необходимо заменить на UI.callAction
            Ext.Ajax.request({
                url: this.callbackUrl,
                success: function (res) {
                    var result = Ext.decode(res.responseText);
                    if (!result.success) {
                        Ext.Msg.alert('Ошибка', result.message)
                    } else {
                        this.fireEvent('closed_ok'); // deprecated
                        this.fireEvent('select', this);
                        this.close();
                    }
                },
                params: Ext.applyIf({id: id}, this.getContext() || {}),
                failure: uiAjaxFailMessage,
                scope: this
            });
        } else {
            if (id && displayText) {
                this.fireEvent('select', this, id, displayText);
            }
            this.close();
        }
    }
});


// Ext.apply(win, {

//     initMultiSelect:function(selectedItems) {
//         var grid = Ext.getCmp('{{ component.grid.client_id }}');
//         this.checkedItems = this.extractSelectedData(selectedItems);
//         this.grid = grid;

//         grid.getStore().on('load', this.onGridStoreLoad, this);
//         grid.getSelectionModel().on('rowselect', this.onCheckBoxSelect, this);
//         grid.getSelectionModel().on('rowdeselect', this.onCheckBoxDeselect, this);
//     },

//     extractSelectedData:function(selectedItems) {
//         var i = 0, result = {};
//         for(; i < selectedItems.length; i++) {
//             result[selectedItems[i].data.id] = selectedItems[i].copy();
//         }
//         return result;
//     },

//     onGridStoreLoad:function(store, records, options) {
//         var i = 0, j = 0, recordsToSelect = [];
//         for (;i< records.length;i++) {
//             if (this.checkedItems[records[i].data.id]) {
//                 recordsToSelect.push(records[i]);
//             }
//         }
//         this.grid.getSelectionModel().selectRecords(recordsToSelect);
//     },

//     onCheckBoxSelect:function(selModel, rowIndex, record) {
//         if (!this.checkedItems[record.data.id] ) {
//             this.checkedItems[record.data.id] = record.copy();
//         }
//     },

//     onCheckBoxDeselect:function(selModel, rowIndex, record) {
//         if (this.checkedItems[record.data.id]) {
//             this.checkedItems[record.data.id] = undefined;
//         }
//     }
// });

// function selectValue() {
//     var records = [], win, v;
//     win = Ext.getCmp('{{ component.client_id }}');
//     var grid = Ext.getCmp('{{ component.grid.client_id }}');
//     for (v in win.checkedItems) {
//         if (win.checkedItems.hasOwnProperty(v) && win.checkedItems[v] !== undefined) {
//             records.push(win.checkedItems[v]);
//         }
//     };
//     win = Ext.getCmp('{{ component.client_id}}');
//     win.fireEvent('closed_ok', records);
//     win.close();
// };
