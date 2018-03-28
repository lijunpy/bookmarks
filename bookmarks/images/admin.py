# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Image


# Register your models here.
class ImageAdmin(admin.ModelAdmin):
    list_display = ['id','title', 'slug', 'image', 'created']
    list_filter = ['created']
    list_editable = ['title']


admin.site.register(Image, ImageAdmin)

