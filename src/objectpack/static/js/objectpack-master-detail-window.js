/**
 * Окно master-detail
 */
Ext.define('Ext.objectpack.MasterDetailWindow', {
    extend: 'Ext.m3.Window',
    xtype: 'objectpack-master-detail-window',

    masterGrid: null,
    detailGrid: null,

    masterParamName: null,

    getMaster: function() {
        var sm = this.masterGrid.getSelectionModel();
        return (sm.getSelected && sm.getSelected()) || (
            sm.getSelectedNode && sm.getSelectedNode());
    },

    initComponent: function(){
        var win = this;
        win.callParent();
        win.masterGrid = win.find('itemId', 'master_grid')[0];
        win.detailGrid = win.find('itemId', 'detail_grid')[0];
        win.masterGrid.getSelectionModel().on('selectionchange', function(){
            var m = win.getMaster();
            if (m !== undefined) {
                win.getContext()[win.masterParamName] = m.id;
                win.detailGrid.getStore().reload();
            }
        });

        win.detailGrid.getStore().on('beforeload', function(st, options) {
            var m = win.getMaster(),
                newOptions = {};

            newOptions[win.masterParamName] = (m && m.id) || 0;
            options.params = Ext.applyIf(newOptions, options.params);
        });

        win.detailGrid.on('beforenewrequest', function(){
            if (!win.getMaster()) {
                Ext.Msg.show({
                    title: 'Внимание!',
                    msg: win.chooseMasterMsg,
                    buttons: Ext.MessageBox.CANCEL,
                    icon: Ext.MessageBox.ERROR,
                });
                return false;
            };
        });
    },

    bind: function(data) {
        this.masterParamName = data['master_param_name'];
        this.chooseMasterMsg = data['choose_master_msg'] || (
            'Сначала выберите родительский элемент!'
        );
    },
});
