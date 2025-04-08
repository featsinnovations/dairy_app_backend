from django.urls import path
from .views import OrderCreateView, CustomerOrderHistoryAPIView, ProductListAPIView, verify_customer, customer_monthly_totals

urlpatterns = [
    path('orders/', OrderCreateView.as_view(), name='create-order'),
    path("orders/<str:id>/", CustomerOrderHistoryAPIView.as_view(), name="customer-order-history"),
    path("products/", ProductListAPIView.as_view(), name="product-list"),
    path('customers/verify/<int:id>/', verify_customer, name='verify-customer'),
    path('customers/monthly-totals/', customer_monthly_totals, name='customer_monthly_totals'),
]

