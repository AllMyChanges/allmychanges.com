#!/usr/bin/env zsh

source ~/.zsh/growl

nosetests --failed && nb 'Tests PASSED' || nb 'Tests ERROR'


