# -*- coding: utf-8 -*-
from django.contrib import admin

from allmychanges.models import (
    Subscription)


class SubscriptionAdmin(admin.ModelAdmin):
    pass


admin.site.register(Subscription, SubscriptionAdmin)
