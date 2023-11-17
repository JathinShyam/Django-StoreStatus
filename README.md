# Django-StoreStatus

This Django project is designed to monitor the online status of stores based on provided data sources. It includes backend APIs to generate reports on store uptime and downtime within specific time intervals.

## Overview

The primary goal of this project is to address the need for real-time monitoring of store activity. By leveraging data from multiple sources, including CSV files containing store status, business hours, and timezone information, the system aims to provide accurate and timely insights for restaurant owners.


## Data Sources

1. **Store Status CSV**: Contains information about whether the store was active or inactive at specific timestamps.
   - [View CSV](link_to_store_status_csv)

2. **Business Hours CSV**: Provides business hours for all stores, including day of the week, start time, and end time.
   - [View CSV](link_to_business_hours_csv)

3. **Timezone CSV**: Specifies the timezone for each store.
   - [View CSV](link_to_timezone_csv)

## System Requirements

- The data is not static; the system should dynamically handle updates every hour.
- CSV data is stored in a relevant database, and API calls are made to retrieve the data.

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/JathinShyam/Django-StoreStatus.git
   
2. Install project dependencies:
   ```bash
   pip install -r requirements.txt

3. Apply database migrations:
   ```bash
   python manage.py migrate

4. Create a superuser(admin):
   ```bash
   python manage.py createsuperuser

5. Run the development server:
   ```bash
   python manage.py runserver

The project should now be accessible at http://localhost:8000/.


## Report Output
The system outputs a report to the user with the following metrics:

store_id, uptime_last_hour (in minutes), uptime_last_day (in hours), uptime_last_week (in hours), downtime_last_hour (in minutes), downtime_last_day (in hours), downtime_last_week (in hours)

## API Endpoints
**/trigger_report:** Endpoint to trigger report generation.

*Input:* No input required.

*Output:* Report ID (random string).

**/get_report:** Endpoint to retrieve the status of the report or the CSV file.

*Input:* Report ID.

*Output:*
If report generation is not complete, return "Running." (Under process)

If report generation is complete, return "Complete" along with the CSV file.


