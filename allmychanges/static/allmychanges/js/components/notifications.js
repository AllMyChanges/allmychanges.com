var React = require('react');

// пример использования нотификаций:
// PubSub.publish('show-info', 'Привет мир!');

module.exports = React.createClass({
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
                // closing item [item_id] @notifications
                items = this.state.items;
                items = _.filter(items, function(item) {return item.id != item_id});
                this.setState({items: items});
            }.bind(this);
        }.bind(this);

        if (this.state.show) {
            notifications = _.map(this.state.items,
                                function(item) {
                                        return <li className={"notifications__item notifications__" + item.class} key={item.id}><div className="notifications__close-button" onClick={closeItem2(item.id)}>+</div>{item.text}</li>
                                });
        }
        return  (<ul className="notifications">{notifications}</ul>);
    }
});
