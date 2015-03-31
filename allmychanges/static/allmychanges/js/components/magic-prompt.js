// uses jquery typeahead plugin:
// http://twitter.github.io/typeahead.js/

module.exports = React.createClass({
    componentDidMount: function(){
        var element = this.getDOMNode();
        var fetch_timer;
        var fetch_suggestions = function(query, cb) {
            clearTimeout(fetch_timer);
            fetch_timer = setTimeout(function () {
                really_fetch_suggestions(query, cb)
            }, 500);
        }
        var really_fetch_suggestions = function(query, cb) {
            $.get('/v1/search-autocomplete/', {q: query}, function(data) {
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
                minLength: 1,
                highlight: true
            },
            {
                name: 'magic-prompt',
                displayKey: 'value',
                
                // Just a little object that implements the necessary 
                // signature to plug into typeahead.js
                source: fetch_suggestions,
                templates: {
                    empty: '<div class="magic-prompt__no-matches">No matches found</div>',
                    suggestion: show_suggestion
                }
        }).focus();
        
        // Behind the scenes, this is just delegating to Backbone's router
        // to 'navigate' the main pane of the page to a different view
        $(element).on('typeahead:selected', function(jquery, option){
            window.location = option.url;
        });
    },
    
    componentWillUnmount: function(){
        var element = this.getDOMNode();
        $(element).find('.magic-prompt__input').typeahead('destroy');
    },

    render: function(){
        return (
            <div className="magic-prompt">
                <form action="/search/" method="GET">
                  <input type="search" name="q" ref="input" 
                         className="magic-prompt__input" 
                         placeholder="Search packages and namespaces"/>
                  <input type="submit" className="button _good _large magic-prompt__submit" value="Search"/>
                </form>
            </div>
        );
    }
});
