var css = require('./index.styl');
var React = require('react');
var R = require('ramda');
var ReactMDL = require('react-mdl');
var FABButton = ReactMDL.FABButton;
var Button = ReactMDL.Button;
var Icon = ReactMDL.Icon;
var List = ReactMDL.List;
var Textfield = ReactMDL.Textfield;
var ListItem = ReactMDL.ListItem;
var ListItemContent = ReactMDL.ListItemContent;
var ListItemAction = ReactMDL.ListItemAction;


module.exports = React.createClass({
    getInitialState: function () {
        return {
            show_dialog: false,
            new_tag_name: '',
            tag_name_error: '',
            tags: [],
        };
    },
    handle_click: function (e) {
        this.setState({'show_dialog': true});
        //        e.preventDefault();
        
        $.ajax({
            url: '/v1/tags/?version_id=' + this.props.version_id,
            success: (data) => {
                var tags = R.map(R.prop('name'), data['results']);
                this.setState({tags: tags});
            },
            error: (xhr, status, err) => {
                console.error('Unable to fetch tags for the version', status, err.toString());
            }
        });
    },
    handle_popup_click: function (e) {
    },
    on_done: function (e) {
        e.preventDefault();
        window.location = window.location;
    },
    update_new_tag_name: function (e) {
        this.setState({'new_tag_name': e.target.value});
    },
    check_if_enter_was_pressed: function (e) {
        if (e.key === 'Enter') {
            this.add_new_tag(e);
        }
    },
    add_new_tag: function (e) {
        e.preventDefault();

        // фиксируем значение, которое отправим на сервер
        var new_tag_name = this.state.new_tag_name;
        
        // TODO: добавить обработку случая, когда тег нулевой длинны
        
        $.ajax({
            url: '/v1/changelogs/' + this.props.project_id + '/tag/',
            method: 'POST',
            dataType: 'json',
            data: {
                name: new_tag_name,
                version: this.props.version_number
            },
            headers: {'X-CSRFToken': $.cookie('csrftoken')},
            success: (data) => {
                var new_tags = this.state.tags;
                new_tags.push(new_tag_name)
                this.setState({
                    tags: new_tags,
                    tag_name_error: '',
                    new_tag_name: ''
                });
            },
            error: (xhr, status, err) => {
                var error_message = xhr.responseJSON.errors.name[0];
                this.setState({tag_name_error: error_message});
            }
        })
    },
    render: function() {
        if (this.state.show_dialog) {

            var tag_item = (name) => {
                var remove_tag = () => {
                    $.ajax({
                        url: '/v1/changelogs/' + this.props.project_id + '/untag/',
                        method: 'POST',
                        dataType: 'json',
                        data: {
                            name: name,
                        },
                        headers: {'X-CSRFToken': $.cookie('csrftoken')},
                        success: (data) => {
                            var new_tags = this.state.tags.filter(
                                (item) => item != name);
                            this.setState({tags: new_tags});
                        },
                        error: (xhr, status, err) => {
                            // TODO: добавить обработку ошибок и отображение их пользователю
                            console.error('Unable to remove tag', status, err.toString());
                        }
                    })
                }

                return (
                        <ListItem key={name}>
                          <ListItemContent icon="label">{name}</ListItemContent>
                          <ListItemAction><FABButton onClick={remove_tag} className="md-18"><Icon name="remove"/></FABButton></ListItemAction>
                        </ListItem>
                );
            };
            var tags = R.map(tag_item, this.state.tags);
            
            return (
                <div className="modal-popup" onClick={this.handle_popup_click}>
                    <div className="modal-popup__content">
                    <p>These tags are private, only you manage and see them.</p>
                    <List>
                       {tags}
                    </List>
                    <table width="100%">
                      <tr>
                        <td width="100%" style={{"padding-right": "18px"}}>
                          <Textfield onChange={this.update_new_tag_name}
                                     onKeyPress={this.check_if_enter_was_pressed}
                                     label="New tag's name"
                                     pattern="^[a-z][a-z0-9-.]{0,38}[a-z0-9]$"
                                     value={this.state.new_tag_name}
                                     error={this.state.tag_name_error}
                                     floatingLabel/></td>
                        <td><FABButton onClick={this.add_new_tag} className="md-18"><Icon name="add"/></FABButton></td>
                      </tr>
                    </table>
                    <p className="close-button-row"><Button onClick={this.on_done}>Close</Button></p>
                    </div>
                </div>
            );
        } else {
            return (<button className="button" onClick={this.handle_click}>Tag</button>);
        }
    }
});
