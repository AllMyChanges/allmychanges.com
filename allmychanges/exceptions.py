class UpdateError(Exception):
    pass

class DownloaderWarning(Exception):
    pass

class AppStoreAppNotFound(Exception):
    def __init__(self, app_id):
        super(AppStoreAppNotFound, self).__init__(
            'AppStore app with id {0} wasn\'t found in appstore'.format(app_id))
        self.app_id = app_id


class SynonymError(RuntimeError):
    """This exception is raised during synonym's binding
    to the project.
    """
