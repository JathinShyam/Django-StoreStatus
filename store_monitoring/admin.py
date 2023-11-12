from django.contrib import admin
from .models import StoreStatus, BusinessHours, Timezone

admin.site.register(StoreStatus)
admin.site.register(BusinessHours)
admin.site.register(Timezone)