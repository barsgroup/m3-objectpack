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
            var master = win.getMaster();
            // выделение снимается при некоторых действиях в окне
            if (master) {
                win.getContext()[win.masterParamName] = master.id;
                win.detailGrid.getStore().reload();
            }
        });
        win.detailGrid.getStore().on('beforeload', function(st) {
            if (win.getMaster() == undefined) {
                return false;
            };
        });
    },

    bind: function(data) {
        this.masterParamName = data['master_param_name'];
    },
});
