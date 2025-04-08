# orders/admin_forms.py
from django import forms

class CsvImportForm(forms.Form):
    csv_file = forms.FileField()
