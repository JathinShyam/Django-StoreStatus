from django.db import models

class StoreStatus(models.Model):
    store_id = models.CharField(max_length=20)  # Adjust the max length as needed
    timestamp_utc = models.DateTimeField()
    status = models.CharField(max_length=10)  # 'active' or 'inactive'

    def __str__(self):
        return f"Report {self.store_id}"


class BusinessHours(models.Model):
    store_id = models.CharField(max_length=20)  # Adjust the max length as needed
    day_of_week = models.IntegerField()  # 0=Monday, 6=Sunday
    start_time_local = models.TimeField()
    end_time_local = models.TimeField()

    def __str__(self):
        return f"Report {self.store_id}"


class Timezone(models.Model):
    store_id = models.CharField(max_length=20)
    timezone_str = models.CharField(max_length=50)

    def __str__(self):
        return f"Report {self.store_id}"

class StatusReport(models.Model):
    report_id = models.CharField(max_length=50, unique=True)
    store_id = models.CharField(max_length=20)
    uptime_last_hour = models.IntegerField()
    uptime_last_day = models.IntegerField()
    uptime_last_week = models.IntegerField()
    downtime_last_hour = models.IntegerField()
    downtime_last_day = models.IntegerField()
    downtime_last_week = models.IntegerField()

    def __str__(self):
        return f"Report {self.report_id}"
