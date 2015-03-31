app.controller('AddNewCtrl', function ($scope, $attrs, $http, $cookies, $timeout, $log) {
    $http.defaults.headers.common['X-CSRFToken'] = $cookies['csrftoken'];
    
    var mode = $attrs['mode'];

    // we use angucomplete, for namespace and it
    // returns an object instead of plain string
    $scope.namespace = $attrs['changelogNamespace'];
    $scope.name = $attrs['changelogName'];
    $scope.description = $attrs['changelogDescription'];
    $scope.namespace_error = !$scope.namespace && 'Please, fill this field' || '';
    $scope.name_error = $scope.namespace_error;
    $scope.package_url = 'unknown';
    $scope.search_list = $attrs['searchList'];
    $scope.ignore_list = $attrs['ignoreList'];

    $scope.changelog_id = $attrs['changelogId'];
    $scope.preview_id = $attrs['previewId'];
    $scope.changelog_source = $attrs['changelogSource'];

    $scope.tracked = false;

    // these messages will be show as plates at the top of the screen
    $scope.messages = [];

    $scope.saving = false;
    if (mode == 'edit') {
        $scope.save_button_title = 'Save';
    } else {
        $scope.save_button_title = 'Save&Track';
    }

    var spinner;

    $scope.can_save = function () {
        var result = ($scope.saving == false
                      && $scope.is_apply_button_disabled()
                      && $scope.namespace_error == '' 
                      && $scope.name_error == '' 
                      && $scope.results_ready);
        return result;
    }
    $scope.can_track = function () {
        var result = ($scope.can_save()
                      && $scope.tracked == false);
        return result;
    }

    $scope.orig_name = $scope.name;
    $scope.orig_namespace = $scope.namespace;
    $scope.orig_description = $scope.description;
    $scope.orig_changelog_source = $scope.changelog_source;
    $scope.orig_search_list = undefined;
    $scope.orig_ignore_list = undefined;


    $scope.is_apply_button_disabled = function () {
        var result = ($scope.waiting == true
                      || ($scope.orig_search_list == $scope.search_list
                          && $scope.orig_ignore_list == $scope.ignore_list
                          && $scope.orig_changelog_source == $scope.changelog_source));
        return result;
    }

    var check_and_show_messages = function () {
        $http.get('/v1/messages/').success(function (data) {
            $scope.messages = data;
        });
    }

    $scope.save = function () {
        $scope.saving = true;
        $scope.save_button_title = 'Saving...';
        return $http.put('/v1/changelogs/' + $scope.changelog_id + '/',
                         {'namespace': $scope.namespace,
                          'description': $scope.description,
                          'name': $scope.name,
                          'source': $scope.changelog_source,
                          'search_list': $scope.search_list,
                          'ignore_list': $scope.ignore_list}).success(
                              function() {
                                  $scope.saving = false;
                                  $scope.save_button_title = 'Save';
                                  check_and_show_messages();
                              });
    };

    $scope.save_and_track = function () {
        $scope.save().success(function() {
            $http.post('/v1/changelogs/' + $scope.changelog_id + '/track/').success(function() {
                $scope.tracked = true;
                $scope.package_url = '/p/' + $scope.namespace + '/' + $scope.name + '/';
                $log.info($scope.namespace);
                $log.info($scope.name);
                $log.info($scope.package_url);
            });
        });
    }

    var wait_for_preview = function () {
        if (spinner === undefined) {
            $log.info('Creating a spinner');
            spinner = new Spinner({left: '50%', top: '30px'}).spin($('.results-spin__wrapper')[0]);
        }

        $http.get('/preview/' + $scope.preview_id + '/')
            .success(function(data) {
                var data = $(data);

                if (data.hasClass('please-wait')) {
                    $('.progress-text').html(data);
                    setTimeout(wait_for_preview, 1000);
                } else {
                    $scope.waiting = false;

                    if (data.hasClass('package-changes')) {
                        $('.changelog-preview').html(data);
                        $scope.results_ready = true;
                    } else {
                        $('.changelog-problem').html(data);
                        $scope.problem = true;
                    }
                }
        });
    }

    var update_preview_callback = function () {
        $scope.waiting = true;
        $scope.results_ready = false;
        $scope.problem = false;
        $scope.orig_search_list = $scope.search_list;
        $scope.orig_ignore_list = $scope.ignore_list;
        $scope.orig_changelog_source = $scope.changelog_source;

        wait_for_preview();
    };

    update_preview_callback();

    $scope.update_preview = function () {
        $log.info('Updating preview');
        $http.post('/preview/' + $scope.preview_id + '/',
                   {'source': $scope.changelog_source,
                    'search_list': $scope.search_list,
                    'ignore_list': $scope.ignore_list})
            .success(update_preview_callback);
    };


    var validate_namespace_name_timeout;

    var validate_namespace_and_name = function () {
        $http.get('/v1/validate-changelog-name/?namespace=' + $scope.namespace + '&name=' + $scope.name + '&changelog_id=' + $scope.changelog_id)
             .success(function (data) {
                 $scope.namespace_error = '';
                 $scope.name_error = '';

                 if (data.errors) {
                     if (data.errors.namespace) {
                         $scope.namespace_error = data.errors.namespace[0];
                     }
                     if (data.errors.name) {
                         $scope.name_error = data.errors.name[0];
                     }
                 }
        });
    }

    $scope.schedule_validation = function () {
        $timeout.cancel(validate_namespace_name_timeout);
        validate_namespace_name_timeout = $timeout(validate_namespace_and_name, 500);
    }

    $scope.namespace_changed = function (str) {
        $scope.namespace = str;
        $scope.schedule_validation();
    };

    $scope.is_name_or_namespace_were_changed = function () {
        return ($scope.orig_name && $scope.orig_name != $scope.name) || ($scope.orig_namespace && $scope.orig_namespace != $scope.namespace);
    }
});

