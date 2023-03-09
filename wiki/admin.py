from django.contrib import admin
from .models import *

admin.site.register(Event)
admin.site.register(Sponsor)
admin.site.register(Participation)


class RiderAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ('name', )}


admin.site.register(Rider, RiderAdmin)
