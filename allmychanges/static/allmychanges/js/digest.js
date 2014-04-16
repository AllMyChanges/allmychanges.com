var app = angular.module('allMyChangesApp', ['ngCookies', 'angucomplete-alt']);

app.controller('DigestBuilderCtrl', function ($scope, $http, $cookies) {
    $http.defaults.headers.common['X-CSRFToken'] = $cookies['csrftoken'];
    $scope.items = [];

    $scope.$watch('selected_namespace', function(new_object, old_object) {
        if (new_object !== undefined) {
            if (new_object.originalObject.name != undefined) {
                $scope.new_item.namespace = new_object.originalObject.name;
            } else {
                $scope.new_item.namespace = new_object.originalObject;
            }
        }
    })

    function init_new_item () {
        var namespace = '';
        if ($scope.items.length > 0) {
            namespace = $scope.items[$scope.items.length - 1].namespace;
        }
        return {
            'namespace': namespace,
            'name': '',
            'source': ''
        }
    }
    $scope.new_item = {};


    $http.get('/v1/packages/').success(function(data) {
        $scope.items = data;
        $scope.new_item = init_new_item();

        $scope.$watch('items', function(new_collection, old_collection) {
            if (new_collection.length == old_collection.length) {
                for (i=0; i<new_collection.length; i++) {
                    var new_obj = new_collection[i];
                    var old_obj = old_collection[i];
                    angular.forEach(new_obj, function(value, key) {
                        if (key != '$$hashKey' && value != old_obj[key]) {
                            console.log(key);
                            console.log(old_obj[key] + ' -> ' + value);
                            $http.put(new_obj['resource_uri'], new_obj);
                            // TODO: optimize and save with slight delay
                        }
                    });
                }
            }
        }, true);
    });

    $scope.add_item = function () {
        $http.post('/v1/packages/', $scope.new_item).success(function(data) {
            $scope.items.push(data);
            $scope.new_item = init_new_item();
        }).error(function(data) {
            // TODO: may be handle error someday
        });
    };

    $scope.remove = function (url) {
        var item_index = this.$index;

        $http.delete(url).success(function(data) {
            $scope.items.splice(item_index, 1);
        });
    }
});

