from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Customer, Product, Order, OrderItem
from .serializers import OrderSerializer, ProductSerializer, CustomerSerializer
from .models import Order, Product, Customer
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema
from django.db.models import Sum, F, DecimalField, ExpressionWrapper



@extend_schema(
    responses={200: CustomerSerializer, 404: None}
)
@api_view(['GET'])
def verify_customer(request, customer_id):
    """
    Check if a customer exists by ID.
    """
    try:
        customer = Customer.objects.get(customer_id=customer_id)
        serializer = CustomerSerializer(customer)
        total_amount = customer.order_set.annotate(order_total=Sum(ExpressionWrapper(F('items__quantity') * F('items__product__price'), output_field=DecimalField()))).aggregate(total=Sum('order_total'))['total'] or 0
        data = serializer.data
        data['total_order_amount'] = float(total_amount)
        print("data",data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Customer.DoesNotExist:
        return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)


class OrderCreateView(APIView):
    def post(self, request):
        customer_id = request.data.get('customer_id')
        try:
            customer, created = Customer.objects.get_or_create(customer_id=customer_id)
        except:
            return Response({"error": "Invalid customer"}, status=400)

        serializer = OrderSerializer(data={**request.data, "customer": customer.id})
        if serializer.is_valid():
            order = serializer.save()
            return Response(OrderSerializer(order).data, status=201)
        return Response(serializer.errors, status=400)

class CustomerOrderHistoryAPIView(APIView):
    def get(self, request, customer_id):
        customer = get_object_or_404(Customer, customer_id=customer_id)
        orders = Order.objects.filter(customer=customer).order_by('-date')

        result = {
            "customer_id": customer.customer_id,
            "customer_name": customer.name,
            "orders": []
        }

        for order in orders:
            items = OrderItem.objects.filter(order=order)
            item_list = [
                {
                    "product": item.product.name,
                    "quantity": item.quantity
                } for item in items
            ]
            result["orders"].append({
                "date": order.date.strftime('%Y-%m-%d'),
                "items": item_list
            })

        return Response(result, status=status.HTTP_200_OK)

class ProductListAPIView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
