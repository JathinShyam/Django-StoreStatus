from datetime import datetime
from django.shortcuts import render
import csv
from .models import StoreStatus, BusinessHours, Timezone, StatusReport
from django.http import HttpResponse
from django.http import JsonResponse
from .forms import ReportGenerationForm
from datetime import timedelta
from django.db.models import QuerySet
import pytz
import secrets

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

            # We will create an object if does't exists
            StoreStatus.objects.get_or_create(
                store_id=store_id,
                timestamp_utc=timestamp_utc,
                defaults={'status': status.lower()}  # Convert to lowercase for consistency
            )
        return HttpResponse('Imported Successfully!')     
    

def populate_business_hours(request):
    with open('business_hours.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Skip header row
        for row in csv_reader:
            store_id, day_of_week, start_time_local, end_time_local = row

            # We will create an object if does't exists
            BusinessHours.objects.get_or_create(
                store_id=store_id,
                day_of_week=day_of_week,
                defaults={
                    'start_time_local': datetime.strptime(start_time_local, '%H:%M:%S').time(),
                    'end_time_local': datetime.strptime(end_time_local, '%H:%M:%S').time(),
                }
            )
        return HttpResponse('Imported Successfully!')
    

def populate_timezone(request):
    with open('timezone.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Skip header row
        for row in csv_reader:
            store_id, timezone_str = row

            # We will create an object if does't exists
            Timezone.objects.get_or_create(
                store_id=store_id,
                defaults={'timezone_str': timezone_str}
            )
        return HttpResponse('Imported Successfully!')


def generate_report_id():
    return secrets.token_hex(16)


def generate_report(store_id, timestamp = datetime.now()):

    store_id = store_id
    
    # Retrieve business hours and status data for the given store_id and timestamp
    day_of_week = timestamp.weekday() # Generates the weekday code of the day
    business_hours = get_business_hours(store_id, day_of_week) # Retrive business hours of the given day
    status_data = get_status_data(store_id, timestamp)  # Retrive store status for the timestamp
    
    # Calculate uptime and downtime
    uptime_last_hour = calculate_uptime_last_hour(status_data, business_hours, timestamp)
    downtime_last_hour = calculate_downtime_last_hour(status_data, business_hours, timestamp)

    if day_of_week == 0:
        day_of_week = 6
    else:
        day_of_week -= 1
    
    # Adding previous day business hours for the calculation
    business_hours = business_hours.union(get_business_hours(store_id, day_of_week)) 

    # Calculating the uptime and downtime
    uptime_last_day = calculate_uptime_last_day(status_data, business_hours, timestamp)
    downtime_last_day = calculate_downtime_last_day(status_data, business_hours, timestamp)

    # adding 1 week business hours for calculation
    for _ in range(5):
        if day_of_week == 0:
            day_of_week = 6
        else:
            day_of_week -= 1
        business_hours = business_hours.union(get_business_hours(store_id, day_of_week))

    uptime_last_week = calculate_uptime_last_week(status_data, business_hours, timestamp)
    downtime_last_week = calculate_downtime_last_week(status_data, business_hours, timestamp)

    # Save the report to the database
    report = StatusReport.objects.create(
        report_id = generate_report_id(),
        store_id=store_id,
        uptime_last_hour=uptime_last_hour,
        uptime_last_day=uptime_last_day,
        uptime_last_week=uptime_last_week,
        downtime_last_hour=downtime_last_hour,
        downtime_last_day=downtime_last_day,
        downtime_last_week=downtime_last_week,
    )

    return report.report_id


def get_business_hours(store_id, day_of_week) -> QuerySet:
    business_hours = BusinessHours.objects.filter(store_id=store_id, day_of_week = day_of_week)

    # If there is no store_id then assuming it runs for 24*7
    # create a new BusinessHours for calculation
    if not business_hours:
        a = BusinessHours.objects.create(
            store_id=store_id,
            day_of_week=day_of_week,
            start_time_local=datetime.strptime('00:00:00', '%H:%M:%S').time(),
            end_time_local=datetime.strptime('23:59:59', '%H:%M:%S').time(),
        )
        return QuerySet([a])
    return business_hours

def get_status_data(store_id, timestamp) -> QuerySet:
    status_data = StoreStatus.objects.filter(store_id=store_id, timestamp_utc__lte=timestamp)
    return status_data


def calculate_uptime_last_hour(status_data, business_hours, timestamp) -> int:
    counter = 0
    for i in business_hours:
        active_count_last_hour = status_data.filter(
            status='active',
            timestamp_utc__gte=timestamp - timedelta(hours=1),
            timestamp_utc__lte=timestamp,
            timestamp_utc__time__range=(i.start_time_local, i.end_time_local)
        ).count()
        counter += active_count_last_hour
    return counter * 60         # 60 minutes in a hour


def calculate_uptime_last_day(status_data, business_hours, timestamp):
    counter = 0
    for i in business_hours:
        active_count_last_day = status_data.filter(
            status='active',
            timestamp_utc__gte=timestamp - timedelta(days=1),
            timestamp_utc__lte=timestamp,
            timestamp_utc__time__range=(i.start_time_local, i.end_time_local)
        ).count()
        counter += active_count_last_day 
    return counter


def calculate_uptime_last_week(status_data, business_hours, timestamp):
    counter = 0
    for i in business_hours:
        active_count_last_week = status_data.filter(
            status='active',
            timestamp_utc__gte=timestamp - timedelta(weeks=1),
            timestamp_utc__lte=timestamp,
            timestamp_utc__time__range=(i.start_time_local, i.end_time_local)
        ).count()
        counter += active_count_last_week 
    return counter


def calculate_downtime_last_hour(status_data, business_hours, timestamp):
    counter = 0
    for i in business_hours:
        inactive_count_last_hour = status_data.filter(
            status='inactive',
            timestamp_utc__gte=timestamp - timedelta(hours=1),
            timestamp_utc__lte=timestamp,
            timestamp_utc__time__range=(i.start_time_local, i.end_time_local)
        ).count()
        counter += inactive_count_last_hour
    return counter


def calculate_downtime_last_day(status_data, business_hours, timestamp):
    counter = 0
    for i in business_hours:
        inactive_count_last_day = status_data.filter(
            status='inactive',
            timestamp_utc__gte=timestamp - timedelta(days=1),
            timestamp_utc__lte=timestamp,
            timestamp_utc__time__range=(i.start_time_local, i.end_time_local)
        ).count()
        counter += inactive_count_last_day 
    return counter


def calculate_downtime_last_week(status_data, business_hours, timestamp):
    counter = 0
    for i in business_hours:
        inactive_count_last_week = status_data.filter(
            status='inactive',
            timestamp_utc__gte=timestamp - timedelta(weeks=1),
            timestamp_utc__lte=timestamp,
            timestamp_utc__time__range=(i.start_time_local, i.end_time_local)
        ).count()
        counter += inactive_count_last_week 
    return counter


def trigger_report(request):

    if request.method == 'POST':
        form = ReportGenerationForm(request.POST)
        if form.is_valid():
            store_id = form.cleaned_data['store_id']
            timestamp = form.cleaned_data['timestamp']
            
            try:
                # Retriving the TimeZone object for the given store_id for conversion to local time
                timezone_obj = Timezone.objects.get(store_id=store_id)
                timezone_str = timezone_obj.timezone_str
                # Converting UTC to local time
                local_timestamp = convert_utc_to_local(timestamp, timezone_str)
            except Timezone.DoesNotExist:
                local_timestamp = convert_utc_to_local(timestamp, 'America/Chicago')

            report_id = generate_report(store_id, local_timestamp)

            # TODO: Polling or batch processing
            return HttpResponse(f"Report generated successfully. Report ID: {report_id}")
    else:
        form = ReportGenerationForm()

    return render(request, 'store_monitoring/trigger_report.html', {'form': form})


def get_report(request, report_id):
    try:
        report = StatusReport.objects.get(report_id=report_id)
        # Return the report details in JSON format
        report_data = {
            "status": "Complete",
            "store_id": report.store_id,
            "uptime_last_hour": report.uptime_last_hour,
            "uptime_last_day": report.uptime_last_day,
            "uptime_last_week": report.uptime_last_week,
            "downtime_last_hour": report.downtime_last_hour,
            "downtime_last_day": report.downtime_last_day,
            "downtime_last_week": report.downtime_last_week,
        }

        # Write the report details to a CSV file
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="report.csv"'

        csv_writer = csv.writer(response)
        csv_writer.writerow(["Field", "Value"])

        for field, value in report_data.items():
            csv_writer.writerow([field, value])

        return response
    except StatusReport.DoesNotExist:
        return JsonResponse({"status": "Running"})
    

def convert_utc_to_local(utc_time, timezone_str):
    utc = pytz.timezone('UTC')
    local_timezone = pytz.timezone(timezone_str)
    utc_time = utc.localize(utc_time)
    local_time = utc_time.astimezone(local_timezone)
    return local_time
