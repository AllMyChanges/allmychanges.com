module.exports = React.createClass({
    getInitialState: function () {
        // init add new page @add-new
        return {source: this.props.source,
                search_list: this.props.search_list,
                ignore_list: this.props.ignore_list,
                xslt: this.props.xslt,
                tracked: false,
                saving: false,
                waiting: false,
                results: null,
                problem: null};
    },
    componentDidMount: function() {
        this.form_fields = {};
        this.update_preview_callback();
    },
    can_save: function() {
        return false;
    },
    can_track: function() {
        return false;
    },
    update_preview: function() {
        // Updating preview @package-settings
    },
    onFieldChange: function(event) {
        this.form_fields[event.target.name] = event.target.value;
        // ng-change="schedule_validation()"
    },
    save: function() {
        // Saving @package-settings
    },
    save_and_track: function() {
        // Saving and tracking @package-settings
    },
    is_name_or_namespace_were_changed: function() {
        return false;
    },
    is_apply_button_disabled: function() {
        return false;
    },
    draw_table: function() {
        var xslt_editing_fields = [
                <tr><td className="new-package__xslt-label">XSLT mighty feature!</td></tr>,
                <tr>
                  <td className="new-package__xslt-wrap"><textarea placeholder="Behold XSLT\'s mighty power!" className="new-package__xslt-input" name="xslt" onChange={this.onFieldChange} disabled={this.state.waiting}></textarea></td>
                </tr>];
        if (username != 'svetlyak40wt') {
            xslt_editing_fields = [];
        }

        var save_button;
        var submit_button_disabled = !this.can_track();
        if (this.props.mode == 'edit') {
            save_button = <input type="submit" className="button _good _large magic-prompt__apply" value="Save" onClick={this.save} disabled={submit_button_disabled}/>;
        } else {
            save_button = <input type="submit" className="button _good _large magic-prompt__apply" value="Save&amp;Track" onClick={this.save_and_track} disabled={submit_button_disabled}/>;

        }

        var save_tooltip;
        if (this.can_save() && !this.state.saving) {
            save_tooltip = <span className="new-package__save-tooltip">Please, update preview to ensure that we able to get a changelog for this package.</span>;
        }

        var broken_links_warning;
        if (this.is_name_or_namespace_were_changed()) {
                broken_links_warning = (
                        <tr>
                          <td className="new-package__rename-warning" colspan="2">
                            Beware, renaming this package will broke all links to this package!
                          </td>
                        </tr>);
        }
        var namespace_error;
        if (this.state.namespace_error) {
            namespace_error = <span className="input__error">{this.state.namespace_error}</span>;
        }
        var name_error;
        if(this.state.name_error) {
            name_error = <span className="input__error">{this.state.name_error}</span>;
        }
        var description_error;
        if (this.state.description_error) {
            description_error = <span className="input__error">{this.state.description_error}</span>;
        }

        var content = (<table className="new-package__fields-table">
       <tr>
        <td className="new-package__namespace-name-cell">
          <table className="namespace-name-cell__table">
            <tr>
              <td className="namespace-name-cell__namespace-cell">
                <div className="input">
                  <label className="input__label">Namespace:</label>{namespace_error}<br/>
                  <input name="namespace" type="text" placeholder="Namespace (e.g. python, node)" onChange={this.onFieldChange} className="text-input" value={this.props.namespace}/>
                </div>
              </td>
           </tr>
           <tr>
              <td className="namespace-name-cell__name-cell">
                <div className="input">
                  <label className="input__label">Name:</label>{name_error}<br/>
                  <input name="name" type="text" placeholder="Package name" onChange={this.onFieldChange} className="text-input"/>
                </div>
              </td>
            </tr>
            {broken_links_warning}
          </table>
        </td>
        <td className="new-package__button-cell">
        </td>
       </tr>
       <tr>
         <td className="new-package__description-cell">
           <div className="input">
             <label className="input__label">Description:</label>{description_error}<br/>
             <input name="description" type="text" placeholder="Tell us what it does" onChange={this.onFieldChange} className="text-input"/>
           </div>
         </td>
       </tr>
       <tr>
         <td className="new-package__search-label">Search in these dirs and files:</td>
       </tr>
       <tr>
         <td className="new-package__search-input-wrap"><textarea placeholder="Enter here a directories where parser should search for changelogs. By default parser searches through all sources and sometimes it consider a changelog file which are not changelogs. Using this field you could narrow the search." className="new-package__search-input" name="search_list" onChange={this.onFieldChange} disabled={this.state.waiting}></textarea></td>
       </tr>
       <tr>
         <td className="new-package__ignore-label">Ignore these dirs and files:</td>
       </tr>
       <tr>
         <td className="new-package__ignore-input-wrap"><textarea placeholder="Here you could enter a list of directories to ignore during the changelog search. This is another way how to prevent robot from taking changelog-like data from wierd places." className="new-package__ignore-input" name="ignore_list" onChange={this.onFieldChange} disabled={this.state.waiting}></textarea></td>
       </tr>
       {xslt_editing_fields}
       <tr>
        <td className="new-package__button-cell">
          <input type="submit" className="button _large magic-prompt__apply" value="Update Preview" onClick={this.update_preview} disabled={this.is_apply_button_disabled()}/>
          {save_button}
          {save_tooltip}
        </td>
       </tr>
     </table>);

     return content;
    },
    wait_for_preview: function () {
        if (this.spinner === undefined) {
            // Creating a spinner @package-settings
            this.spinner = new Spinner({left: '50%', top: '30px'}).spin($('.results-spin__wrapper')[0]);
        }

        $.getJSON('/preview/' + this.props.preview_id + '/')
            .success(function(data) {
                var data = $(data);

                if (data.hasClass('please-wait')) {
                    $('.progress-text').html(data);
                    setTimeout(this.wait_for_preview, 1000);
                } else {
                    this.setState({waiting: false});

                    if (data.hasClass('package-changes')) {
//                        $('.changelog-preview').html(data);
                        this.setState({results: data});
                    } else {
//                        $('.changelog-problem').html(data);
                        this.setState({problem: data});
                    }
                }
        });
    },
    update_preview_callback: function () {
        this.setState({waiting: true,
//                       results_ready: false,
                       problem: false})
        // $scope.orig_search_list = $scope.search_list;
        // $scope.orig_ignore_list = $scope.ignore_list;
        // $scope.orig_xslt = $scope.xslt;
        // $scope.orig_changelog_source = $scope.changelog_source;

        this.wait_for_preview();
    },
    on_update_preview: function () {
        // Updating preview @package-settings
        $http.post('/preview/' + this.props.preview_id + '/',
                   {'source': this.state.source,
                    'search_list': this.state.search_list,
                    'ignore_list': this.state.ignore_list,
                    'xslt': this.state.xslt})
            .success(update_preview_callback);
    },
    render: function() {
        var content = [];
        if (this.props.mode == 'edit') {
            content.push(<label for="changelog_source">Changelog\'s source:</label>);
            content.push(<input name="changelog_source"
                                type="text"
                                placeholder="Changelog\'s source URL"
                                className="text-input"/>);
        } else {
            if (this.state.tracked) {
              content.push(<p className="plate">Horay! The package was added and is available <a href="/p/{this.props.namespace}}/{{this.props.name}}/">on a separate page</a>.</p>);
            } else {
              content.push(<p className="new-package__greeting">There is no package with source url <a className="new-package__url" href="{this.props.source}">{this.props.source}</a> yet.<br/>Please, fill in a namespace and name to track it or return back and <a href="/p/new/">add another</a> package.</p>);
            }
            
           if (username == "" && this.state.tracked) {
               content.push(<p className="plate plate_warning">To continue tracking of this package, please, login through <a href="{login_url_github}">GitHub</a> or <a href="{login_url_twitter}">Twitter</a>.</p>);
           }

           if (!this.state.tracked) {
               content = content.concat(this.draw_table());
           }

           if (this.state.waiting) {
               content.push(<div ng-show="waiting"><div className="progress-text">Please, wait while we search and process its changelog.</div>
                                <div className="results-spin"><div className="results-spin__wrapper"></div></div>
                            </div>);
           }
           if (this.state.results && !this.state.tracked) {
               content.push(<div>
                              <h1>This is the latest versions for this package</h1>
                              <div className="changelog-preview">{this.state.results}</div>
                            </div>);
           }

           if (this.state.problem) {
               content.push(<div>
                                <div className="changelog-problem">{this.state.problem}</div>
                            </div>);
           }
        }
        return (<div className="package-settings">{content}</div>);
    }
});
