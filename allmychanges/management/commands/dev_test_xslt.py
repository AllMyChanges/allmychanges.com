# /tmp/allmychanges/tmpAxgowO/2015/02/minecraft-1-8-2-is-now-available/index.html
import sys

from lxml import etree
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin


class Command(LogMixin, BaseCommand):
    help = u"""Send release beats to graphite."""

    def handle(self, *args, **options):
        filename, template = args
        parser = etree.HTMLParser()
        sys.stderr.write('Loading {0}\n'.format(filename))
        doc = etree.parse(filename, parser)

        sys.stderr.write('Loading {0}\n'.format(template))
        pre_xslt = etree.parse(template)
        transform = etree.XSLT(pre_xslt)

        new_doc = transform(doc)
#        print etree.tostring(doc, pretty_print=True)
#        print '\n================================\n'
        print etree.tostring(new_doc, pretty_print=True).encode('utf-8')
