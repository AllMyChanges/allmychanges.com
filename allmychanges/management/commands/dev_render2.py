# coding: utf-8
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.browser import Browser


class Command(LogMixin, BaseCommand):
    help = u"""Download package sources into a temporary directory."""

    def handle(self, *args, **options):
	webkit = Browser()
	path = 'capture2.png'
        url = 'https://allmychanges.com/p/python/django-fields'

	webkit.save_image(url, path, width=590)
	print "Image Saved to", path
