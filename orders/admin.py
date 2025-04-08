# orders/admin.py
from django.contrib import admin
from .models import Customer, Product, Order, OrderItem
from django.shortcuts import render, redirect
from django.urls import path


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'phone_number')

    change_list_template = "admin/customer_changelist.html"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path("upload-csv/", self.upload_csv),
        ]
        return custom_urls + urls

    def upload_csv(self, request):
        from .admin_forms import CsvImportForm
        import csv

        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data["csv_file"]
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)

                for row in reader:
                    name = row.get("name", "").strip()
                    if not name:
                        continue  # skip rows without a name

                    Customer.objects.create(
                        name=name,
                        id=row.get("id") or None,
                        phone_number=row.get("phone_number") or None,
                        address=row.get("address") or None,
                    )

                self.message_user(request, "CSV upload successful!")
                return redirect("..")
        else:
            form = CsvImportForm()

        context = {"form": form}
        return render(request, "admin/csv_form.html", context)


# Register each model
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)

# admin.py
