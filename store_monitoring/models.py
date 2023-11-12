from django.db import models

class StoreStatus(models.Model):
    store_id = models.CharField(max_length=20)  # Adjust the max length as needed
    timestamp_utc = models.DateTimeField()
    status = models.CharField(max_length=10)  # 'active' or 'inactive'


class BusinessHours(models.Model):
    store_id = models.CharField(max_length=20)  # Adjust the max length as needed
    day_of_week = models.IntegerField()  # 0=Monday, 6=Sunday
    start_time_local = models.TimeField()
    end_time_local = models.TimeField()


class Timezone(models.Model):
    store_id = models.CharField(max_length=20)
    timezone_str = models.CharField(max_length=50)
