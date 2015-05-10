/******/ (function(modules) { // webpackBootstrap
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId])
/******/ 			return installedModules[moduleId].exports;
/******/
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			exports: {},
/******/ 			id: moduleId,
/******/ 			loaded: false
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.loaded = true;
/******/
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/
/******/
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = modules;
/******/
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = installedModules;
/******/
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "";
/******/
/******/ 	// Load entry module and return exports
/******/ 	return __webpack_require__(0);
/******/ })
/************************************************************************/
/******/ ([
/* 0 */
/***/ function(module, exports, __webpack_require__) {

	__webpack_require__(1).render()
	__webpack_require__(2).render()
	__webpack_require__(3).render()
	__webpack_require__(4).render()
	__webpack_require__(5).render()


/***/ },
/* 1 */
/***/ function(module, exports, __webpack_require__) {

	var PackageSelector = __webpack_require__(17)

	module.exports = {
	    render: function () {
	        var element = document.getElementById('login-index');

	        if (element !== null) {
	            React.render(
	                React.createElement(PackageSelector, {url: "/v1/landing-package-suggest/?limit=20&versions_limit=5"}),
	                element);
	        }
	    }
	}


/***/ },
/* 2 */
/***/ function(module, exports, __webpack_require__) {

	var LoginMenu = __webpack_require__(6)
	var ReportButton = __webpack_require__(7)
	var ResolveButton = __webpack_require__(8)
	var DeleteButton = __webpack_require__(9)
	var TrackButton = __webpack_require__(10)
	var MagicPrompt = __webpack_require__(11)
	var Share = __webpack_require__(12)
	var Notifications = __webpack_require__(13)
	var FeedbackForm = __webpack_require__(14)


	module.exports = {
	    render: function () {
	        $('.report-button').each(function (idx, element) {
	            React.render(
	                React.createElement(ReportButton, {changelog_id: element.dataset['changelogId']}),
	                element);
	        });

	        $('.track-button-container').each(function (idx, element) {
	            React.render(
	                React.createElement(TrackButton, {changelog_id: element.dataset['changelogId'], 
	                             tracked: element.dataset['tracked'], 
	                             username: username, 
	                             num_trackers: element.dataset['numTrackers']}),
	                element);
	        });

	        $('.resolve-button-container').each(function (idx, element) {
	            React.render(
	                React.createElement(ResolveButton, {issue_id: element.dataset['issueId']}),
	                element);
	        });
	        $('.delete-button-container').each(function (idx, element) {
	            React.render(
	                React.createElement(DeleteButton, {version_id: element.dataset['versionId']}),
	                element);
	        });
	        $('.magic-prompt-container').each(function (idx, element) {
	            React.render(
	                React.createElement(MagicPrompt, null),
	                element);
	        });
	        $('.login-menu-container').each(function (idx, element) {
	            React.render(
	                React.createElement(LoginMenu, {opened: element.dataset['opened'], 
	                           username: element.dataset['username']}),
	                element);
	        });
	        $('.notifications-container').each(function (idx, element) {
	            React.render(
	                React.createElement(Notifications, null),
	                element);
	        });
	        $('.feedback-form-container').each(function (idx, element) {
	            React.render(
	                React.createElement(FeedbackForm, {page: element.dataset['page']}),
	                element);
	        });
	    }
	}


/***/ },
/* 3 */
/***/ function(module, exports, __webpack_require__) {

	var Share = __webpack_require__(12)

	module.exports = {
	    render: function () {
	        $('.share-badge-container').each(function (idx, element) {
	            React.render(
	                React.createElement(Share, {namespace: element.dataset['namespace'], 
	                       name: element.dataset['name']}),
	                element);
	        });
	    }
	}


/***/ },
/* 4 */
/***/ function(module, exports, __webpack_require__) {

	var Promo = __webpack_require__(15)

	module.exports = {
	    render: function () {
	        $('.ios-promo-container').each(function (idx, element) {
	            React.render(React.createElement(Promo, null), element);
	        });
	    }
	}


/***/ },
/* 5 */
/***/ function(module, exports, __webpack_require__) {

	var Landing = __webpack_require__(16)

	module.exports = {
	    render: function () {
	        $('.landing-page-container').each(function (idx, element) {
	            React.render(React.createElement(Landing, null), element);
	        });
	    }
	}


/***/ },
/* 6 */
/***/ function(module, exports, __webpack_require__) {

	var metrika = __webpack_require__(18)

	module.exports = React.createClass({displayName: 'exports',
	    getInitialState: function () {
	        return {opened: (this.props.opened == 'true')};
	    },
	    open: function () {
	        this.setState({opened: true});
	    },
	    close: function () {
	        this.setState({opened: false});
	    },
	    render: function() {
	        if (this.state.opened) {
	            return (React.createElement("div", {className: "login-menu"}, 
	                      React.createElement("a", {className: "login-menu__button", 
	                              onClick: this.close, 
	                              title: "Click to close a menu."}, this.props.username), 
	                      React.createElement("ul", {className: "login-menu__items"}, 
	                        React.createElement("li", null, React.createElement("a", {href: "/account/settings/"}, "Settings")), 
	                        React.createElement("li", null, React.createElement("a", {href: "/logout/?next=/"}, "Logout"))
	                      )
	                    ));
	        } else {
	            return (React.createElement("div", {className: "login-menu"}, 
	                      React.createElement("a", {className: "login-menu__button", 
	                              onClick: this.open, 
	                              title: "Click to open a menu."}, this.props.username)
	                    ));
	        }
	    }
	});


/***/ },
/* 7 */
/***/ function(module, exports, __webpack_require__) {

	var metrika = __webpack_require__(18)

	module.exports = React.createClass({displayName: 'exports',
	    getInitialState: function () {
	        return {show_popup: false,
	                body_callback_installed: false};
	    },
	    handle_switcher_click: function (e) {
	        UserStory.log(["user clicked report button"], ["buttons.report"]);
	        metrika.reach_goal('CLICK-REPORT-BUTTON');

	        e.nativeEvent.stopImmediatePropagation();
	        e.preventDefault();

	        if (this.state.body_callback_installed == false) {
	            $(document).click(function() {
	                this.setState({show_popup: false});
	                UserStory.log(["hiding from body click"], ["buttons.report"]);
	            }.bind(this));
	            this.setState({body_callback_installed: true});
	        }

	        if (this.state.show_popup) {
	            this.setState({show_popup: false});
	        } else {
	            this.setState({show_popup: true});
	        }
	    },
	    handle_form_keypress: function (e) {
	        if (e.key == 'Enter' && (e.metaKey || e.ctrlKey)) {
	            this.handle_post(e);
	        }
	    },
	    handle_popup_click: function (e) {
	        UserStory.log(["popup click"], ["buttons.report"]);
	        e.nativeEvent.stopImmediatePropagation();
	    },
	    handle_post: function (e) {
	        UserStory.log(["sending feedback to the server"], ["report.button"]);
	        metrika.reach_goal('REPORT');
	        e.preventDefault();
	        var type = this.refs.type.getDOMNode().value.trim();
	        var comment = this.refs.comment.getDOMNode().value.trim();

	        $.ajax({
	            url: '/v1/issues/',
	            dataType: 'json',
	            type: 'POST',
	            headers: {'X-CSRFToken': $.cookie('csrftoken')},
	            data: {changelog: this.props.changelog_id,
	                   type: type,
	                   comment: comment},
	            success: function(data) {
	                this.setState({show_popup: false});
	                PubSub.publish('show-info', 'Thank you for reporing about the issue. We\'ll fix it as soon as possible.');
	            }.bind(this),
	            error: function(xhr, status, err) {
	                console.error(this.props.url, status, err.toString());
	            }.bind(this)
	        });
	    },
	    render: function() {
	        var popup;
	        if (this.state.show_popup) {
	            popup = React.createElement("div", {className: "report-button__popup", onClick: this.handle_popup_click}, 
	                React.createElement("form", {className: "form", onSubmit: this.handle_post}, 
	                  React.createElement("label", {htmlFor: "type"}, "Problem type:"), 
	                  React.createElement("select", {className: "select-box", ref: "type", placeholder: "Some issue type"}, 
	                    React.createElement("option", {value: "other"}, "---"), 
	                    React.createElement("option", {value: "version-missing"}, "Some version is missing"), 
	                    React.createElement("option", {value: "wrong-version"}, "I found version which is wrong"), 
	                    React.createElement("option", {value: "wrong-dates"}, "There is some problem with dates"), 
	                    React.createElement("option", {value: "wrong-version-content"}, "A problem with content parsing"), 
	                    React.createElement("option", {value: "other"}, "Other issue")
	                  ), React.createElement("br", null), 
	                  React.createElement("textarea", {className: "textarea", 
	                            ref: "comment", 
	                            onKeyPress: this.handle_form_keypress, 
	                            placeholder: "Please, describe issue here"}
	                  ), React.createElement("br", null), 
	                  React.createElement("table", {className: "form-buttons"}, 
	                    React.createElement("tr", null, 
	                      React.createElement("td", {className: "form-buttons__back"}), 
	                      React.createElement("td", {className: "form-buttons__next"}, 
	                        React.createElement("button", {className: "button _good"}, "Report")
	                      )
	                    )
	                   )
	                )
	            );
	        }
	        return  (React.createElement("div", {className: "report-button__dropdown"}, React.createElement("button", {className: "button", onClick: this.handle_switcher_click, title: "If you found some issues with this changelog, please file this issue."}, React.createElement("i", {className: "fa fa-exclamation-circle fa-lg", style: {color: '#D9534F', marginRight: '5px'}}), "Report"), popup));
	    }
	});


/***/ },
/* 8 */
/***/ function(module, exports, __webpack_require__) {

	module.exports = React.createClass({displayName: 'exports',
	    getInitialState: function () {
	        return {resolved: false};
	    },
	    handle_click: function (e) {
	        e.preventDefault();
	        $.ajax({
	            url: '/v1/issues/' + this.props.issue_id + '/resolve/',
	            method: 'POST',
	            dataType: 'json',
	            headers: {'X-CSRFToken': $.cookie('csrftoken')},
	            success: function(data) {
	                this.setState({resolved: true});
	            }.bind(this),
	            error: function(xhr, status, err) {
	                console.error('Unable to resolve issue', status, err.toString());
	            }.bind(this)
	        });
	    },
	    render: function() {
	        if (this.state.resolved) {
	            return (React.createElement("button", {className: "button", disabled: "disabled"}, "Resolved"));
	        } else {
	            return (React.createElement("button", {className: "button", onClick: this.handle_click}, "Resolve"));
	        }
	    }
	});


/***/ },
/* 9 */
/***/ function(module, exports, __webpack_require__) {

	module.exports = React.createClass({displayName: 'exports',
	    getInitialState: function () {
	        return {deleted: false};
	    },
	    handle_click: function (e) {
	        e.preventDefault();
	        $.ajax({
	            url: '/v1/versions/' + this.props.version_id + '/',
	            method: 'DELETE',
	            dataType: 'json',
	            headers: {'X-CSRFToken': $.cookie('csrftoken')},
	            success: function(data) {
	                this.setState({deleted: true});
	            }.bind(this),
	            error: function(xhr, status, err) {
	                console.error('Unable to delete version', status, err.toString());
	            }.bind(this)
	        });
	    },
	    render: function() {
	        if (this.state.deleted) {
	            return (React.createElement("button", {className: "button", disabled: "disabled"}, "Deleted"));
	        } else {
	            return (React.createElement("button", {className: "button", onClick: this.handle_click}, "Delete"));
	        }
	    }
	});


/***/ },
/* 10 */
/***/ function(module, exports, __webpack_require__) {

	var metrika = __webpack_require__(18)

	module.exports = React.createClass({displayName: 'exports',
	    getInitialState: function () {
	        UserStory.log(["init track button for [this.props.username=", this.props.username, "]"], ["buttons.track"]);
	        return {tracked: (this.props.tracked == 'true'),
	                show_popup: false};
	    },
	    perform_action: function(action, state_after) {
	        UserStory.log(["performing action [action=", action, "]"], ["buttons.track"]);
	        $.ajax({
	            url: '/v1/changelogs/' + this.props.changelog_id + '/' + action + '/',
	            method: 'POST',
	            dataType: 'json',
	            headers: {'X-CSRFToken': $.cookie('csrftoken')},
	            success: function(data) {
	                metrika.reach_goal(action.toUpperCase());

	                if (this.props.on_track !== undefined) {
	                    this.props.on_track();
	                }

	                this.setState({tracked: state_after});

	                if (this.props.username == '') {
	                    UserStory.log(["if user is anonymous, then show him a fullscreen popup"], ["buttons.track"]);
	                    this.setState({show_popup: true});
	                }
	            }.bind(this),
	            error: function(xhr, status, err) {
	                console.error('Unable to perform action ' + action + ' on changelog', status, err.toString());
	            }.bind(this)
	        });
	    },
	    track: function (e) {
	        e.preventDefault();
	        this.perform_action('track', true);
	    },
	    untrack: function (e) {
	        e.preventDefault();
	        this.perform_action('untrack', false);
	    },
	    handle_popup_click: function (e) {
	        UserStory.log(["popup click"], ["buttons.report"]);
	        e.nativeEvent.stopImmediatePropagation();
	    },
	    render: function() {
	        var num_trackers = this.props.num_trackers;
	        var popup;

	        if (this.state.show_popup) {
	            popup = (
	                React.createElement("div", {className: "modal-popup", onClick: this.handle_popup_click}, 
	                    React.createElement("div", {className: "modal-popup__content modal-popup__please-login"}, 
	                      React.createElement("p", null, "Good job! You\\'ve made first step, tracking this package."), 
	                      React.createElement("p", null, "Now, to receive notifications about future updates, you need to login via:"), 
	                      React.createElement("p", null, React.createElement("a", {className: "button _good _large", href: "/login/twitter/"}, React.createElement("i", {className: "fa fa-twitter fa-lg"}), " Twitter"), " or ", React.createElement("a", {className: "button _good _large", href: "/login/twitter/"}, React.createElement("i", {className: "fa fa-github fa-lg"}), " GitHub"))
	                    )
	                ));
	        }


	        var trackers_msg;
	        if (num_trackers) {
	            var msg;
	            if (num_trackers && num_trackers != '0') {
	                msg = num_trackers + ' followers';
	                if (num_trackers == '1') {
	                    msg = 'one follower';
	                }
	            } else {
	                msg = 'nobody follows it, be the first!';
	            }
	            trackers_msg = React.createElement("div", {className: "track-button__message"}, msg);
	        }

	        if (this.state.tracked) {
	            return (React.createElement("div", {className: "track-button"}, 
	                      React.createElement("button", {className: "button _bad", 
	                              onClick: this.untrack, 
	                              title: "Click to unsubscribe from this package."}, "Unfollow"), 
	                      popup
	                    ));
	        } else {
	            return (React.createElement("div", {className: "track-button"}, 
	                      React.createElement("button", {className: "button _good", 
	                              onClick: this.track, 
	                              title: "Click to receive notifications about new versions."}, "Follow"), 
	                      trackers_msg
	                    ));
	        }
	    }
	});


/***/ },
/* 11 */
/***/ function(module, exports, __webpack_require__) {

	// uses jquery typeahead plugin:
	// http://twitter.github.io/typeahead.js/

	module.exports = React.createClass({displayName: 'exports',
	    componentDidMount: function(){
	        var element = this.getDOMNode();
	        var input_spinner = new Spinner({left: '50%', top: '20px'}); 
	        var fetch_timer;
	        var fetch_suggestions = function(query, cb) {
	            clearTimeout(fetch_timer);
	            fetch_timer = setTimeout(function () {
	                really_fetch_suggestions(query, cb)
	            }, 500);
	        }
	        var really_fetch_suggestions = function(query, cb) {
	            input_spinner.spin($('.input-spin-wrapper')[0]);

	            $.get('/v1/search-autocomplete/', {q: query}, function(data) {
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
	                        item.value = item.source;
	                    }
	                });

	                cb(results);
	            });
	        };

	        var show_by_type = {
	            'package': _.template('<div class="magic-prompt__suggest-item"><%- namespace %>/<%- name %> <span class="magic-prompt__suggest-item-info">package</span></div>'),
	            'namespace': _.template('<div class="magic-prompt__suggest-item"><%- namespace %> <span class="magic-prompt__suggest-item-info">namespace</span></div>'),
	            'add-new': _.template('<div class="magic-prompt__suggest-item"><span class="magic-prompt__suggest-item-info button _good">add new</span><%- namespace %>/<%- name %><br/><span class="magic-prompt__suggest-item-source"><%- source %></span></div>')
	        }

	        var show_suggestion = function (obj) {
	            return show_by_type[obj.type](obj);
	        }

	        $(element).find('.magic-prompt__input').typeahead(
	            {
	                minLength: 3,
	                highlight: true
	            },
	            {
	                name: 'magic-prompt',
	                source: fetch_suggestions,
	                templates: {
	                    empty: '<div class="magic-prompt__no-matches">No matches found</div>',
	                    suggestion: show_suggestion
	                }
	        }).on('typeahead:selected', function(ev, option){
	            window.location = option.url;
	        }).focus();
	    },
	    
	    componentWillUnmount: function(){
	        var element = this.getDOMNode();
	        $(element).find('.magic-prompt__input').typeahead('destroy');
	    },

	    render: function(){
	        return (
	            React.createElement("div", {className: "magic-prompt"}, 
	                React.createElement("form", {action: "/search/", method: "GET"}, 
	                  React.createElement("input", {type: "search", name: "q", ref: "input", 
	                         className: "magic-prompt__input", 
	                         placeholder: "Search packages and namespaces"}), React.createElement("div", {className: "input-spin-wrapper"}), 
	                  React.createElement("input", {type: "submit", className: "button _good _large magic-prompt__submit", value: "Search"})
	                )
	            )
	        );
	    }
	});


/***/ },
/* 12 */
/***/ function(module, exports, __webpack_require__) {

	module.exports = React.createClass({displayName: 'exports',
	    getInitialState: function () {
	        return {active_tab: 'markdown'};
	    },
	    show: function (tab) {
	        return function () {
	            this.setState({active_tab: tab});
	        }.bind(this);
	    },
	    render: function() {
	        var base_url = window.location.origin + '/p/' + this.props.namespace + '/' + this.props.name + '/';
	        var package_url = base_url + '?utm_source=badge';
	        var image_url = base_url + 'badge/';
	        var tab_classes = {}
	        tab_classes[this.state.active_tab] = 'tab_active';

	        var get_content = function (tab) {
	            var snippets = {
	                markdown: '[![changelog](' + image_url + ')](' + package_url + ')',
	                rst: '.. image:: ' + image_url + '\n   :target: ' + package_url,
	                html: '<a href="' + package_url + '"><img title="changelog" src="' + image_url + '"/></a>'};
	            var num_rows = {markdown: 1, rst: 2, html: 1};
	            return (React.createElement("textarea", {readOnly: "1", 
	                              wrap: "off", 
	                              rows: num_rows[tab], 
	                              className: "text-input share-badge__text", 
	                              value: snippets[tab]}));
	        }

	        return (
	React.createElement("table", {className: "share-badge"}, 
	  React.createElement("tbody", null, 
	    React.createElement("tr", null, 
	      React.createElement("td", null), 
	      React.createElement("td", null, 
	        React.createElement("ul", {className: "share-badge__tabs"}, 
	          React.createElement("li", {className: "tab " + tab_classes.markdown, onClick: this.show('markdown')}, "markdown"), 
	          React.createElement("li", {className: "tab " + tab_classes.rst, onClick: this.show('rst')}, "reST"), 
	          React.createElement("li", {className: "tab " + tab_classes.html, onClick: this.show('html')}, "html")
	        )
	      )
	    ), 

	    React.createElement("tr", null, 
	      React.createElement("td", null, 
	        React.createElement("img", {className: "share-badge__example", src: image_url})
	      ), 
	      React.createElement("td", null, 
	        get_content(this.state.active_tab)
	      )
	    )
	  )
	));
	    }
	});


/***/ },
/* 13 */
/***/ function(module, exports, __webpack_require__) {

	// пример использования нотификаций:
	// PubSub.publish('show-info', 'Привет мир!');

	module.exports = React.createClass({displayName: 'exports',
	    componentDidMount: function() {
	        PubSub.subscribe('show-info', this.newItem);
	        PubSub.subscribe('show-warning', this.newItem);
	        $(document).trigger('notifications-mounted');
	    },
	    newItem: function (msg, data) {
	        this.counter += 1;
	        var item = {'id': this.counter,
	                    'text': data}
	        
	        if (msg == 'show-warning') {
	            item['class'] = 'warning';
	        } else {
	            item['class'] = 'info';
	        }

	        var items = this.state.items;
	        items[items.length] = item;
	        this.setState({show: true, items: items});
	    },
	    getInitialState: function () {
	        this.counter = 0;
	        return {show: false, items: []};
	    },
	    render: function() {
	        var notifications;
	        var closeItem2 = function (item_id) {
	            return function() {
	                UserStory.log(["closing item [item_id=", item_id, "]"], ["notifications"]);
	                items = this.state.items;
	                items = _.filter(items, function(item) {return item.id != item_id});
	                this.setState({items: items});
	            }.bind(this);
	        }.bind(this);

	        if (this.state.show) {
	            notifications = _.map(this.state.items,
	                                function(item) {
	                                        return React.createElement("li", {className: "notifications__item notifications__" + item.class, key: item.id}, React.createElement("div", {className: "notifications__close-button", onClick: closeItem2(item.id)}, "+"), item.text)
	                                });
	        }
	        return  (React.createElement("ul", {className: "notifications"}, notifications));
	    }
	});


/***/ },
/* 14 */
/***/ function(module, exports, __webpack_require__) {

	var metrika = __webpack_require__(18)

	module.exports = React.createClass({displayName: 'exports',
	    getInitialState: function () {
	        return {enable_submit: false};
	    },
	    handle_form_keypress: function (e) {
	        if (e.key == 'Enter' && (e.metaKey || e.ctrlKey)) {
	            this.handle_post(e);
	        }
	    },
	    handle_comment_change: function (e) {
	        this.setState({
	            enable_submit: (this.refs.comment.getDOMNode().value.trim().length > 0)});
	    },
	    handle_post: function (e) {
	        UserStory.log(["sending feedback to the server"], ["report.button"]);
	        metrika.reach_goal('REPORT');
	        e.preventDefault();
	        var comment = this.refs.comment.getDOMNode().value.trim();
	        var email = this.refs.email.getDOMNode().value.trim();

	        $.ajax({
	            url: '/v1/issues/',
	            dataType: 'json',
	            type: 'POST',
	            headers: {'X-CSRFToken': $.cookie('csrftoken')},
	            data: {type: 'feedback',
	                   email: email,
	                   page: this.props.page,
	                   comment: comment},
	            success: function(data) {
	                this.setState({show_popup: false});
	                this.refs.comment.getDOMNode().value = '';
	                PubSub.publish('show-info', 'Thank you for sharing your ideas!');
	            }.bind(this),
	            error: function(xhr, status, err) {
	                console.error(this.props.url, status, err.toString());
	            }.bind(this)
	        });
	    },
	    render: function() {
	        var form = React.createElement("form", {className: "form", onSubmit: this.handle_post}, 
	            React.createElement("input", {ref: "email", className: "text-input", placeholder: "Your email will let us answer you, but it is optional.", type: "text", maxLength: "100"}), 
	            React.createElement("textarea", {className: "textarea", 
	                      ref: "comment", 
	                      onKeyPress: this.handle_form_keypress, 
	                      onChange: this.handle_comment_change, 
	                      placeholder: "Please, describe your ideas here."}
	            ), React.createElement("br", null), 
	            React.createElement("table", {className: "form-buttons"}, 
	               React.createElement("tr", null, 
	                  React.createElement("td", {className: "form-buttons__back"}), 
	                  React.createElement("td", {className: "form-buttons__next"}, 
	                     React.createElement("button", {className: "button _good", 
	                             disabled: this.state.enable_submit ? false: "disabled"}, "Send")
	                  )
	               )
	            )
	        );
	        return  form;
	    }
	});


/***/ },
/* 15 */
/***/ function(module, exports, __webpack_require__) {

	var metrika = __webpack_require__(18)

	// uses jquery typeahead plugin:
	// http://twitter.github.io/typeahead.js/

	module.exports = React.createClass({displayName: 'exports',
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
	            UserStory.log(["adding app to the list"], ["ios"]);
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
	                        UserStory.log(["update the digest example"], ["ios"]);
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
	            return (React.createElement("li", {key: obj.source, className: "ios-promo__selected-app"}, React.createElement("img", {className: "ios-promo__thumb", src: icon, title: obj.name})));
	        }

	        var selected_apps = _.map(this.state.selected_apps, process_app);

	        var login_link;
	        if (this.state.selected_apps.length > 0) {
	            if (this.state.digest_loaded) {
	                login_link = (React.createElement("div", {className: "ios-promo__login"}, React.createElement("p", {className: "ios-promo__text"}, "Good job! Now, please, login with ", React.createElement("a", {className: "button _good _large", href: "/login/twitter/"}, React.createElement("i", {className: "fa fa-twitter fa-lg"}), " Twitter"), " to receive notifications about future updates.")));
	            }
	        } else {
	            login_link = (React.createElement("div", {className: "ios_promo__login"}, React.createElement("p", {className: "ios-promo__text"}, "Please, ", React.createElement("span", {className: "ios-promo__highlight"}, "select one or more applications"), " to continue.")));
	        }

	        return (
	            React.createElement("div", {className: "ios-promo"}, 
	                React.createElement("div", {className: "ios-promo__input-wrapper"}, 
	                  React.createElement("input", {type: "search", name: "q", ref: "input", 
	                         className: "ios-promo__input", 
	                         placeholder: "Search iOS apps and add them to the list"}), React.createElement("div", {className: "input-spin-wrapper"}), 
	                  React.createElement("ul", {className: "ios-promo__selected-apps"}, 
	                    selected_apps
	                  )
	                ), 
	                login_link, 
	                React.createElement("div", {className: "ios-promo__digest"})
	            )
	        );
	    }
	});


/***/ },
/* 16 */
/***/ function(module, exports, __webpack_require__) {

	var PackageSelector = __webpack_require__(17)

	module.exports = React.createClass({displayName: 'exports',
	    getInitialState: function () {
	        UserStory.log(["init landing page"], ["landing"]);
	        return {num_tracked: 0};
	    },
	    componentDidMount: function() {
	    },
	    render: function() {
	        return (React.createElement("div", {className: "landing-page"}, 
	                  React.createElement(PackageSelector, {url: "/v1/landing-package-suggest/?limit=1&versions_limit=5"})
	                ));
	    }
	});


/***/ },
/* 17 */
/***/ function(module, exports, __webpack_require__) {

	var Package = __webpack_require__(19)
	var metrika = __webpack_require__(18)

	module.exports = React.createClass({displayName: 'exports',
	    getInitialState: function () {
	        return {packages: [],
	                tracked: []};
	    },
	    load_package: function () {
	        $.ajax({
	            url: this.props.url,
	            dataType: 'json',
	            success: function(data) {
	                var results = data.results;
	                if (results.length > 0) {
	                    this.setState({package: results[0]});
	                } else {
	                    // TODO: somethings
	                }
	            }.bind(this),
	            error: function(xhr, status, err) {
	                console.error(this.props.url, status, err.toString());
	            }.bind(this)
	        });

	    },
	    componentDidMount: function() {
	        this.load_package();
	    },
	    render: function() {
	        var track_handler = function (changelog) {
	            var tracked = this.state.tracked;
	            tracked[tracked.length] = changelog;

	            if (tracked.length == 1) {
	                metrika.reach_goal('LAND-TRACK-1');
	            }
	            if (tracked.length == 3) {
	                metrika.reach_goal('LAND-TRACK-3');
	            }
	            if (tracked.length == 5) {
	                metrika.reach_goal('LAND-TRACK-5');
	            }

	            this.setState({tracked: tracked});
	            this.load_package();
	        }.bind(this);

	        var skip_handler = function () {
	            this.load_package();
	        }.bind(this);

	        var pkg_obj;
	        var pkg = this.state.package;
	        if (pkg !== undefined) {
	            pkg_obj = React.createElement(Package, {key: pkg.id, 
	                           changelog_id: pkg.id, 
	                           namespace: pkg.namespace, 
	                           name: pkg.name, 
	                           description: pkg.description, 
	                           versions: pkg.versions, 
	                           track_handler: track_handler, 
	                           skip_handler: skip_handler});
	        }

	        var tracked = _.map(this.state.tracked,
	                            function (changelog) {
	                                return (
	            React.createElement("li", {key: changelog.id}, changelog.namespace, "/", changelog.name));});

	        var tracked_msg;
	        if (tracked.length > 0) {
	            tracked_msg = (React.createElement("div", {className: "package-selector__tracked-msg"}, 
	                React.createElement("p", null, "You are following these packages:"), 
	                React.createElement("ul", null, tracked), 
	                React.createElement("p", null, "To receive notifications on future releases, please, ", React.createElement("br", null), "login with ", React.createElement("a", {className: "button _green _large", href: "/login/github/", id: "package-selector__login-button-id"}, React.createElement("i", {className: "fa fa-github fa-lg"}), " GitHub"), " or ", React.createElement("a", {className: "button _blue _large", href: "/login/twitter/"}, React.createElement("i", {className: "fa fa-twitter fa-lg"}), " Twitter"))
	            ));

	            // when first package is tracked, scroll down
	            // to show the buttons
	            if (tracked.length == 1) {
	                setTimeout(function() {
	                    $('html, body').animate({
	                        scrollTop: $("#package-selector__login-button-id").offset().top
	                    }, 2000)
	                }, 500);
	            }
	        }
	                                        
	        return (
	            React.createElement("div", {className: "package-selector"}, 
	                pkg_obj, 
	                tracked_msg
	            )
	        );
	    }
	});


/***/ },
/* 18 */
/***/ function(module, exports, __webpack_require__) {

	module.exports = {
	    reach_goal: function(name) {
	        if (window.yaCounter !== undefined) {
	            UserStory.log(["registering goal [name=", name, "]"], ["metrika.reach_goal"]);
	            window.yaCounter.reachGoal(name);
	        }
	    }
	}


/***/ },
/* 19 */
/***/ function(module, exports, __webpack_require__) {

	TrackButton = __webpack_require__(10)
	SkipButton = __webpack_require__(20)

	module.exports = React.createClass({displayName: 'exports',
	  render: function() {
	    var changelog_id = this.props.changelog_id;

	    var on_track = function () {
	        this.props.track_handler({id: this.props.changelog_id,
	                                  namespace: this.props.namespace,
	                                  name: this.props.name});
	    }.bind(this);

	    var url = '/p/' + this.props.namespace + '/' + this.props.name + '/';
	    return (
	    React.createElement("div", {className: "package-selector__package"}, 
	      React.createElement("h1", {className: "package-selector__title"}, React.createElement("a", {href: url}, this.props.namespace, "/", this.props.name)), 
	      React.createElement("h2", {className: "package-selector__description"}, this.props.description), 
	      React.createElement("div", {className: "package-selector__versions-wrapper"}, 
	        React.createElement("div", {className: "package-selector__versions-grad"}), 
	        React.createElement("iframe", {className: "package-selector__versions", scrolling: "no", src: "/package-selector-versions/?changelog=" + this.props.changelog_id})
	      ), 
	      React.createElement("div", {className: "package-selector__buttons"}, 
	        React.createElement(TrackButton, {changelog_id: this.props.changelog_id, num_trackers: false, on_track: on_track}), 
	        React.createElement(SkipButton, {changelog_id: this.props.changelog_id, on_skip: this.props.skip_handler})
	      )
	    )
	    );
	  }
	});


/***/ },
/* 20 */
/***/ function(module, exports, __webpack_require__) {

	var metrika = __webpack_require__(18)

	module.exports = React.createClass({displayName: 'exports',
	    perform_action: function(action) {
	        UserStory.log(["performing action [action=", action, "]"], ["buttons.skip"]);
	        $.ajax({
	            url: '/v1/changelogs/' + this.props.changelog_id + '/' + action + '/',
	            method: 'POST',
	            dataType: 'json',
	            headers: {'X-CSRFToken': $.cookie('csrftoken')},
	            success: function(data) {
	                metrika.reach_goal(action.toUpperCase());

	                if (this.props.on_skip !== undefined) {
	                    this.props.on_skip();
	                }
	            }.bind(this),
	            error: function(xhr, status, err) {
	                console.error('Unable to perform action ' + action + ' on changelog', status, err.toString());
	            }.bind(this)
	        });
	    },
	    skip: function (e) {
	        e.preventDefault();
	        this.perform_action('skip', true);
	    },
	    handle_popup_click: function (e) {
	        UserStory.log(["popup click"], ["buttons.report"]);
	        e.nativeEvent.stopImmediatePropagation();
	    },
	    render: function() {
	        return (React.createElement("div", {className: "skip-button"}, 
	                    React.createElement("button", {className: "button", 
	                            onClick: this.skip, 
	                            title: "Click me to show next package."}, "Show next")
	                ));
	    }
	});


/***/ }
/******/ ])