var channelstreamApp = angular.module('channelstreamApp', []);

channelstreamApp.controller('chatCtl', function ($scope, $http) {
    $scope.user = {
        userName: userName
    };
    $scope.connSignature = null;
    $scope.channels = ['pub_chan', 'pub_chan2'];
    $scope.selected_channel = {value: $scope.channels[0]}
    $scope.stream = [];
    $scope.conn_id = null;
    $scope.socket = null;

    var webapp_url = window.location.toString();

    $scope.subscribe_channel = function () {
        var json_data = {
            channels: ['notify'],
            conn_id: $scope.conn_id };
        $scope.socket.emit('join', ['notify']);
    }

    $scope.send_message = function () {
        var json_data = {message: $scope.message,
            username: $scope.user.userName,
            channel: $scope.selected_channel.value};
        $http({method: 'POST', url: webapp_url + '/message', data: json_data}).
            success(function (data, status, headers, config) {
                $scope.message = ''
            }).
            error(function (data, status, headers, config) {
                // called asynchronously if an error occurs
                // or server returns response with an error status.
            });
    }

    var on_message = function (messages) {
        console.log('messages', messages);
        $scope.$apply(function (scope) {
            _.each(messages, function (message) {
                if (scope.stream.length > 10) {
                    scope.stream.shift();
                }
                scope.stream.push(message);
            });
        });
    }

    var json_data = {'user': $scope.user.userName,
        'channels': $scope.channels
    };


    $http({method: 'POST', url: webapp_url + '/connect', data: json_data}).
        success(function (data, status, headers, config) {
            $scope.user.userName = data['username'];
            $scope.connSignature = data['signature'];
            var query = 'username=' + data.username +
                '&signature=' + encodeURIComponent($scope.connSignature);
            $scope.socket = io.connect('/stream', {query: query});
            $scope.socket.on('chat', function (data) {
                console.log('chat', data);

            });
            $scope.socket.on('connecting', function () {
                console.log('connecting');
            });
            $scope.socket.on('heartbeat', function () {
                console.log('heartbeat');
            });

            $scope.socket.on('connect', function () {
                console.log('connected');
                $scope.socket.emit('join', ['pub_chan', 'pub_chan2'])
            });
            $scope.socket.on('disconnect', function () {
                console.log('disconnected');
            });
            $scope.socket.on('user_connect', function (message, callback) {
                console.log('user_connect', message);
            });
            $scope.socket.on('message', on_message);
            $scope.socket.on('join', function (channels, callback) {
                $scope.$apply(function (scope) {
                    _.each(channels, function (chan) {
                        console.log('joined', chan);
                        if (_.indexOf(scope.channels, chan) === -1) {
                            scope.channels.push(chan);
                        }
                    });
                });
            });
            $scope.socket.on('leave', function (channels, callback) {
                console.log('leave', channels);
            });
            $scope.socket.on('presence_join', function (user, channels) {
                console.log('presence_join', user, channels);
            });
        }).
        error(function (data, status, headers, config) {
            // called asynchronously if an error occurs
            // or server returns response with an error status.
        });


});