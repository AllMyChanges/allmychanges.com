#!/usr/bin/env python
# coding: utf-8

import re
import envoy


def parse_state(line):
    match = re.search('\[(?P<state>[^\]]+?)\] at time', line)
    if match:
        return match.group('state')

def parse_time(line):
    time = line.rsplit(' ', 1)[-1]
    time = map(float, time.split(':'))
    return time[0] * 60 * 60 + time[1] * 60 + time[2]

def format_duration(seconds):
    if seconds > 60:
        minutes = int(seconds) / 60
        seconds = seconds - minutes * 60
        return '{0} minutes and {1} seconds'.format(
            minutes, seconds)
    else:
        return '{0} seconds'.format(seconds)

def process(lines):
    starts = {}
    for line in lines:
        line = line.strip()

        if 'Running state' in line:
            state = parse_state(line)
            starts[state] = parse_time(line)
        elif 'Completed state' in line:
            state = parse_state(line)
            end = parse_time(line)
            duration = end - starts[state]
            if duration > 30:
                print 'State {0} took {1}'.format(state,
                                                  format_duration(duration))
        else:
            print ''
            print line


if __name__ == '__main__':
    command = "sudo grep -e 'Running state' -e 'Completed state' -e 'Executing command state.highstate' /var/log/salt/minion"
    response = envoy.run(command)

    if response.std_err:
        print response.std_err
    else:
        lines = response.std_out.split('\n')
        process(lines)
