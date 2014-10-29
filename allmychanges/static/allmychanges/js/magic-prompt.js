app.directive('magicPrompt', [function(){
    var link = function (scope, element, attrs) {
        scope.entered_query = '';

        scope.submit = function () {
            if (scope.query.originalObject != undefined) {
                window.location = '/search/?q=' + encodeURIComponent(scope.query.originalObject);
            } else {
                window.location = '/search/?q=' + encodeURIComponent(scope.entered_query);
            }
        }

        scope.query_changed = function (str) {
            scope.entered_query = str;
        }
    }

    return {
        scope: {
            query: '@',
        },
        link: link,
        restrict: 'E',
        templateUrl: '/static/allmychanges/html/magic-prompt.html',
    };
}]);
