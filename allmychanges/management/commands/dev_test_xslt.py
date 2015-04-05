# /tmp/allmychanges/tmpAxgowO/2015/02/minecraft-1-8-2-is-now-available/index.html

from lxml import etree
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin


class Command(LogMixin, BaseCommand):
    help = u"""Send release beats to graphite."""

    def handle(self, *args, **options):
        filename, template = args
        xslt = etree.XSLT(etree.parse(template))

        parser = etree.HTMLParser()
        doc = etree.parse(filename, parser)
        new_doc = xslt(doc)
        print etree.tostring(doc, pretty_print=True)
        print '\n================================\n'
        print etree.tostring(new_doc, pretty_print=True)
