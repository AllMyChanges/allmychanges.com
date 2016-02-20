def calculate_issue_importance(num_trackers, user, light_user):
    """Calculates issue's importance, based on the changelog's popularity
    and if it was reported by human or a robot.
    """
    importance = 1 + num_trackers

    if user:
        importance *= 10

    return importance
