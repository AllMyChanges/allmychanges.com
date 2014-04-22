var app = angular.module('allMyChangesApp', ['ngCookies', 'angucomplete-alt']);

app.directive('digestLine', ['$http', '$interval', '$timeout', function ($http, $interval, $timeout) {
    return {
        restrict: 'EA',
        scope: {
            package: '='
        },
        template: '<p> <input type="text" ng-model="package.namespace"/> <input type="text" ng-model="package.name"/> <input type="text" ng-model="package.source" class="digest-source__source-field"/> <button ng-click="remove()">x</button> <a class="digest-source__problem" ng-if="package.problem" ng-href="{{package.absolute_uri}}">{{package.problem}}</a> <a class="digest-source__version" ng-if="package.latest_version" ng-href="{{package.absolute_uri}}">{{package.latest_version}}</a> <a class="digest-source__waiting" ng-if="!package.latest_version && !package.problem" ng-href="{{package.absolute_uri}}">Waiting</a></p>',
        link: function (scope, elem, attrs) {
            scope.package = angular.copy(scope.package);
            var my_compare = function(left, right, fields) {
                var equal = true;
                angular.forEach(fields, function(key) {
                    if (left[key] != right[key]) {
                        console.log('left[' + key + '] = ' + left[key] + ', but right is "' + right[key] + '"');
                        equal = false;
                    }});
                return equal;
            }
            var update_package = function (data) {
                angular.extend(scope.package, data);
            }

            var update_timeout = null;
            var interval = null

            scope.$watch('package', function(new_val, old_val) {
                if (!my_compare(new_val, old_val, ['namespace', 'name', 'source'])) {

                    if (update_timeout !== null) {
                        $timeout.cancel(update_timeout);
                    }

                    update_timeout = $timeout(function() {
                        $http.put(new_val['resource_uri'], new_val).success(update_package);
                    }, 1000);
                }
            }, true);

            scope.remove = function () {
                var item_index = scope.$parent.$index;
                
                $http.delete(scope.package.resource_uri).success(function(data) {
                    scope.$parent.$parent.items.splice(item_index, 1);
                    $interval.cancel(interval);
                });
            }

            interval = $interval(function () {
                $http.get(scope.package.resource_uri).success(function (data) {
                    angular.extend(scope.package, data);
                });
            }, 15 * 1000);
        }
   }
}]);

app.controller('DigestBuilderCtrl', function ($scope, $http, $cookies, $log) {
    $http.defaults.headers.common['X-CSRFToken'] = $cookies['csrftoken'];
    $scope.items = [];

    $scope.get_source_guessing_params = function (str) {
        return $scope.new_item;
    }

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
    });

    $scope.add_item = function () {
        $http.post('/v1/packages/', $scope.new_item).success(function(data) {
            $scope.items.push(data);
            $scope.new_item = init_new_item();
        }).error(function(data) {
            // TODO: may be handle error someday
        });
    };

    
});

