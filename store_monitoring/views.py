from datetime import datetime
from django.shortcuts import render
import csv
from .models import StoreStatus, BusinessHours, Timezone, StatusReport
from django.http import HttpResponse
from django.http import JsonResponse
from .forms import ReportGenerationForm

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
        



def generate_report(store_id, timestamp):

    # Replace 'example_store' with the actual store_id
    store_id = store_id
    
    # Retrieve business hours and status data for the given store_id and timestamp
    business_hours = get_business_hours(store_id)
    status_data = get_status_data(store_id, timestamp)
    
    # Calculate uptime and downtime
    uptime_last_hour = calculate_uptime_last_hour(status_data, business_hours, timestamp)
    uptime_last_day = calculate_uptime_last_day(status_data, business_hours, timestamp)
    uptime_last_week = calculate_uptime_last_week(status_data, business_hours, timestamp)
    downtime_last_hour = calculate_downtime_last_hour(status_data, business_hours, timestamp)
    downtime_last_day = calculate_downtime_last_day(status_data, business_hours, timestamp)
    downtime_last_week = calculate_downtime_last_week(status_data, business_hours, timestamp)

    # Save the report to the database
    report = StatusReport.objects.create(
        report_id = f"{store_id}_{timestamp}",
        store_id=store_id,
        uptime_last_hour=uptime_last_hour,
        uptime_last_day=uptime_last_day,
        uptime_last_week=uptime_last_week,
        downtime_last_hour=downtime_last_hour,
        downtime_last_day=downtime_last_day,
        downtime_last_week=downtime_last_week,
    )

    return report.report_id

def get_business_hours(store_id):
    business_hours = BusinessHours.objects.filter(store_id=store_id)
    if not business_hours:
        a = BusinessHours.objects.create(
            store_id=store_id,
            day_of_week=0,
            start_time_local=datetime.strptime('00:00:00', '%H:%M:%S').time(),
            end_time_local=datetime.strptime('23:00:00', '%H:%M:%S').time(),
        )
        return a
    return business_hours

def get_status_data(store_id, timestamp):
    status_data = StoreStatus.objects.filter(store_id=store_id, timestamp_utc__lte=timestamp)
    return status_data

def calculate_uptime_last_hour(status_data, business_hours, timestamp):
    active_count_last_hour = status_data.filter(
        status='active',
        timestamp_utc__gte=timestamp - timedelta(hours=1),
        timestamp_utc__lte=timestamp,
        # timestamp_utc__time__range=(business_hours.start_time_local, business_hours.end_time_local)
    ).count()
    return active_count_last_hour * 60  # Convert to minutes


from datetime import timedelta

def calculate_uptime_last_day(status_data, business_hours, timestamp):
    active_count_last_day = status_data.filter(
        status='active',
        timestamp_utc__gte=timestamp - timedelta(days=1),
        timestamp_utc__lte=timestamp,
        # timestamp_utc__time__range=(business_hours.start_time_local, business_hours.end_time_local)
    ).count()
    return active_count_last_day * 60  # Convert to minutes

def calculate_uptime_last_week(status_data, business_hours, timestamp):
    active_count_last_week = status_data.filter(
        status='active',
        timestamp_utc__gte=timestamp - timedelta(weeks=1),
        timestamp_utc__lte=timestamp,
        # timestamp_utc__time__range=(business_hours.start_time_local, business_hours.end_time_local)
    ).count()
    return active_count_last_week * 60  # Convert to minutes

def calculate_downtime_last_hour(status_data, business_hours, timestamp):
    inactive_count_last_hour = status_data.filter(
        status='inactive',
        timestamp_utc__gte=timestamp - timedelta(hours=1),
        timestamp_utc__lte=timestamp,
        # timestamp_utc__time__range=(business_hours.start_time_local, business_hours.end_time_local)
    ).count()
    return inactive_count_last_hour * 60  # Convert to minutes

def calculate_downtime_last_day(status_data, business_hours, timestamp):
    inactive_count_last_day = status_data.filter(
        status='inactive',
        timestamp_utc__gte=timestamp - timedelta(days=1),
        timestamp_utc__lte=timestamp,
        # timestamp_utc__time__range=(business_hours.start_time_local, business_hours.end_time_local)
    ).count()
    return inactive_count_last_day * 60  # Convert to minutes

def calculate_downtime_last_week(status_data, business_hours, timestamp):
    inactive_count_last_week = status_data.filter(
        status='inactive',
        timestamp_utc__gte=timestamp - timedelta(weeks=1),
        timestamp_utc__lte=timestamp,
        # timestamp_utc__time__range=(business_hours.start_time_local, business_hours.end_time_local)
    ).count()
    return inactive_count_last_week * 60  # Convert to minutes




def trigger_report(request):

    if request.method == 'POST':
        form = ReportGenerationForm(request.POST)
        if form.is_valid():
            store_id = form.cleaned_data['store_id']
            timestamp = form.cleaned_data['timestamp']

            report_id = generate_report(store_id, timestamp)
            return HttpResponse(f"Report generated successfully. Report ID: {report_id}")
    else:
        form = ReportGenerationForm()

    return render(request, 'store_monitoring/trigger_report.html', {'form': form})




def get_report(request, report_id):
    try:
        report = StatusReport.objects.get(report_id=report_id)
        # Return the report details in the specified format
        report_data = {
            "store_id": report.store_id,
            "uptime_last_hour": report.uptime_last_hour,
            "uptime_last_day": report.uptime_last_day,
            "uptime_last_week": report.uptime_last_week,
            "downtime_last_hour": report.downtime_last_hour,
            "downtime_last_day": report.downtime_last_day,
            "downtime_last_week": report.downtime_last_week,
        }
        return JsonResponse(report_data)
    except StatusReport.DoesNotExist:
        return JsonResponse({"error": "Report not found"}, status=404)