app.directive('magicPrompt', [function(){
    var link = function (scope, element, attrs) {
        scope.submit = function () {
            window.location = '/search/?q=' + encodeURIComponent(scope.query.originalObject);
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
