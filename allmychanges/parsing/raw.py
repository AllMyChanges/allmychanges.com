from allmychanges.crawler import parse_changelog


class RawVersion(object):
    def __init__(self, number, date=None):
        self.number = number
        self.date = date


class RawChunk(object):
    def __init__(self, title, content):
        self.title = title
        self.content = content

    def get_versions(self):
        content = self.title + u'====\n\n' + self.content
        return map(self.create_version, parse_changelog(content))

    def create_version(self, struct):
        return RawVersion(struct['version'],
                          date=struct.get('date'))


class RawChangelog(object):
    def create_chunk(self, title, content):
        return RawChunk(title, content)
