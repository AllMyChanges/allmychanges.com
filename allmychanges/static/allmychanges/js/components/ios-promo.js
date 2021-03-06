var React = require('react');
var metrika = require('./metrika.js')

// uses jquery typeahead plugin:
// http://twitter.github.io/typeahead.js/

module.exports = React.createClass({
    getInitialState: function () {
        return {selected_apps: [],
                digest_loaded: false};
    },
    componentDidMount: function(){
        var element = this.getDOMNode();

        var input_spinner = new Spinner({left: '50%', top: '20px'}); 
        var fetch_timer;
        var fetch_suggestions = function(query, cb) {
            clearTimeout(fetch_timer);
            fetch_timer = setTimeout(function () {
                really_fetch_suggestions(query, cb)
            }, 1000);
        }

        var really_fetch_suggestions = function(query, cb) {
            input_spinner.spin($('.input-spin-wrapper')[0]);

            $.get('/v1/search-autocomplete/', {namespace: 'ios', q: query}, function(data) {
                input_spinner.stop();

                var results = data['results'];
                _.each(results, function(item) {
                    if (item.type == 'package') {
                        item.value = item.namespace + '/' + item.name;
                    }
                    if (item.type == 'namespace') {
                        item.value = item.namespace;
                    }
                    if (item.type == 'add-new') {
                        item.value = item.name;
                    }
                });
                cb(results);
            });
        };

        var show_suggestion = _.template('<table class="ios-promo__suggest-item"><tr><td rowspan="2"><img class="ios-promo__thumb" src="<%- icon %>"/></td><td class="ios-promo__suggest-item-name"><%- name %></td></tr><tr><td class="ios-promo__suggest-item-description"><%- description %></td></tr></table>');

        $(element).find('.ios-promo__input').typeahead(
            {
                minLength: 3,
                highlight: true
            },
            {
                name: 'ios-promo',
                displayKey: 'value',
                
                // Just a little object that implements the necessary 
                // signature to plug into typeahead.js
                source: fetch_suggestions,
                templates: {
                    empty: '<div class="ios-promo__no-matches">No matches found</div>',
                    suggestion: show_suggestion
                }
        }).focus();

        var repeat_fetch_timer;
        var digest_spinner = new Spinner({left: '50%', top: '20px'}); 

        var fetch_new_digest = function (ids) {
            clearTimeout(repeat_fetch_timer);
            this.setState({digest_loaded: false});
            $('.ios-promo__digest').html('<div class="ios-promo">Loading release notes...</div>');
            digest_spinner.spin($('.ios-promo__digest')[0]);

            $.get('/landing-digest/?long-period=yes&changelogs=' + ids.join(','))
                .success(function (data) {
                    data = data.trim();

                    if (data) {
                        digest_spinner.stop();
                        $('.ios-promo__digest').html(data);
                        this.setState({digest_loaded: true});
                    } else {
                        repeat_fetch_timer = setTimeout(
                            fetch_new_digest, 1000, ids);
                    }
                }.bind(this));
        }.bind(this);

        
        var tracked_ids = [];
        $(element).on('typeahead:selected', function(jquery, option) {
            // adding app to the list @ios-promo
            var new_apps = _.union(this.state.selected_apps, [option]);
            this.setState({selected_apps: new_apps});

            // clearing input
            $('.ios-promo__input.tt-input').typeahead('val', '');

            var track = function(resource_uri) {
                if (tracked_ids.length == 0) {
                    // регистрируем первый затреканный пакет
                    metrika.reach_goal('IOS-PROMO-TRACK-1');
                }

                var tracked_id = /.*\/(\d+)\//.exec(resource_uri)[1];

                $.ajax({
                    url: resource_uri + 'track/',
                    method: 'POST',
                    dataType: 'json',
                    headers: {'X-CSRFToken': $.cookie('csrftoken')},
                    success: function (data) {
                        // update the digest example @ios-promo
                        tracked_ids[tracked_ids.length] = tracked_id;
                        fetch_new_digest(tracked_ids);
                    },
                    error: function(xhr, status, err) {
                        console.error('Unable to track', status, err.toString());
                    }.bind(option)
                });
            }
                
            // creating a package if needed
            if (option.type == 'add-new') {
                var name = option.name;
                name = name.slice(0, name.indexOf(' by'))

                $.ajax({
                    url: '/v1/changelogs/',
                    data: {namespace: option.namespace,
                           name: name.slice(0, 80),
                           description: option.description.slice(0, 255),
                           icon: option.icon,
                           source: option.source},
                    method: 'POST',
                    dataType: 'json',
                    headers: {'X-CSRFToken': $.cookie('csrftoken')},
                    success: function (data) {track(data.resource_uri);},
                    error: function(xhr, status, err) {
                        console.error('Unable to add a package', status, err.toString());
                    }.bind(option)
                });
            } else {
                track(option.resource_uri);
            }
        }.bind(this));
    },
    
    componentWillUnmount: function(){
        var element = this.getDOMNode();
        $(element).find('.ios-promo__input').typeahead('destroy');
    },

    render: function() {
        var process_app = function(obj) {
            var icon = '';
            if (obj.icon !== undefined) {
                icon = obj.icon;
            }
            return (<li key={obj.source} className="ios-promo__selected-app"><img className="ios-promo__thumb" src={icon} title={obj.name}/></li>);
        }

        var selected_apps = _.map(this.state.selected_apps, process_app);

        var login_link;
        if (this.state.selected_apps.length > 0) {
            if (this.state.digest_loaded) {
                login_link = (<div className="ios-promo__login"><p className="ios-promo__text">Good job! Now, please, login with <a className="button _good _large" href="/login/twitter/"><i className="fa fa-twitter fa-lg"></i> Twitter</a> to receive notifications about future updates.</p></div>);
            }
        } else {
            login_link = (<div className="ios_promo__login"><p className="ios-promo__text">Please, <span className="ios-promo__highlight">select one or more applications</span> to continue.</p></div>);
        }

        return (
            <div className="ios-promo">
                <div className="ios-promo__input-wrapper">
                  <input type="search" name="q" ref="input" 
                         className="ios-promo__input" 
                         placeholder="Search iOS apps and add them to the list"/><div className="input-spin-wrapper"></div>
                  <ul className="ios-promo__selected-apps">
                    {selected_apps}
                  </ul>
                </div>
                {login_link}
                <div className="ios-promo__digest"></div>
            </div>
        );
    }
});
