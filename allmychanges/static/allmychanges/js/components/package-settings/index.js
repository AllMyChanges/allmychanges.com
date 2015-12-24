var Accordion = require('../accordion');
var ReactMDL = require('react-mdl');
var Spinner2 = ReactMDL.Spinner;
var R = require('ramda');
var css = require('./index.styl');


var React = require('react');
var ReactTabs = require('react-tabs');
var Tab = ReactTabs.Tab;
var Tabs = ReactTabs.Tabs;
var TabList = ReactTabs.TabList;
var TabPanel = ReactTabs.TabPanel;
var render_change_downloader_tab = require('./tune-downloader');
var TunePanel = require('./tune-panel');


var render_tabs = function(tabs, tab_panels) {
    return (
        <Tabs>
            <TabList>{ tabs }</TabList>
            { tab_panels }
        </Tabs>
   );
}

var render_change_source_plate = function (on_submit) {
    return (
        <div>
            <p>You changed the source URL, please, hit "Apply" button to search changelog data at the new source.</p>
            <p className="buttons-row">
              <input type="submit" className="button _good" value="Apply" onClick={on_submit}/>
            </p>
        </div>
    )
}

var render_no_downloaders_plate = function () {
    return (
        <div>
            <p>No downloaders are able to process this source url, please change it to something else and try again.</p>
        </div>
    )
}

var render_we_are_waiting = function() {
    return (
        <div key="waiting">
            <div className="progress-text">Please, wait while we search a changelog.</div>
        </div>);
}

var render_log = function(log, show_spinner) {
    // показываем лог @package_settings.render_log
    var log_items = [];
    
    for (var i=0; i < log.length; i++) {
        log_items.push(<li key={i}>{log[i]}</li>);
    }
    if (show_spinner) {
        log_items.push(<li key="spinner" className="preview-processing-log__spinner"><Spinner2/></li>);
    }
    
    return (<ul key="log" className="preview-processing-log">{log_items}</ul>);
}

var render_results = function (results) {
    // тут есть баг с тем, что заданный max-height не ресетится после того,
    // как окно растягивается, и плашка начинает "плавать"
    // при этом footer "подягивается" вверх и начинает наезжать на
    // превью
    // пока я решил забить, потому что вряд ли кто-то будет ресайзить окно
    // во время добавления нового ченьджлога
    
    var show_more = function (a1, a2, a3, a4) {
        var sel = $('.preview-container__content');
        var new_height = parseInt(sel.css('max-height')) + 500;
        sel.css('max-height', new_height);
    }
    // сами результаты
    return(
            <div key="results" className="preview-container">
              <h1>This is the latest versions for this package</h1>
              <div className="preview-container__content" dangerouslySetInnerHTML={{__html: results}}></div>
              <div className="preview-container__show-more">
                <input type="button" className="button _good" onClick={show_more} value="show more"/>
              </div>
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

    var save_button = <input type="submit" className="button _good _large" value={opts.button_title} onClick={opts.on_submit} disabled={opts.disabled}/>;

    var save_panel = (
          <div key="save-panel">
            <div className="changelog-settings__tune-panel">
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
            </div>
          </div>);
    return save_panel;
}


var render_tune_parser_panel = function(opts) {

    var elements = [
        {
            title: 'Search in dirs or files',
            content: (
        <textarea placeholder="Enter here a directories where parser should search for changelogs. By default parser searches through all sources and sometimes it consider a changelog file which are not changelogs. Using this field you could narrow the search."
            className="new-package__search-input"
        name="search_list"
        onChange={opts.on_field_change}
        value={opts.search_list}></textarea>
            )
        },
        {
            title: 'Exclude some dirs or files',
            content: (
        <textarea placeholder="Here you could enter a list of directories to ignore during the changelog search. This is another way how to prevent robot from taking changelog-like data from wierd places."
            className="new-package__ignore-input"
        name="ignore_list"
        onChange={opts.on_field_change}
        value={opts.ignore_list}></textarea>
)
        },
        {
            title: 'XSL Transformation',
            content:
            (
                    <textarea placeholder="Behold XSLT's mighty power!"
                className="new-package__xslt-input"
                onChange={opts.on_field_change}
                name="xslt"
                value={opts.xslt}></textarea>
            )
        }
    ];

    var button_style = {transition: 'all 0.2s ease-in', opacity: 0};
    var button_disabled = true;
    
    if (opts.need_apply) {
        button_style.opacity = 1;
        button_disabled = false;
    } else {
        button_style.cursor = 'default';
    }
        
    return (
        <div key="tune-parser-panel">
          <div className="changelog-settings__tune-panel">
            <Accordion elements={elements}/>
            <p className="buttons-row">
            <input type="submit"
                   className="button _good _large"
                   value="Apply"
                   onClick={opts.on_submit}
                   style={button_style}
                   disabled={button_disabled}/>
            </p>
          </div>
        </div>
    );
}


module.exports = React.createClass({
    // this field keeps state for which preview was generated
    preview: {},
    validate_namespace_name_timeout: null,

    getInitialState: function () {
        // [this.props.downloader] @package_settings.getInitialState
        var downloader = R.or(
            this.props.downloader,
            R.path('name',
                   R.head(this.props.downloaders || [])));

        // downloader is [downloader] @package_settings.getInitialState
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
                downloader: downloader,
                downloader_settings: this.props.downloader_settings,
                downloaders: [],
                namespace: this.props.namespace || '',
                namespace_error: !this.props.namespace && 'Please, fill this field' || '',
                name: this.props.name || '',
                description: this.props.description || '',
                name_error: !this.props.namespace && 'Please, fill this field' || '',
                status: null, // here we store preview's status as it returned by API
                problem: null,
                tune_panel_height: 0,
                log: []};
    },
    componentDidMount: function() {
        this.save_preview_params();
        this.update_preview_callback();
    },
    save_preview_params: function () {
        // downloader [this.state.downloader] @package_settings.save_preview_params
        this.preview = {
            source: this.state.source,
            downloader: this.state.downloader,
            downloader_settings: R.clone(this.state.downloader_settings),
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
        // updating preview @package_settings.update_preview

        // this field keeps state for which preview was generated
        this.save_preview_params();

        $.ajax({url: '/preview/' + this.props.preview_id + '/',
                method: 'POST',
                data: JSON.stringify(this.preview),
                contentType: 'application/json',
                headers: {'X-CSRFToken': $.cookie('csrftoken')}})
            .success(this.update_preview_callback);
    },
    apply_settings: function() {
        // applying parser settings @package_settings.apply_settings
        this.save_preview_params();

        $.ajax({url: '/v1/previews/' + this.props.preview_id + '/',
                method: 'PATCH',
                data: JSON.stringify(
                    R.pick(['downloader',
                            'downloader_settings',
                            'search_list',
                            'ignore_list',
                            'xslt',
                            'source'],
                           this.state)
                ),
                contentType: 'application/json',
                headers: {'X-CSRFToken': $.cookie('csrftoken')}})
            .success(this.update_preview_callback);
    },
    on_field_change: function(event, on_state_change) {
        // on_state_change could be a function to be called
        // when field changes will be applied to the state

        var name = event.target.name;
        var new_value = event.target.value;

        // field [name] was changed to [new_value] @package_settings.on_field_change
        var params = {}
        params[name] = new_value;

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
        // Saving @package_settings.save
        this.setState({saving: true,
                       save_button_title: 'Saving...'});
        var data = {
            'namespace': this.state.namespace,
            'description': this.state.description,
            'downloader': this.state.downloader,
            'downloader_settings': this.state.downloader_settings,
            'downloaders': this.state.downloaders,
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
        // Saving and tracking @package_settings.save_and_track
        this.save().success(function() {
            $.ajax({
                url: '/v1/changelogs/' + this.props.changelog_id + '/track/',
                method: 'POST',
                headers: {'X-CSRFToken': $.cookie('csrftoken')}})
                .success(this.redirect);
        });
    },
    redirect: function(data) {
        // Redirecting to package's page @package_settings.redirect
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
        // scheduling namespace or name validation @package_settings.schedule_validation
        window.clearTimeout(this.validate_namespace_name_timeout);
        this.setState({validating: true});
        this.validate_namespace_name_timeout = window.setTimeout(this.validate_namespace_and_name, 500);
    },
    validate_namespace_and_name: function () {
        // validating namespace and name @package_settings.validate_namespace_and_name
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
            // нужно сохранить настройки preview
            // с которыми были получены результаты,
            // чтобы правильно показывать или не показывать
            // кнопки Apply
            this.save_preview_params();
            
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
    update_downloader: function (downloader) {
        // Updating downloader @package_settings.update_downloader
        var current_downloader = R.find(
            R.propEq('name', downloader),
            this.state.downloaders);
        
        var params = {'downloader': downloader};
        
        if (downloader) {
            params = R.merge(
                params,
                {
                    'namespace': this.state.namespace || current_downloader.changelog.namespace || '',
                    'name': this.state.name || current_downloader.changelog.name || '',
                    'description': this.state.description || current_downloader.changelog.description || ''
                }
            );
            this.schedule_validation();
        }
        this.setState(params);
    },
    wait_for_preview: function () {
        // waiting for preview results @package_settings.wait_for_preview
        $.get('/v1/previews/' + this.props.preview_id + '/')
            .success((data) => {
                // received [data] about preview state @package_settings.wait_for_preview
                this.setState({'log': data.log,
                               'status': data.status,
                               'downloaders': data.downloaders,
                               'downloader': data.downloader},
                              () => {
                                  this.update_downloader(data.downloader);
                              });

                if (data.status == 'processing') {
                    // preview is still in processing status @package_settings.wait_for_preview
                    setTimeout(this.wait_for_preview, 1000);
                } else {
                    // preview data is ready @package_settings.wait_for_preview
                    this.fetch_rendered_preview();
                }
            })
            .error(function(data) {
                // some shit happened @package_settings.wait_for_preview
            });
    },
    update_preview_callback: function () {
        // resetting state before waiting for preview results @package_settings.update_preview_callback
        this.setState({waiting: true,
                       results: null,
                       problem: false})
        this.wait_for_preview();
    },
    render: function() {

        var content = [];
        var next_actions = [];

        content.push(<input name="source"
                     key="source"
                     type="text"
                     placeholder="Changelog&#39;s source URL"
                     className="text-input"
                     value={this.state.source}
                     onChange={this.on_field_change}/>);

        var tabs = [];
        var tab_panels = [];

        var add_tab = function (text, content) {
            tabs.push(<Tab>{ text }</Tab>);
            tab_panels.push(<TabPanel key={ text }>{ content }</TabPanel>);
        }

        var status = this.state.status;

        if (status == 'processing') {
            content.push(render_we_are_waiting());
            content.push(render_log(this.state.log, true));
        } else {
            // статус равен created, когда мы открыли changelog
            // для редактирования и версии preview взяты из него
            
            if (status == 'error') {
                content.push(render_log(this.state.log, false));
            }
            if (status == 'success' || status == 'created') {
                content.push(render_results(this.state.results));

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
            
            if (status != 'processing') {
                var is_downloader_options_should_be_applied = () => {
                    var result = (
                        this.state.downloader != this.preview.downloader ||
                            !R.equals(this.state.downloader_settings, this.preview.downloader_settings));

                    if (result) {
                        // Downloader options SHOULD be applied @package_settings.render
                    } else {
                        // Downloader options SHOULD NOT be applied @package_settings.render
                    }
                    return result;
                }
                
                var is_parser_options_should_be_applied = () => {
                    var result = (
                        this.state.search_list != this.preview.search_list
                            || this.state.ignore_list != this.preview.ignore_list
                            || this.state.xslt != this.preview.xslt);
                    return result;
                }

                var is_settings_should_be_applied = () => {
                    return is_downloader_options_should_be_applied() || is_parser_options_should_be_applied();
                }

                var update_downloader_settings = (settings) => {
                    // Updating downloader [settings] @package_settings.update_downloader_settings
                    this.setState({'downloader_settings': settings});
                }

                add_tab('Change downloader',
                        render_change_downloader_tab({
                            downloader: this.state.downloader,
                            update_downloader: this.update_downloader,
                            downloader_settings: this.state.downloader_settings,
                            update_settings: update_downloader_settings,
                            downloaders: this.state.downloaders,
                            on_submit: this.apply_settings,
                            need_apply: is_settings_should_be_applied()
                        }));

                add_tab('Tune parser',
                        render_tune_parser_panel({
                            on_field_change: this.on_field_change,
                            on_submit: this.apply_settings,
                            search_list: this.state.search_list,
                            ignore_list: this.state.ignore_list,
                            xslt: this.state.xslt,
                            need_apply: is_settings_should_be_applied()
                        }));
            }
            
            if (this.preview.source != this.state.source) {
                content.push(<TunePanel>{render_change_source_plate(this.apply_settings)}</TunePanel>);
            } else {
                if (this.state.downloaders.length == 0) {
                    content.push(<TunePanel>{render_no_downloaders_plate()}</TunePanel>);
                } else {
                    content.push(
        <TunePanel>
          {render_tabs(tabs,
                       tab_panels)}
        </TunePanel>);
                }
            }
        }
        return (<div className="changelog-settings">{content}</div>);
    }
});
