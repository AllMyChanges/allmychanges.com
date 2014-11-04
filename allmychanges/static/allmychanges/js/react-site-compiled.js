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


/***/ },
/* 1 */
/***/ function(module, exports, __webpack_require__) {

	var PackageSelector = __webpack_require__(2)

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

	var Package = __webpack_require__(3)

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
/* 3 */
/***/ function(module, exports, __webpack_require__) {

	TrackButton = __webpack_require__(4)

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
/* 4 */
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