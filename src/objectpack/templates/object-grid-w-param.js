(function(){
    var grid = {% include "ext-grids/ext-object-grid.js" %},
        session_param = {'{{ component.session_key_name }}': '{{ component.session_key_value }}'};

    function addSessionParams(grid, request) {
        console.log('addSessionParams')
        request.params = Ext.applyIf(request.params, session_param);
    };
    grid.on('beforenewrequest', addSessionParams);
    grid.on('beforeeditrequest', addSessionParams);
    grid.on('beforedeleterequest', addSessionParams);
    grid.store.on('beforeload', function(store) {
        console.log('beforeLoad')
        store.setBaseParam(
            '{{ component.session_key_name }}',
            '{{ component.session_key_value }}'
        );
    });

    return grid;
})()
