app.directive('trackButton', ['$http', '$cookies', '$log', function($http, $cookies, $log){
    $http.defaults.headers.common['X-CSRFToken'] = $cookies['csrftoken'];

    var link = function (scope, element, attrs) {
//       scope.alreadyTracked = false;
        scope.alreadyTracked = scope.alreadyTracked == 'true';

        $log.debug(scope.alreadyTracked);
        scope.track = function () {
            $http.post('/v1/changelogs/' + scope.changelog + '/track/').success(function(data) {
                $log.info('Tracked');
                scope.alreadyTracked = true;
                $log.info(scope.alreadyTracked);
            });
        }
        scope.untrack = function () {
            $http.post('/v1/changelogs/' + scope.changelog + '/untrack/').success(function(data) {
                $log.info('UnTracked');
                scope.alreadyTracked = false;
                $log.info(scope.alreadyTracked);
            });
        }
    }

    return {
        scope: {
            changelog: '=',
            alreadyTracked: '@'
        },
        link: link,
        restrict: 'E',
        templateUrl: '/static/allmychanges/html/track-button.html'
    };
}]);
