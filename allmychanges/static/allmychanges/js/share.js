angular.module('share-badge', [])
.directive('shareBadge', [function(){
    var link = function (scope, element, attrs) {
        var all_markups = ['markdown', 'rst', 'html'];
        
        scope.show = function (new_markup) {
            angular.forEach(all_markups, function(markup) {
                scope[markup] = (markup == new_markup);
            });
        }
        scope.show(all_markups[0]);
    }

    return {
        scope: {
            package: '=',
        },
        link: link,
        restrict: 'E',
        templateUrl: '/static/allmychanges/html/share-badge.html',
    };
}]);
