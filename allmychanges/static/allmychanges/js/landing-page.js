app.directive('packageSelectorLine', ['$http', '$interval', '$timeout', function ($http, $interval, $timeout) {
    return {
        restrict: 'EA',
        scope: {
            package: '='
        },
        templateUrl: '/static/allmychanges/html/package-selector-line.html',
        link: function (scope, elem, attrs) {
            scope.package = angular.copy(scope.package);
        }
   }
}]);


var reach_goal = function(name) {
    if (yaCounter !== undefined) {
        yaCounter.reachGoal(name);
    }
};

app.controller('LandingPageCtrl', function ($scope, $http, $cookies, $log) {
    $scope.tracked = [];
    $scope.tracked_len = 0;
    $scope.ignored = [];
    $scope.packages = [];

    var remove_package_from_list = function(package) {
        $scope.packages = $scope.packages.filter(function (el) {return el.id != package.id})
    };

    var add_more_elements = function(track_id, ignore_id) {
        $http.get('/v1/landing-package-suggest/?tracked=' +
                  $scope.tracked.join(',') +
                  '&ignored=' +
                  $scope.ignored.join(',') +
                  '&skip=' + $scope.packages.map(function (el) { return el.id }) +
                  '&track_id=' + track_id +
                  '&ignore_id=' + ignore_id)
             .success(function(data) {

            data.results.forEach(function(el) {
                if ($scope.packages.length < 3) {
                    $scope.packages.push(el);
                }
            });
        });
    };

    $scope.track = function (package) {
        $scope.tracked.push(package.id);
        $scope.tracked_len = $scope.tracked.length;
        if ($scope.tracked_len == 1) {
            reach_goal('LAND-TRACK-1');
        }
        if ($scope.tracked_len == 3) {
            reach_goal('LAND-TRACK-3');
        }
        if ($scope.tracked_len == 5) {
            reach_goal('LAND-TRACK-5');
        }

        var strings = ['To continue, track at least five projects…',
                       'Horay! You have tracked your first project!',
                       'Yeah, let\'s do it!',
                       'Track two packages and you are done!',
                       'Only one package left!',
                       'Good job, feel free to track more packages!']

        var label = $('.package-selector__next');
        if ($scope.tracked_len <= 5) {
            label.animate({'opacity': 0},
                          400,
                          'swing',
                          function() {
                              label.text(strings[$scope.tracked_len]);
                              label.animate({'opacity': 1});
                          });
        }
        if ($scope.tracked_len >= 5) {
            console.log('receiving digest');
            $http.get('/landing-digest/?packages=' + $scope.tracked.join(','))
                .success(function(data) {
                    $('.package-selector__digest').html(data);
                });

        }


        remove_package_from_list(package);
        add_more_elements(package.id, '');
    };
    $scope.ignore = function (package) {
        $scope.ignored.push(package.id);
        remove_package_from_list(package);
        add_more_elements('', package.id);
    };

    add_more_elements('', '');
});
