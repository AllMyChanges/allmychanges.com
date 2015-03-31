module.exports = {
    reach_goal: function(name) {
        if (window.yaCounter !== undefined) {
            // registering goal [name] @metrika.reach_goal
            window.yaCounter.reachGoal(name);
        }
    }
}
