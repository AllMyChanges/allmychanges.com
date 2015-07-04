// тодо:
// [X] сделать обработку ошибок namespace и name
// [X] поправить disabled стиль для белой кнопки
// [X] разобраться почему не отображается footer
// [ ] доделать сохранение результатов
// [ ] проверить как оно работает на редактировании пакета

module.exports = React.createClass({
    // this field keeps state for which preview was generated
    preview: {},
    validate_namespace_name_timeout: null,

    getInitialState: function () {
        // init add new page @add-new
        return {tracked: false,
                saving: false,
                waiting: false,
                source: this.props.source,
                search_list: this.props.search_list || '',
                ignore_list: this.props.ignore_list || '',
                xslt: this.props.xslt || '',
                results: null,
                namespace: this.props.namespace || '',
                namespace_error: !this.props.namespace && 'Please, fill this field' || '',
                name: this.props.name || '',
                name_error: !this.props.namespace && 'Please, fill this field' || '',
                problem: null};
    },
    componentDidMount: function() {
        this.save_preview_params();
        this.update_preview_callback();
    },
    save_preview_params: function () {
        this.preview = {
            source: this.state.source,
            search_list: this.state.search_list,
            ignore_list: this.state.ignore_list,
            xslt: this.state.xslt};
    },
    can_save: function() {
        var result = (this.state.saving == false
                   && this.is_apply_button_disabled()
                   && this.state.namespace_error == '' 
                   && this.state.name_error == '' 
                   && this.state.results);
        return result;
    },
    can_track: function() {
        var result = (this.can_save()
                   && this.state.tracked == false);
        return result;
    },
    update_preview: function() {
        // updating preview @update-preview

        // this field keeps state for which preview was generated
        this.save_preview_params();

        $.ajax({url: '/preview/' + this.props.preview_id + '/',
                method: 'POST',
                data: JSON.stringify(this.preview),
                contentType: 'application/json',
               headers: {'X-CSRFToken': $.cookie('csrftoken')}})
            .success(this.update_preview_callback);
    },
    on_field_change: function(event) {
        var name = event.target.name;
        // field [name] was changed @on-field-change
        var params = {}
        params[name] = event.target.value;
        this.setState(params);

        if (name == 'namespace' || name == 'name') {
            this.schedule_validation();
        }
    },
    save: function() {
        // Saving @package-settings
    },
    save_and_track: function() {
        // Saving and tracking @package-settings
    },
    is_name_or_namespace_were_changed: function() {
        return ((this.props.name && this.props.name != this.state.name) ||
                (this.props.namespace && this.props.namespace != this.state.namespace));
    },
    is_apply_button_disabled: function() {
        var result = (
            this.state.waiting == true
        || (this.preview.search_list == this.state.search_list
            && this.preview.ignore_list == this.state.ignore_list
            && this.preview.xslt == this.state.xslt
            && this.preview.source == this.state.source));
        return result;
    },
    schedule_validation: function () {
        // scheduling namespace or name validation @schedule-validation
        window.clearTimeout(this.validate_namespace_name_timeout);
        this.validate_namespace_name_timeout = window.setTimeout(this.validate_namespace_and_name, 500);
    },
    validate_namespace_and_name: function () {
        // validating namespace and name @validate-namespace-and-name
        $.get('/v1/validate-changelog-name/?namespace=' + this.state.namespace
              + '&name=' + this.state.name + '&changelog_id=' + this.props.changelog_id)
            .success(function (data) {
                var namespace_error = '';
                var name_error = '';

                if (data.errors) {
                    if (data.errors.namespace) {
                        var namespace_error = data.errors.namespace[0];
                    }
                    if (data.errors.name) {
                        var name_error = data.errors.name[0];
                    }
                }
                this.setState({namespace_error: namespace_error,
                               name_error: name_error});
            }.bind(this));
    },
    draw_table: function() {
        var xslt_editing_fields = [
                <tr><td className="new-package__xslt-label">XSLT mighty feature!</td></tr>,
                <tr>
                  <td className="new-package__xslt-wrap"><textarea placeholder="Behold XSLT\'s mighty power!" className="new-package__xslt-input" name="xslt" onChange={this.on_field_change} disabled={this.state.waiting}></textarea></td>
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
        if (!this.is_apply_button_disabled()) {
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
                  <input name="namespace" type="text" placeholder="Namespace (e.g. python, node)" onChange={this.on_field_change} className="text-input" value={this.props.namespace}/>
                </div>
              </td>
           </tr>
           <tr>
              <td className="namespace-name-cell__name-cell">
                <div className="input">
                  <label className="input__label">Name:</label>{name_error}<br/>
                  <input name="name" type="text" placeholder="Package name" onChange={this.on_field_change} className="text-input"/>
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
             <input name="description" type="text" placeholder="Tell us what it does" onChange={this.on_field_change} className="text-input"/>
           </div>
         </td>
       </tr>
       <tr>
         <td className="new-package__search-label">Search in these dirs and files:</td>
       </tr>
       <tr>
         <td className="new-package__search-input-wrap"><textarea placeholder="Enter here a directories where parser should search for changelogs. By default parser searches through all sources and sometimes it consider a changelog file which are not changelogs. Using this field you could narrow the search." className="new-package__search-input" name="search_list" onChange={this.on_field_change} disabled={this.state.waiting}></textarea></td>
       </tr>
       <tr>
         <td className="new-package__ignore-label">Ignore these dirs and files:</td>
       </tr>
       <tr>
         <td className="new-package__ignore-input-wrap"><textarea placeholder="Here you could enter a list of directories to ignore during the changelog search. This is another way how to prevent robot from taking changelog-like data from wierd places." className="new-package__ignore-input" name="ignore_list" onChange={this.on_field_change} disabled={this.state.waiting}></textarea></td>
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
        // waiting for preview results @wait-for-preview
        if (this.spinner === undefined) {
            // creating a spinner @wait-for-preview
            this.spinner = new Spinner({left: '50%', top: '30px'}).spin($('.results-spin__wrapper')[0]);
        }

        // checking if preview is ready @wait-for-preview
        $.get('/preview/' + this.props.preview_id + '/')
            .success(function(data_orig) {
                // received results about preview state @wait-for-preview
                var data = $(data_orig);

                if (data.hasClass('please-wait')) {
                    // data has class please-wait @wait-for-preview
                    $('.progress-text').html(data);
                    setTimeout(this.wait_for_preview, 1000);
                } else {
                    // preview data is ready @wait-for-preview
                    this.setState({waiting: false});

                    if (data.hasClass('package-changes')) {
                        // showing preview @wait-for-preview
                        this.setState({results: data_orig});
                    } else {
                        // showing a problem @wait-for-preview
                        this.setState({problem: data_orig});
                    }
                }
        }.bind(this))
        .error(function(data) {
            // some shit happened @wait-for-preview
         });
    },
    update_preview_callback: function () {
        // resetting state before waiting for preview results @update-preview-callback
        this.setState({waiting: true,
                       results: null,
                       problem: false})
        // $scope.orig_search_list = $scope.search_list;
        // $scope.orig_ignore_list = $scope.ignore_list;
        // $scope.orig_xslt = $scope.xslt;
        // $scope.orig_changelog_source = $scope.changelog_source;

        this.wait_for_preview();
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
                              <div className="changelog-preview" dangerouslySetInnerHTML={{__html: this.state.results}}></div>
                            </div>);
           }

           if (this.state.problem) {
               content.push(<div className="changelog-problem" dangerouslySetInnerHTML={{__html: this.state.problem}}></div>);
           }
        }
        return (<div className="package-settings">{content}</div>);
    }
});
