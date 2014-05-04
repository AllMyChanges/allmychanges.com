"""Logster parsers"""
from __future__ import absolute_import

import anyjson
from logster.parsers.ErrorLogLogster import (ErrorLogLogster as _ErrorLogLogster,
                                             LogsterParsingException)

class ErrorLogLogster(_ErrorLogLogster):
    def __init__(self, *args, **kwargs):
        super(ErrorLogLogster, self).__init__(*args, **kwargs)
        self.levels = ('debug', 'info', 'error', 'warning')
        
    def parse_line(self, line):
        try:
            data = anyjson.deserialize(line)
        except:
            raise LogsterParsingException('unable to parse json')

        level = data['@fields']['level'].lower()

        if level not in self.levels:
            level = 'other'
            
        self.counters[level] += 1
        
