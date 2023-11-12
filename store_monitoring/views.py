from datetime import datetime
from django.shortcuts import render
import csv
from .models import StoreStatus, BusinessHours, Timezone
from django.http import HttpResponse


def populate_store_status(request):
    with open('store_status.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Skip header row
        for row in csv_reader:
            store_id, status, timestamp_utc = row
            try:
                timestamp_utc = datetime.strptime(timestamp_utc, '%Y-%m-%d %H:%M:%S.%f %Z')
            except ValueError:
                # Handle variations in timestamp format
                timestamp_utc = datetime.strptime(timestamp_utc, '%Y-%m-%d %H:%M:%S %Z')

            StoreStatus.objects.create(
                store_id=store_id,
                timestamp_utc=timestamp_utc,
                status=status.lower()  # Convert to lowercase for consistency
            )
        return HttpResponse('Imported Successfully!')     
    

def populate_business_hours(request):
    with open('business_hours.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Skip header row
        for row in csv_reader:
                store_id, day_of_week, start_time_local, end_time_local = row
                BusinessHours.objects.create(
                    store_id=store_id,
                    day_of_week=day_of_week,
                    start_time_local=datetime.strptime(start_time_local, '%H:%M:%S').time(),
                    end_time_local=datetime.strptime(end_time_local, '%H:%M:%S').time(),
                )
        return HttpResponse('Imported Successfully!')
    

def populate_timezone(request):
    with open('timezone.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Skip header row
        for row in csv_reader:
            store_id, timezone_str = row
            Timezone.objects.create(
                store_id=store_id,
                timezone_str=timezone_str
            )
        return HttpResponse('Imported Successfully!')
        

    
