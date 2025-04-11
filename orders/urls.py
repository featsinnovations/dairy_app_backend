from django.urls import path
from .views import OrderCreateView, CustomerOrderHistoryAPIView, ProductListAPIView, verify_customer, customer_monthly_totals, mark_order_paid, customer_total_due, monthly_payment_status, mark_month_orders_paid, monthly_payment_summary

urlpatterns = [
    path('orders/', OrderCreateView.as_view(), name='create-order'),
    path('orders/<int:order_id>/pay/', mark_order_paid, name='mark-order-paid'),
    path("customer/<int:id>/orders/", CustomerOrderHistoryAPIView.as_view(), name="customer-order-history"),
    path("products/", ProductListAPIView.as_view(), name="product-list"),
    path('customers/verify/<int:id>/', verify_customer, name='verify-customer'),
    path('customers/monthly-totals/', customer_monthly_totals, name='customer_monthly_totals'),
    path('customers/<int:id>/total-due/', customer_total_due, name='customer-total-due'),
    path('customer/<int:customer_id>/monthly-status/', monthly_payment_status, name='monthly-payment-status'),
    path('customer/<int:customer_id>/mark-paid/', mark_month_orders_paid, name='mark-month-orders-paid'),
    path('payment-summary/',monthly_payment_summary, name='monthly-payment-summary'),
]

