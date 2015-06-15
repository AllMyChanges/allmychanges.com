import re

def _process_rule(line):
    line = line.strip()
    if line.startswith('s/'):
        rule = line[2:].split('/')
        return re.compile(rule[0]), rule[1]


def sed(rules):
    rules = filter(None, map(_process_rule, rules.split(u'\n')))

    def sed_processor(text):
        for regex, replacement in rules:
            text = regex.sub(replacement, text)
        return text
    return sed_processor
