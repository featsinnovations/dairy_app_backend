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
from django.utils import timezone
from .models import Customer, Order
from datetime import datetime
from pytz import timezone






@extend_schema(
    responses={200: CustomerSerializer, 404: None}
)
@api_view(['GET'])
def verify_customer(request, id):
    """
    Check if a customer exists by ID.
    """
    print("Received id:", id)
    try:
        customer = Customer.objects.get(id=id)
        serializer = CustomerSerializer(customer)
        # total_amount = customer.order_set.annotate(order_total=Sum(ExpressionWrapper(F('items__quantity') * F('items__product__price'), output_field=DecimalField()))).aggregate(total=Sum('order_total'))['total'] or 0
        data = serializer.data
        # data['total_order_amount'] = float(total_amount)
        return Response(data, status=status.HTTP_200_OK)
    except Customer.DoesNotExist:
        return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
def customer_monthly_totals(request):
    now = timezone.now()

    # Step 1: Get totals only for customers who placed orders this month
    totals = OrderItem.objects.filter(
        order__date__year=now.year,
        order__date__month=now.month
    ).values(
        "order__customer__id"
    ).annotate(
        total_amount=Sum(
            ExpressionWrapper(
                F("quantity") * F("product__price"),
                output_field=DecimalField()
            )
        )
    )

    # Step 2: Map customer ID to total for quick lookup
    totals_map = {item["order__customer__id"]: item["total_amount"] for item in totals}

    # Step 3: Include all customers, even if not in totals
    customer_data = []
    for customer in Customer.objects.all():
        total = totals_map.get(customer.id, 0)
        customer_data.append({
            "id": customer.id,
            "name": customer.name,
            "total_amount": float(total)
        })

    return Response(customer_data)


class OrderCreateView(APIView):
    def post(self, request):
        id = request.data.get('id')
        try:
            customer, created = Customer.objects.get_or_create(id=id)
        except:
            return Response({"error": "Invalid customer"}, status=400)

        serializer = OrderSerializer(data={**request.data, "customer": customer.id})
        if serializer.is_valid():
            order = serializer.save()
            return Response(OrderSerializer(order).data, status=201)
        return Response(serializer.errors, status=400)

class CustomerOrderHistoryAPIView(APIView):
    def get(self, request, id):
        today = datetime.today()
        first_day = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        customer = get_object_or_404(Customer, id=id)
        orders = Order.objects.filter(customer=customer,date__gte=first_day,date__lt=next_month).order_by('-date', '-id')

        result = {
            "id": customer.id,
            "customer_name": customer.name,
            "orders": []
        }

        for order in orders:
            items = OrderItem.objects.filter(order=order).select_related('product')
            item_list = []
            total_amount = 0

            for item in items:
                price = item.product.price
                quantity = item.quantity
                total = price * quantity
                total_amount += total

                item_list.append({
                    "product": item.product.name,
                    "quantity": quantity,
                    "price": float(price),
                })
                ist = timezone("Asia/Kolkata")
                order_time_ist = order.date.astimezone(ist)
                formatted_date = order_time_ist.strftime('%Y-%m-%d %I:%M:%S %p')

            result["orders"].append({
                "order_id": order.id,
                "date": formatted_date,
                "total_amount": float(total_amount),
                "items": item_list
            })

        return Response(result, status=status.HTTP_200_OK)

class ProductListAPIView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
