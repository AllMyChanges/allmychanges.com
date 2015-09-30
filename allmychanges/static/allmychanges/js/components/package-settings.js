// новое TODO:

// На чем закончил:
// Вынес куски рендеринга в отдельные функции
// теперь надо поправить логику
// она должна быть такая:
// если status == processing, то показывае лог и всё
// если status != processing, то
//   если status == success, то
//     показываем результаты обработки ченьджлога
//     показываем таб Save
//   если status == error
//     показываем лог
//   показываем панель с табами

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


var render_tabs = function(tabs, tab_panels) {
    return (
        <div className="changelog-settings__tune">
        <Tabs>
        <TabList>{{ tabs }}</TabList>
        {{ tab_panels }}
        </Tabs>
        </div>
   );
}

var render_problem = function(problem) {
    return <div key="problem" className="changelog-problem" dangerouslySetInnerHTML={{__html: problem}}></div>
}

var render_we_are_waiting = function() {
    // показываем предложение подождать пока обработка закончится
    return (
        <div>
            <div className="progress-text">Please, wait while we search a changelog.</div>
            <div className="results-spin"><div className="results-spin__wrapper"></div></div>
        </div>);
}

var render_log = function(log) {
    // показываем лог
    var log_items = [];
    for (i=0; i< log.length; i++) {
        log_items.push(<li key={i}>{log[i]}</li>);
    }
    return (<ul className="preview-processing-log">{log_items}</ul>);
}

var render_results = function (results) {
    // сами результаты
    return(<div className="changelog-preview-container">
        <h1>This is the latest versions for this package</h1>
        <div className="changelog-preview" dangerouslySetInnerHTML={{__html: results}}></div>
        </div>);
}

var render_save_panel = function (opts) {
    // показываем поля для заполнения namespace и name
    var namespace_error;
    if (opts.namespace_error) {
        namespace_error = <span className="input__error">{opts.namespace_error}</span>;
    }
    var name_error;
    if(opts.name_error) {
        name_error = <span className="input__error">{opts.name_error}</span>;
    }
    var description_error;
    if (opts.description.length > 255) {
        description_error = <span className="input__error">Description should be no more than 255 symbols.</span>;
    }

    var save_button = <input type="submit" className="button _good _large magic-prompt__apply" value={opts.button_title} onClick={opts.on_submit} disabled={opts.disabled}/>;

    var save_panel = (<div>
        <div className="input">
        {namespace_error}<br/>
        <input name="namespace"
        type="text"
        placeholder="Namespace (e.g. python, node)"
        onChange={opts.on_field_change}
        className="text-input"
        value={opts.namespace}/>
        </div>

        <div className="input">
        {name_error}<br/>
        <input name="name"
        type="text"
        placeholder="Package name"
        onChange={opts.on_field_change}
        className="text-input"
        value={opts.name}/>
        </div>
        
        <div className="input">
        {description_error}<br/>
        <input name="description"
        type="text"
        placeholder="Describe what it does."
        onChange={opts.on_field_change}
        className="text-input"
        value={opts.description}/>
        </div>

        <p className="buttons-row">{save_button}</p>
        </div>);
    return save_panel;
}

var render_change_downloader_panel = function (opts) {
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
        if (name == opts.downloader) {
            return <option value={name} key={name} selected>{available_downloaders[name]}</option>;
        } else {
            return <option value={name} key={name}>{available_downloaders[name]}</option>;
        }
    };
    
    var options = R.map(render_option, opts.downloaders);
    
    var change_downloader_panel = (
        <div>
        <p>Please, select which downloader to use:</p>
        <select className="downloader-selector"
        name="downloader"
        value={opts.downloader}
        onChange={opts.on_field_change}
        disabled={opts.disabled}>
        {options}
        </select>
        <input type="submit" className="button _good _large magic-prompt__apply" value="Apply" onClick={opts.on_submit}/>;
        </div>);

    return change_downloader_panel;
}

var render_tune_parser_panel = function(opts) {
    return (
        <div>
        <textarea placeholder="Enter here a directories where parser should search for changelogs. By default parser searches through all sources and sometimes it consider a changelog file which are not changelogs. Using this field you could narrow the search."
            className="new-package__search-input"
        name="search_list"
        onChange={opts.on_field_change}
        disabled={opts.disabled}
        value={opts.value}></textarea>
        </div>);
}


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
                downloaders: [],
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


        var tabs = [];
        var tab_panels = [];

        var add_tab = function (text, content) {
            tabs.push(<Tab>{ text }</Tab>);
            tab_panels.push(<TabPanel>{ content }</TabPanel>);
        }

        if (this.state.status == 'success') {
            add_tab('Save', render_save_panel({
                disabled: !this.can_save(),
                button_title: this.state.save_button_title,
                on_submit: this.save_and_redirect,
                namespace_error: this.state.namespace_error,
                name_error: this.state.name_error,
                description: this.state.description,
                on_field_change: this.on_field_change,
                namespace: this.state.namespace,
                name: this.state.name,
            }));
        }
        
        // спрашиваем, всё ли с логом в порядке и предлагаем затрекать
        if (this.state.waiting) {
            content.push(render_we_are_waiting());
            content.push(render_log(this.state.log));
        } else {
            if (this.state.status == 'success') {
                content.push(render_results(this.state.results));
            }
            add_tab('Change downloader',
                    render_change_downloader_panel({
                        downloader: this.state.downloader,
                        downloaders: this.state.downloaders,
                        on_field_change: this.on_field_change,
                        on_submit: this.apply_downloader_settings,
                        disabled: this.state.waiting
                    }));

            add_tab('Tune parser',
                    render_tune_parser_panel({
                        on_field_change: this.on_field_change,
                        disabled: this.state.waiting,
                        value: this.state.search_list
                    }));
        }

        if (this.state.problem) {
            content.push(render_problem(this.state.problem));
        }
        
        if (this.state.status != 'processing') {
            content.push(render_tabs(tabs, tab_panels));
        }
                  
        
        return (<div className="package-settings">{content}</div>);
    }
});
