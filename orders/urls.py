from django.urls import path
from .views import OrderCreateView, CustomerOrderHistoryAPIView, ProductListAPIView, verify_customer

urlpatterns = [
    path('orders/', OrderCreateView.as_view(), name='create-order'),
    path("orders/<str:customer_id>/", CustomerOrderHistoryAPIView.as_view(), name="customer-order-history"),
    path("products/", ProductListAPIView.as_view(), name="product-list"),
    path('customers/<str:customer_id>/', verify_customer, name='verify-customer'),

]

