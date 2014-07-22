/**
 * Окно выбора из справочника
 */
Ext.define('Ext.objectpack.BaseTreeSelectWindow', {
    extend: 'Ext.m3.Window',
    xtype: 'tree-select-window',

    multiSelect: false,
    columnNameOnSelect: null,

    callbackUrl: null,

    grid: null,

    initComponent: function () {
        this.callParent();
        this.grid = this.find(this.gridItemId)[0];

        this.grid.un('dblclick', this.grid.onEditRecord);
        this.grid.on('dblclick', function (cmp, rowIndex, e) {
            this.selectValue();
        }, this);
    },

    isGridSelected: function (grid, title, message) {
        res = true;
        if (!grid.getSelectionModel().getSelectedNode()) {
            Ext.Msg.show({
                title: title,
                msg: message,
                buttons: Ext.Msg.OK,
                icon: Ext.MessageBox.INFO
            });
            res = false;
        }
        ;
        return res;
    },

    selectValue: function() {
        var id, displayText;

        var grid = this.grid;
        if (!this.isGridSelected(grid, 'Выбор элемента', 'Выберите элемент из списка')) {
            return;
        }

        if (this.multiSelect) {
            var selections = [grid.selModel.getSelectedNode(), ],
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
            id = grid.getSelectionModel().getSelectedNode().id;
            displayText = grid.getSelectionModel().getSelectedNode().attributes[this.columnNameOnSelect];
        }

        if (this.callbackUrl) {
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
                this.fireEvent('closed_ok', id, displayText);
            }
            this.close();
        }
    }
});