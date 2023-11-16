from datetime import datetime
from django.shortcuts import render
import csv
from .models import StoreStatus, BusinessHours, Timezone, StatusReport
from django.http import HttpResponse
from django.http import JsonResponse
from .forms import ReportGenerationForm
from datetime import timedelta
from django.db.models import QuerySet
# from django.db.models import Count
import pytz
# import random
import secrets
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_POST, require_GET
# from django.shortcuts import get_object_or_404
from django.db.models import Sum, ExpressionWrapper, fields,F

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
            Timezone.objects.get_or_create(
                store_id=store_id,
                defaults={'timezone_str': timezone_str}
            )
        return HttpResponse('Imported Successfully!')


def generate_report_id():
    return secrets.token_hex(16)


def generate_report(store_id, timestamp):

    store_id = store_id
    
    # Retrieve business hours and status data for the given store_id and timestamp
    day_of_week = timestamp.weekday()
    print("***************")
    print(day_of_week)
    print("***************")
    business_hours = get_business_hours(store_id, day_of_week)
    
    status_data = get_status_data(store_id, timestamp)
    # print("***************")
    # print(status_data)
    # print("***************")
    
    
    # Calculate uptime and downtime
    uptime_last_hour = calculate_uptime_last_hour(status_data, business_hours, timestamp)
    downtime_last_hour = calculate_downtime_last_hour(status_data, business_hours, timestamp)

    if day_of_week == 0:
        day_of_week = 6
    else:
        day_of_week -= 1
    business_hours = business_hours.union(get_business_hours(store_id, day_of_week))

    # print("***************")
    # for i in business_hours:
    #     print(i.start_time_local)
    #     print(i.end_time_local)
    #     # Convert time objects to datetime objects
    #     start_datetime = datetime.combine(datetime.today(), i.start_time_local)
    #     end_datetime = datetime.combine(datetime.today(), i.end_time_local)

    #     # Calculate the time difference
    #     time_difference = end_datetime - start_datetime
    #     # Convert time difference to total seconds (as an integer)
    #     total_seconds = int(time_difference.total_seconds())

    #     print(time_difference)
    #     print(total_seconds / 3600)
    # print("***************")

    uptime_last_day = calculate_uptime_last_day(status_data, business_hours, timestamp)
    downtime_last_day = calculate_downtime_last_day(status_data, business_hours, timestamp)

    for _ in range(5):
        if day_of_week == 0:
            day_of_week = 6
        else:
            day_of_week -= 1
        business_hours = business_hours.union(get_business_hours(store_id, day_of_week))

    print("***************")
    for i in business_hours:
        print(i.start_time_local)
        print(i.end_time_local)
        # Convert time objects to datetime objects
        start_datetime = datetime.combine(datetime.today(), i.start_time_local)
        end_datetime = datetime.combine(datetime.today(), i.end_time_local)

        # Calculate the time difference
        time_difference = end_datetime - start_datetime
        # Convert time difference to total seconds (as an integer)
        total_seconds = int(time_difference.total_seconds())

        print(time_difference)
        print(total_seconds / 3600)
    print("***************")


    uptime_last_week = calculate_uptime_last_week(status_data, business_hours, timestamp)
    downtime_last_week = calculate_downtime_last_week(status_data, business_hours, timestamp)
    # if uptime_last_hour == 0:
    #     downtime_last_hour = 60
    # if uptime_last_day == 0:
    #     downtime_last_day = 24
    # if uptime_last_week == 0:
    #     downtime_last_week = 168
    # if downtime_last_hour == 0:
    #     uptime_last_hour = 60
    # if downtime_last_day == 0:
    #     uptime_last_day = 24
    # if downtime_last_week == 0:
    #     uptime_last_week = 168

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
    # print(type(business_hours))
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

            # timezone_str = Timezone.objects.get(store_id, "America/Chicago")
            # local_timestamp = convert_utc_to_local(timestamp, timezone_str)
            
            try:
                timezone_obj = Timezone.objects.get(store_id=store_id)
                timezone_str = timezone_obj.timezone_str
                print("***************")
                print(timezone_str)
                print(timestamp)
                local_timestamp = convert_utc_to_local(timestamp, timezone_str)
            except Timezone.DoesNotExist:
                local_timestamp = convert_utc_to_local(timestamp, 'America/Chicago')
            print(local_timestamp)
            print("***************")

            report_id = generate_report(store_id, local_timestamp)
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


# def compute_metrics(store_id, store_activity_data, business_hours_data, timezone_data):
#     # Filter data for the specific store
#     store_activity_data = store_activity_data.filter(store_id=store_id)

#     # Get the local timezone for the store
#     timezone_str = timezone_data.get(store_id, 'America/Chicago')

#     # Initialize metrics
#     uptime_last_hour = downtime_last_hour = uptime_last_day = downtime_last_day = uptime_last_week = downtime_last_week = 0

#     # Get the current timestamp (assumed to be the max timestamp among all observations)
#     current_timestamp = store_activity_data.aggregate(max_timestamp=Count('timestamp_utc'))['max_timestamp']

#     # Iterate over the store activity data
#     for observation in store_activity_data:
#         timestamp_utc = observation.timestamp_utc
#         status = observation.status

#         # Convert UTC timestamp to local time
#         local_timestamp = convert_utc_to_local(timestamp_utc, timezone_str)

#         # Check if the observation falls within business hours
#         business_hours = business_hours_data.get(store_id, {})
#         if (
#             local_timestamp.weekday() == business_hours.get('day_of_week', local_timestamp.weekday())
#             and business_hours.get('start_time_local') <= local_timestamp.time() <= business_hours.get('end_time_local')
#         ):
#             # Calculate time difference between the current timestamp and the observation timestamp
#             time_difference = current_timestamp - timestamp_utc

#             # Update metrics based on status
#             if status == 'active':
#                 uptime_last_hour += time_difference.total_seconds() / 60
#                 uptime_last_day += time_difference.total_seconds() / 3600
#                 uptime_last_week += time_difference.total_seconds() / 3600
#             elif status == 'inactive':
#                 downtime_last_hour += time_difference.total_seconds() / 60
#                 downtime_last_day += time_difference.total_seconds() / 3600
#                 downtime_last_week += time_difference.total_seconds() / 3600

#     metrics_data = {
#         'uptime_last_hour': round(uptime_last_hour, 2),
#         'uptime_last_day': round(uptime_last_day, 2),
#         'uptime_last_week': round(uptime_last_week, 2),
#         'downtime_last_hour': round(downtime_last_hour, 2),
#         'downtime_last_day': round(downtime_last_day, 2),
#         'downtime_last_week': round(downtime_last_week, 2),
#     }

#     return metrics_data


# @csrf_exempt
# @require_POST
# def trigger_report(request):
#     # Your logic for data ingestion and report generation goes here...
#     # Make sure to populate the StatusReport model with the calculated metrics

#     report_id = generate_report_id()
    
#     # Assuming store_id, store_activity_data, business_hours_data, and timezone_data are available
#     for store_id in store_ids:
#         store_activity_data = StoreStatus.objects.filter(store_id=store_id)
#         business_hours_data = BusinessHours.objects.filter(store_id=store_id)
#         timezone_data = Timezone.objects.filter(store_id=store_id).first()

#         metrics_data = compute_metrics(store_id, store_activity_data, business_hours_data, timezone_data.timezone_str)

#         # Create or update StatusReport model
#         report, created = StatusReport.objects.update_or_create(
#             store_id=store_id,
#             defaults={
#                 'uptime_last_hour': metrics_data['uptime_last_hour'],
#                 'uptime_last_day': metrics_data['uptime_last_day'],
#                 'uptime_last_week': metrics_data['uptime_last_week'],
#                 'downtime_last_hour': metrics_data['downtime_last_hour'],
#                 'downtime_last_day': metrics_data['downtime_last_day'],
#                 'downtime_last_week': metrics_data['downtime_last_week'],
#             }
#         )

#     return JsonResponse({'report_id': report_id})

