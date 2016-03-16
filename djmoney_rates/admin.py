from django.contrib import admin
from .models import Rate


class RateAdmin(admin.ModelAdmin):
    list_display = ['currency', 'value', 'date', 'source']
    list_filter = ['currency']
    readonly_fields = ['source']


admin.site.register(Rate, RateAdmin)
