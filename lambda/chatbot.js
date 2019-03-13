'use strict';
const AWS = require('aws-sdk');

exports.handler = function(event, context, callback) {
    // TODO implement
    var lexruntime = new AWS.LexRuntime();
    var lexUserId = 'chatbot'
    var sessionAttributes = {};
    var params = {
        botAlias: '$LATEST',
        botName: 'FoodOrderBot',
        inputText: event.messages[0].unstructured.text,
        userId: lexUserId,
        sessionAttributes: sessionAttributes
    };
    var response = { "statusCode": 404 };
    // var myPromise = new Promise(function(resolve, reject) {
                                   lexruntime.postText(params, function(err, data) {
                                                       if (err) {
                                                       response = {
                                                       statusCode: 403,
                                                       body: JSON.stringify("bye"),
                                                       };
                                                       callback(null, response);
                                                       }
                                                       if (data) {
                                                       sessionAttributes = data.sessionAttributes;
                                                       response = {
                                                       statusCode: 200,
                                                       body: data.message
                                                       };
                                                       callback(null, response);
                                                       }
                                                       });
                                   // });
    // callback(null, myPromise);
}
