from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime

class ReportGenerationForm(forms.Form):
    store_id = forms.CharField(max_length=20, label='Store ID')
    timestamp = forms.DateTimeField(label='Timestamp', help_text='Format: YYYY-MM-DD HH:MM:SS')

    def clean_timestamp(self):
        timestamp = self.cleaned_data['timestamp']
        
        # Define your desired timestamp format
        desired_format = '%Y-%m-%d %H:%M:%S'

        try:
            # Attempt to parse the timestamp using the desired format
            timestamp = datetime.strptime(timestamp.strftime(desired_format), desired_format)
        except ValueError:
            # If parsing fails, raise a validation error
            raise ValidationError('Invalid timestamp format. Please use the format YYYY-MM-DD HH:MM:SS.')

        return timestamp
