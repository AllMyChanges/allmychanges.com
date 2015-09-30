// новое TODO:

// На чем закончил:
// Когда переключаюсь на http downloader, он таймаутится и происходит ошибка
// при этом в процессе скачивания, downloader ничего не пишет в лог,
// когда случается ошибка, надо скрывать таб Save
// но и список даунлоадеров почему-то сбрасывается и остается один только http
// сброс происходит при установке обишки, видимо

// В целом
// [ ] невозможно сменить URL существующего пакета
// [ ] нельзя запустить dbshell: CommandError: You appear not to have the 'mysql' program installed or on your path.
// [ ] кажется, при сохранении превью, не сохраняется выбранный downloader, надо проверить
// [ ] никак не обрабатываются ошибки, происходящие во время ожидания результатов preview.
//     например, если прервать worker.
// [ ] неудобно - теперь из emacs невозможно почитать или иизменить исходники библиотек, потому что они
//     внутри env в докере

// На табе описания:
// [+] после нажатия Save нужно редиректить на страницу пакета
// [+] когда меняется namespace или name, надо мгновенно дисейблить кнопку save до окончания валидации
// [ ] сохранение по Ctrl-Enter и Cmd+Enter.

// на странице changedownloader:
// [+] надо показывать только список тех даунлоадеров, что выдал guess
//     для существующего пакета guess не запускается и превью показывается
//     сразу, потому что данные копируются из ченьджлога
//     - поэтому надо для ченьджлога и превью сделать отдельное поле downloaders
//       со списком guessed downloaders
//     - и копировать его содержимое в Preview
//     - а затем использовать для показа списка доступных
// [+] и в выпадушке должен быть выбран текущий downloader
// [+] надо добавить кнопку Apply
// -> [+] сделать так, чтобы http downloader хоть писал в лог, что скачивает такую-то страницу
// [+] сделать так, чтобы не сбрасывался список downloaders
// [+] если в случае когда changelog не найден скрывался таб Save
// [ ] если changelog не найден, не показывать текст This is the latest versions
// [ ] если changelog не найден, показывать полный лог, а не только problem
//
// Хорошо бы так же сделать:
// [ ] Анимацию, чтобы панель настроек выезжала снизу

// старое тодо, оставленное для размышлений:
// [ ] разобраться, почему ошибка для google play не показывается, а для hg или git показывается
// [ ] выяснить почему для Google play не показывается статус процесса обработки
// [ ] проверить, как работает search in
// [ ] добавить exclude
// [ ] добавить XSLT
// [ ] сделать отображение сообщений, чтобы они
//     приезжали в ответе на save

var React = require('react');
var ReactTabs = require('react-tabs');
var Tab = ReactTabs.Tab;
var Tabs = ReactTabs.Tabs;
var TabList = ReactTabs.TabList;
var TabPanel = ReactTabs.TabPanel;


module.exports = React.createClass({
    // this field keeps state for which preview was generated
    preview: {},
    validate_namespace_name_timeout: null,

    getInitialState: function () {
        // init add new page @add-new
        // downloader [this.props.downloader] @add-new
        return {tracked: false,
                saving: false,
                validating: false, // выставляется, когда мы ждем проверки namespace и name
                waiting: false,
                source: this.props.source,
                search_list: this.props.search_list || '',
                ignore_list: this.props.ignore_list || '',
                xslt: this.props.xslt || '',
                results: null,
                save_button_title: ((this.props.mode == 'edit') ? 'Save' : 'Save&Track'),
                downloader: this.props.downloader,
                namespace: this.props.namespace || '',
                namespace_error: !this.props.namespace && 'Please, fill this field' || '',
                name: this.props.name || '',
                description: this.props.description || '',
                name_error: !this.props.namespace && 'Please, fill this field' || '',
                status: null, // here we store preview's status as it returned by API
                problem: null,
                log: []};
    },
    componentDidMount: function() {
        this.save_preview_params();
        this.update_preview_callback();
    },
    save_preview_params: function () {
        this.preview = {
            source: this.state.source,
            downloader: this.state.downloader,
            search_list: this.state.search_list,
            ignore_list: this.state.ignore_list,
            xslt: this.state.xslt};
    },
    can_save: function() {
        var result = (this.state.saving == false
                      && this.state.validating == false
                      && this.is_apply_button_disabled()
                      && this.state.namespace_error == '' 
                      && this.state.name_error == '' 
                      && this.state.results);
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
    apply_downloader_settings: function() {
        // applying downloader-sttings @apply-downloader-settings
        this.save_preview_params();

        $.ajax({url: '/v1/previews/' + this.props.preview_id + '/',
                method: 'PATCH',
                data: JSON.stringify({
                    downloader: this.state.downloader
                }),
                contentType: 'application/json',
                headers: {'X-CSRFToken': $.cookie('csrftoken')}})
            .success(this.update_preview_callback);
    },
    on_field_change: function(event, on_state_change) {
        // on_state_change could be a function to be called
        // when field changes will be applied to the state

        var name = event.target.name;
        // field [name] was changed @on-field-change
        var params = {}
        params[name] = event.target.value;

        var callback = function () {
            if (name == 'namespace' || name == 'name') {
                this.schedule_validation();
            }
            if (on_state_change !== undefined) {
                on_state_change();
            }
        }.bind(this);

        this.setState(params, callback);
    },
    save: function() {
        // Saving @package-settings
        this.setState({saving: true,
                       save_button_title: 'Saving...'});
        var data = {
            'namespace': this.state.namespace,
            'description': this.state.description,
            'name': this.state.name,
            'source': this.state.source,
            'search_list': this.state.search_list,
            'ignore_list': this.state.ignore_list,
            'xslt': this.state.xslt}
        return $.ajax({
            url: '/v1/changelogs/' + this.props.changelog_id + '/',
            method: 'PUT',
            data: JSON.stringify(data),
            contentType: 'application/json',
            headers: {'X-CSRFToken': $.cookie('csrftoken')}})
            .success(
                function() {
                    this.setState({
                        saving: false,
                        save_button_title: 'Save'});
//                      check_and_show_messages();
                }.bind(this));
    },
    save_and_redirect: function() {
        this.save().success(this.redirect);
    },
    save_and_track: function() {
        // Saving and tracking @package-settings
        this.save().success(function() {
            $.ajax({
                url: '/v1/changelogs/' + this.props.changelog_id + '/track/',
                method: 'POST',
                headers: {'X-CSRFToken': $.cookie('csrftoken')}})
                .success(this.redirect);
        });
    },
    redirect: function(data) {
        // Redirecting to package's page @package-settings
        window.location = data['absolute_uri'];
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
        this.setState({validating: true});
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
                               name_error: name_error,
                               validating: false});
            }.bind(this));
    },
    // draw_table: function() {
    //     var xslt_editing_fields = [
    //             <tr><td className="new-package__xslt-label">XSLT mighty feature!</td></tr>,
    //             <tr>
    //               <td className="new-package__xslt-wrap">
    //                 <textarea placeholder="Behold XSLT's mighty power!"
    //                           className="new-package__xslt-input" name="xslt"
    //                           onChange={this.on_field_change}
    //                           disabled={this.state.waiting} value={this.state.xslt}></textarea></td>
    //             </tr>];
    //     if (username != 'svetlyak40wt') {
    //         xslt_editing_fields = [];
    //     }

    //     var save_callback;
    //     var submit_button_disabled = !this.can_track();

    //     if (this.props.mode == 'edit') {
    //         save_callback = this.save;
    //     } else {
    //         save_callback = this.save_and_track;
    //     }
    //     var save_button = <input type="submit" className="button _good _large magic-prompt__apply" value={this.state.save_button_title} onClick={this.save} disabled={submit_button_disabled}/>;

    //     var save_tooltip;
    //     if (!this.is_apply_button_disabled()) {
    //         save_tooltip = <span className="new-package__save-tooltip">Please, update preview to ensure that we able to get a changelog for this package.</span>;
    //     }

    //     var broken_links_warning;
    //     if (this.is_name_or_namespace_were_changed()) {
    //             broken_links_warning = (
    //                     <tr>
    //                       <td className="new-package__rename-warning" colspan="2">
    //                         Beware, renaming this package will broke all links to this package!
    //                       </td>
    //                     </tr>);
    //     }
    //     var namespace_error;
    //     if (this.state.namespace_error) {
    //         namespace_error = <span className="input__error">{this.state.namespace_error}</span>;
    //     }
    //     var name_error;
    //     if(this.state.name_error) {
    //         name_error = <span className="input__error">{this.state.name_error}</span>;
    //     }
    //     var description_error;
    //     if (this.state.description_error) {
    //         description_error = <span className="input__error">{this.state.description_error}</span>;
    //     }

    //     var content = (<table className="new-package__fields-table">
    //    <tr>
    //     <td className="new-package__namespace-name-cell">
    //       <table className="namespace-name-cell__table">
    //         <tr>
    //           <td className="namespace-name-cell__namespace-cell">
    //             <div className="input">
    //               {namespace_error}<br/>
    //               <input name="namespace" type="text"
    //                      placeholder="Namespace (e.g. python, node)"
    //                      onChange={this.on_field_change}
    //                      className="text-input" value={this.state.namespace}/>
    //             </div>
    //           </td>
    //        </tr>
    //        <tr>
    //           <td className="namespace-name-cell__name-cell">
    //             <div className="input">
    //               {name_error}<br/>
    //               <input name="name" type="text"
    //                      placeholder="Package name"
    //                      onChange={this.on_field_change}
    //                      className="text-input" value={this.state.name}/>
    //             </div>
    //           </td>
    //         </tr>
    //         {broken_links_warning}
    //       </table>
    //     </td>
    //     <td className="new-package__button-cell">
    //     </td>
    //    </tr>
    //    <tr>
    //      <td className="new-package__description-cell">
    //        <div className="input">
    //          {description_error}<br/>
    //          <input name="description" type="text"
    //                 placeholder="Tell us what it does"
    //                 onChange={this.on_field_change}
    //                 className="text-input" value={this.state.description}/>
    //        </div>
    //      </td>
    //    </tr>
    //    <tr>
    //      <td className="new-package__search-label">Search in these dirs and files:</td>
    //    </tr>
    //    <tr>
    //      <td className="new-package__search-input-wrap">
    //          <textarea placeholder="Enter here a directories where parser should search for changelogs. By default parser searches through all sources and sometimes it consider a changelog file which are not changelogs. Using this field you could narrow the search."
    //                    className="new-package__search-input" name="search_list"
    //                    onChange={this.on_field_change}
    //                    disabled={this.state.waiting} value={this.state.search_list}></textarea></td>
    //    </tr>
    //    <tr>
    //      <td className="new-package__ignore-label">Ignore these dirs and files:</td>
    //    </tr>
    //    <tr>
    //      <td className="new-package__ignore-input-wrap">
    //          <textarea placeholder="Here you could enter a list of directories to ignore during the changelog search. This is another way how to prevent robot from taking changelog-like data from wierd places."
    //                    className="new-package__ignore-input" name="ignore_list"
    //                    onChange={this.on_field_change}
    //                    disabled={this.state.waiting} value={this.state.ignore_list}></textarea></td>
    //    </tr>
    //    {xslt_editing_fields}
    //    <tr>
    //     <td className="new-package__button-cell">
    //       <input type="submit" className="button _large magic-prompt__apply" value="Update Preview" onClick={this.update_preview} disabled={this.is_apply_button_disabled()}/>
    //       {save_button}
    //       {save_tooltip}
    //     </td>
    //    </tr>
    //  </table>);

    //  return content;
    // },
    fetch_rendered_preview: function() {
        var promice = $.get('/preview/' + this.props.preview_id + '/')
        promice.success(function(data) {
            this.setState({waiting: false,
                           results: data});
        }.bind(this));
        promice.error(function(response) {
            // TODO: тут надо в случае продакшена выводить более простое сообщение
            // вместо того, что ответил сервер. Ибо зачем пользователям видеть трейсбэк?
            var problem = '<pre>' + response.responseText + '</pre>';
            
            this.setState({waiting: false,
                           results: null,
                           problem: problem});
        }.bind(this));
        
    },
    wait_for_preview: function () {
        // waiting for preview results @wait-for-preview
        if (this.spinner === undefined) {
            // creating a spinner @wait-for-preview
            this.spinner = new Spinner({left: '50%', top: '30px'}).spin($('.results-spin__wrapper')[0]);
        }

        // checking if preview is ready @wait-for-preview
        $.get('/v1/previews/' + this.props.preview_id + '/')
            .success(function(data) {
                // received results about preview state @wait-for-preview
                this.setState({'log': data.log,
                               'status': data.status,
                               'downloaders': data.downloaders,
                               'downloader': data.downloader});

                if (data.status == 'processing') {
                    // preview is still in processing status @wait-for-preview
                    setTimeout(this.wait_for_preview, 1000);
                } else {
                    // preview data is ready @wait-for-preview
                    this.fetch_rendered_preview();

                    // if (data.hasClass('package-changes')) {
                    //     // showing preview @wait-for-preview
                    //     this.setState({results: data_orig});
                    // } else {
                    //     // showing a problem @wait-for-preview
                    //     this.setState({problem: data_orig});
                    // }
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
        var next_actions = [];
//        if (this.props.mode == 'edit') {
        content.push(<input name="changelog_source"
                     type="text"
                     placeholder="Changelog&#39;s source URL"
                     className="text-input"
                     value={this.state.source}/>);
        // } else {
        //     if (this.state.tracked) {
        //       content.push(<p className="plate">Horay! The package was added and is available <a href="/p/{this.props.namespace}}/{{this.props.name}}/">on a separate page</a>.</p>);
        //     } else {

            
        //    if (username == "" && this.state.tracked) {
        //        content.push(<p className="plate plate_warning">To continue tracking of this package, please, login through <a href="{login_url_github}">GitHub</a> or <a href="{login_url_twitter}">Twitter</a>.</p>);
        //    }
        // }

        // if (!this.state.tracked) {
        //     content = content.concat(this.draw_table());
        // }


        // показываем поля для заполнения namespace и name
        var namespace_error;
        if (this.state.namespace_error) {
            namespace_error = <span className="input__error">{this.state.namespace_error}</span>;
        }
        var name_error;
        if(this.state.name_error) {
            name_error = <span className="input__error">{this.state.name_error}</span>;
        }
        var description_error;
        if (this.state.description.length > 255) {
            description_error = <span className="input__error">Description should be no more than 255 symbols.</span>;
        }

        var tabs = [];
        var tab_panels = [];

        var add_tab = function (text, content) {
            tabs.push(<Tab>{{ text }}</Tab>);
            tab_panels.push(<TabPanel>{{ content }}</TabPanel>);
        }

        var save_button_disabled = !this.can_save();
        var save_button = <input type="submit" className="button _good _large magic-prompt__apply" value={this.state.save_button_title} onClick={this.save_and_redirect} disabled={save_button_disabled}/>;

        var save_panel = (<div>
                     <div className="input">
                     {namespace_error}<br/>
                     <input name="namespace"
                     type="text"
                     placeholder="Namespace (e.g. python, node)"
                     onChange={this.on_field_change}
                     className="text-input"
                     value={this.state.namespace}/>
                     </div>

                     <div className="input">
                     {name_error}<br/>
                     <input name="name"
                     type="text"
                     placeholder="Package name"
                     onChange={this.on_field_change}
                     className="text-input"
                     value={this.state.name}/>
                     </div>
                     <div className="input">
                     {description_error}<br/>
                     <input name="description"
                     type="text"
                     placeholder="Describe what it does."
                     onChange={this.on_field_change}
                     className="text-input"
                     value={this.state.description}/>
                          </div>

                          <p className="buttons-row">{save_button}</p>


                     </div>);

        if (this.state.status == 'success') {
            add_tab('Save', save_panel);
        }
        
        // спрашиваем, всё ли с логом в порядке и предлагаем затрекать
        if (this.state.waiting) {
            // показываем предложение подождать пока обработка закончится
            content.push(<div>
                             <div className="progress-text">Please, wait while we search a changelog.</div>
                             <div className="results-spin"><div className="results-spin__wrapper"></div></div>
                         </div>);
            
            // показываем лог
            var log_items = [];
            for (i=0; i< this.state.log.length; i++) {
                log_items.push(<li key={i}>{this.state.log[i]}</li>);
            }
            content.push(<ul class="preview-processing-log">{log_items}</ul>);

        } else {
            if (this.state.status == 'success') {
                // сами результаты
                content.push(<div className="changelog-preview-container">
                                 <h1>This is the latest versions for this package</h1>
                                 <div className="changelog-preview" dangerouslySetInnerHTML={{__html: this.state.results}}></div>
                             </div>);

            }
            var available_downloaders = {'feed': 'Rss/Atom Feed',
                                         'http': 'Single HTML Page',
                                         'rechttp': 'Multiple HTML Pages',
                                         'google_play': 'Google Play',
                                         'itunes': 'Apple AppStore',
                                         'git': 'Git Repository',
                                         'hg': 'Mercurial Repository',
                                         'github_releases': 'GitHub Releases'};
            var render_option = function (item) {
                var name = item.name;
                if (name == this.state.downloader) {
                    return <option value={name} key={name} selected>{available_downloaders[name]}</option>;
                } else {
                    return <option value={name} key={name}>{available_downloaders[name]}</option>;
                }
            }.bind(this);
            
            var options = R.map(render_option, this.state.downloaders);
            
            var change_downloader_panel = (
<div>
  <p>Please, select which downloader to use:</p>
  <select className="downloader-selector"
          name="downloader"
          value={this.state.downloader}
          onChange={this.on_field_change}
          disabled={this.state.waiting}>
    {options}
  </select>
  <input type="submit" className="button _good _large magic-prompt__apply" value="Apply" onClick={this.apply_downloader_settings}/>;
                    </div>);
            add_tab('Change downloader', change_downloader_panel);

            var tune_parser_panel = (
<div>
  <textarea placeholder="Enter here a directories where parser should search for changelogs. By default parser searches through all sources and sometimes it consider a changelog file which are not changelogs. Using this field you could narrow the search."
            className="new-package__search-input"
            name="search_list"
            onChange={this.on_field_change}
            disabled={this.state.waiting}
            value={this.state.search_list}></textarea>
                        </div>);
            add_tab('Tune parser', tune_parser_panel);
        }

        if (this.state.problem) {
            content.push(<div key="problem" className="changelog-problem" dangerouslySetInnerHTML={{__html: this.state.problem}}></div>);
        }
        
        if (this.state.status != 'processing') {
            // results are [this.state.results] @debug
            content.push(<div className="changelog-settings__tune">
                     <Tabs>
                       <TabList>{{ tabs }}</TabList>
                       {{ tab_panels }}
                     </Tabs>
                     </div>);
        }
                  
        
        return (<div className="package-settings">{content}</div>);
    }
});
