# coding: utf-8
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from allmychanges.source_guesser import guess_source
from allmychanges.models import Changelog


class Command(LogMixin, BaseCommand):
    help = u"""Command to test how well we are able to guess source by namespace and name."""

    def handle(self, *args, **options):
        if args:
            packages = [arg.split('/') + [None]
                        for arg in args]
            show_match = False
        else:
            packages = [(p.namespace, p.name, p)
                        for p in Changelog.objects.all()]
            show_match = True

        total = len(packages)
        matched = 0
        have_guesses = 0

        for namespace, name, package in packages:
            urls = list(guess_source(namespace, name))
            if urls:
                have_guesses += 1

                if show_match:
                    if package.source in urls:
                        matched += 1
                    else:
                        print ''
                        print '!!! Handwritten source is: ', package.source

            print '{0}/{1}: {2}'.format(
                namespace, name, urls)

        if show_match:
            print 'For {0:.4}% packages, hand choosen url was also among guessed.'.format(
                float(matched) / total * 100)

        print 'For {0:.4}% packages, we have some guesses.'.format(
                float(have_guesses) / total * 100)
