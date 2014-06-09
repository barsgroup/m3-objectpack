/**
 * Окно master-detail
 */
Ext.define('Ext.objectpack.MasterDetailWindow', {
    extend: 'Ext.m3.Window',
    xtype: 'objectpack-master-detail-window',

    masterGrid: null,
    detailGrid: null,

    masterParamName: null,

    initComponent: function(){
        var win = this;
        win.callParent();
        win.masterGrid = win.find('itemId', 'master_grid')[0];
        win.detailGrid = win.find('itemId', 'detail_grid')[0];
        win.masterGrid.getSelectionModel().on('selectionchange', function(){
            win.detailGrid.getStore().reload();
        });
        win.detailGrid.getStore().on('beforeload', function(st) {
            var rec = win.masterGrid.getSelectionModel().getSelected();
            if (rec !== undefined) {
                st.setBaseParam(win.masterParamName, rec.id);
            } else {
                return false;
            };
        });
    },

    bind: function(data) {
        this.masterParamName = data['master_param_name'];
    },
});
