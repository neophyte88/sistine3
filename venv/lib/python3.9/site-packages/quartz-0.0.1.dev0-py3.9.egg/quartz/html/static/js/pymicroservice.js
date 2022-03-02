var counter = 1;

var pymicroserviceMethodCall = function (opts) {
    var url = opts.url;
    if (url == undefined) {
        url = "/api";
    }
    var method = opts.method;
    var params = opts.params;
    var onSuccess = opts.onSuccess;

    $.ajax({
        url: url,
        method: "post",
        contentType: "application/json",
        dataType: "json",
        data: JSON.stringify({
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": counter
        }),
        success: onSuccess
    });
    counter++;

};

var pymicroserviceBatchCall = function (opts) {
    var url = opts.url;
    if (url == undefined) {
        url = "/api";
    }
    var onSuccess = opts.onSuccess;

    var body = [];
    for (var i = 0; i < opts.calls.length; i++) {
        body.push({
            "jsonrpc": "2.0",
            "method": opts.calls[i].method,
            "params": opts.calls[i].params,
            "id": i + 1
        })
    }
    $.ajax({
        url: url,
        method: "post",
        contentType: "application/json",
        dataType: "json",
        data: JSON.stringify(body),
        success: onSuccess
    });
};


function bootstrapNotify(type, message) {
    $.notify({
        message: message
    }, {
        type: type
    })
}