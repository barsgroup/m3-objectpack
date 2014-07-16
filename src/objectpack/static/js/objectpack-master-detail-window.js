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
            win.getContext()[win.masterParamName] = m && m.id || 0;
            win.detailGrid.getStore().reload();
        });
        win.detailGrid.getStore().on('beforeload', function(st) {
            var m = win.getMaster();
            st.setBaseParam(
                win.masterParamName,
                (m && m.id) || 0
            );
        });
    },

    bind: function(data) {
        this.masterParamName = data['master_param_name'];
    },
});
