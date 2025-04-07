# orders/admin.py
from django.contrib import admin
from .models import Customer, Product, Order, OrderItem

# Register each model
admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
