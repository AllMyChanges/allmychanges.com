angular.module('share-badge', [])
.directive('shareBadge', [function(){
    var link = function (scope, element, attrs) {
        var all_markups = ['markdown', 'rst', 'html'];

        if (scope.username != 'None') {
            scope.package_url = '/u/' + scope.username + '/' + scope.namespace + '/' + scope.name;
        } else {
            scope.package_url = '/p/' + scope.namespace + '/' + scope.name;
        }
        scope.origin = window.location.origin;

        scope.show = function (new_markup) {
            angular.forEach(all_markups, function(markup) {
                scope[markup] = (markup == new_markup);
            });
        }
        scope.show(all_markups[0]);
    }

    return {
        scope: {
            username: '=',
            namespace: '=',
            name: '=',
        },
        link: link,
        restrict: 'E',
        templateUrl: '/static/allmychanges/html/share-badge.html',
    };
}]);
