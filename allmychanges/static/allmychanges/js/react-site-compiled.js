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


/***/ },
/* 1 */
/***/ function(module, exports, __webpack_require__) {

	var PackageSelector = __webpack_require__(4)

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

	var ReportButton = __webpack_require__(3)

	module.exports = {
	    render: function () {
	        $('.report-button').each(function (idx, element) {
	            React.render(
	                React.createElement(ReportButton, {changelog_id: element.dataset['changelogId']}),
	                element);
	        });
	    }
	}


/***/ },
/* 3 */
/***/ function(module, exports, __webpack_require__) {

	module.exports = React.createClass({displayName: 'exports',
	    getInitialState: function () {
	        return {show_popup: false,
	                body_callback_installed: false};
	    },
	    handle_switcher_click: function (e) {
	        console.log('Switcher click');
	        e.nativeEvent.stopImmediatePropagation();
	        e.preventDefault();

	        if (this.state.body_callback_installed == false) {
	            $(document).click(function() {
	                this.setState({show_popup: false});
	                console.log('Hiding from body click');
	            }.bind(this));
	            this.setState({body_callback_installed: true});
	        }

	        if (this.state.show_popup) {
	            this.setState({show_popup: false});
	        } else {
	            this.setState({show_popup: true});
	        }
	    },
	    handle_popup_click: function (e) {
	        console.log('Popup click');
	        e.nativeEvent.stopImmediatePropagation();
	    },
	    handle_post: function (e) {
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
	            }.bind(this),
	            error: function(xhr, status, err) {
	                console.error(this.props.url, status, err.toString());
	            }.bind(this)
	        });
	    },
	    render: function() {
	        var popup;
	        if (this.state.show_popup) {
	            popup = React.createElement("div", {className: "popup", onClick: this.handle_popup_click}, 
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
	                  React.createElement("textarea", {className: "textarea", ref: "comment", placeholder: "Please, describe issue here"}), React.createElement("br", null), 
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
	        return  (React.createElement("div", {className: "dropdown"}, React.createElement("button", {className: "button", onClick: this.handle_switcher_click}, React.createElement("i", {className: "fa fa-exclamation-circle fa-lg", style: {color: '#D9534F', marginRight: '5px'}}), "Report"), popup));
	    }
	});


/***/ },
/* 4 */
/***/ function(module, exports, __webpack_require__) {

	var Package = __webpack_require__(5)

	module.exports = React.createClass({displayName: 'exports',
	    getInitialState: function () {
	        return {packages: []};
	    },
	    componentDidMount: function() {
	        $.ajax({
	            url: this.props.url,
	            dataType: 'json',
	            success: function(data) {
	                this.setState({packages: data.results});
	            }.bind(this),
	            error: function(xhr, status, err) {
	                console.error(this.props.url, status, err.toString());
	            }.bind(this)
	        });
	    },
	    render: function() {
	        var packages_list = this.state.packages.map(function (package) {
	            return (
	                React.createElement(Package, {key: package.id, 
	                         changelog_id: package.id, 
	                         namespace: package.namespace, 
	                         name: package.name, 
	                         versions: package.versions})
	            );
	        });
	        return (
	            React.createElement("ul", {className: "package-selector"}, 
	                packages_list
	            )
	        );
	    }
	});


/***/ },
/* 5 */
/***/ function(module, exports, __webpack_require__) {

	TrackButton = __webpack_require__(6)

	module.exports = React.createClass({displayName: 'exports',
	  render: function() {
	      var versions = this.props.versions.map(function(version) {
	          return  (
	                  React.createElement("li", {className: "package-selector__version", key: version.number}, 
	                    React.createElement("span", {className: "package-selector__number"}, version.number), 
	                    React.createElement("span", {className: "package-selector__date"}, "Released at ", version.date)
	                  )
	          );
	      });

	    var url = '/p/' + this.props.namespace + '/' + this.props.name + '/';
	    return (
	    React.createElement("li", {className: "package-selector__item"}, 
	    React.createElement("div", {className: "package-selector__package"}, 
	      React.createElement("h1", {className: "package-selector__title"}, React.createElement("a", {href: url}, this.props.namespace, "/", this.props.name)), 
	      React.createElement("ul", {className: "package-selector__versions"}, 
	            versions
	      ), 
	      React.createElement(TrackButton, {changelog_id: this.props.changelog_id})
	    )
	    )
	    );
	  }
	});


/***/ },
/* 6 */
/***/ function(module, exports, __webpack_require__) {

	module.exports = React.createClass({displayName: 'exports',
	    getInitialState: function () {
	        return {tracked: false};
	    },
	    handle_click: function (e) {
	        e.preventDefault();
	        $.ajax({
	            url: '/v1/changelogs/' + this.props.changelog_id + '/track/',
	            method: 'POST',
	            dataType: 'json',
	            headers: {'X-CSRFToken': $.cookie('csrftoken')},
	            success: function(data) {
	                this.setState({tracked: true});
	            }.bind(this),
	            error: function(xhr, status, err) {
	                console.error('Unable to track changelog', status, err.toString());
	            }.bind(this)
	        });
	    },
	    render: function() {
	        if (this.state.tracked) {
	            return (React.createElement("button", {className: "package-select__track-button package-select__track-button_tracked"}, "Tracked"));
	        } else {
	            return (React.createElement("button", {className: "package-select__track-button", onClick: this.handle_click}, "Track"));
	        }
	    }
	});


/***/ }
/******/ ])