# coding: utf-8

import re


ESCAPED_SLASH = '%ESCAPED_SLASH%'


def _process_rule(line):
    line = line.strip()
    if line.startswith('s/'):
        line = line[2:]
        # replace escaped slashes
        line = line.replace(ur'\/', ESCAPED_SLASH)
        rule = line.split('/')
        # replace slashes back and unescape them
        rule = [item.replace(ESCAPED_SLASH, ur'/')
                for item in rule]

        what_to_replace = rule[0]
        replacement = rule[1]
        return re.compile(what_to_replace, re.MULTILINE), replacement


def sed(rules):
    rules = filter(None, map(_process_rule, rules.split(u'\n')))

    def sed_processor(text):
        for regex, replacement in rules:
            text = regex.sub(replacement, text)
        return text
    return sed_processor
