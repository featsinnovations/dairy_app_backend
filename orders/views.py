from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Customer, Product, Order, OrderItem
from .serializers import OrderSerializer, ProductSerializer, CustomerSerializer, CustomerMonthlyTotalSerializer
from .models import Order, Product, Customer
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.utils import timezone
from .models import Customer, Order
from datetime import datetime, timedelta
from pytz import timezone as pytz_timezone
from dateutil.relativedelta import relativedelta
from calendar import monthrange





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


@extend_schema(
    responses={200: CustomerMonthlyTotalSerializer(many=True)} 
)
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

@api_view(["POST"])
def mark_order_paid(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        order.is_paid = True
        order.paid_at = timezone.now()
        order.save()
        return Response({"message": "Order marked as paid."})
    except Order.DoesNotExist:
        return Response({"error": "Order not found."}, status=404)
    
@api_view(['GET'])
def customer_total_due(request, id):
    customer = get_object_or_404(Customer, id=id)
    unpaid_orders = Order.objects.filter(customer=customer, is_paid=False)

    total_due = sum(order.total_amount() for order in unpaid_orders)

    return Response({
        "customer_id": customer.id,
        "customer_name": customer.name,
        "total_due": float(total_due)
    })

@api_view(['GET'])
def monthly_payment_status(request, customer_id):
    month = int(request.query_params.get('month'))
    year = int(request.query_params.get('year'))

    start_date = datetime(year, month, 1, tzinfo=timezone.get_current_timezone())
    end_date = (start_date + relativedelta(months=1))

    customer = get_object_or_404(Customer, id=customer_id)
    orders = Order.objects.filter(
        customer=customer,
        date__gte=start_date,
        date__lt=end_date
    )

    paid_orders = orders.filter(is_paid=True)
    unpaid_orders = orders.filter(is_paid=False)

    paid_total = sum(order.total_amount() for order in paid_orders)
    unpaid_total = sum(order.total_amount() for order in unpaid_orders)

    return Response({
        "customer_id": customer.id,
        "customer_name": customer.name,
        "month": month,
        "year": year,
        "paid_total": float(paid_total),
        "unpaid_total": float(unpaid_total),
        "orders": [
            {
                "order_id": order.id,
                "date": order.date.strftime("%Y-%m-%d"),
                "is_paid": order.is_paid,
                "total_amount": float(order.total_amount())
            }
            for order in orders
        ]
    })

@api_view(["POST"])
def mark_month_orders_paid(request, customer_id):
    month = int(request.query_params.get('month'))
    year = int(request.query_params.get('year'))

    start_date = datetime(year, month, 1, tzinfo=timezone.get_current_timezone())
    end_date = (start_date + relativedelta(months=1))

    customer = get_object_or_404(Customer, id=customer_id)

    orders = Order.objects.filter(
        customer=customer,
        date__gte=start_date,
        date__lt=end_date,
        is_paid=False  # only unpaid
    )

    updated_count = 0
    now = timezone.now()

    for order in orders:
        order.is_paid = True
        order.paid_at = now
        order.save()
        updated_count += 1

    return Response({
        "message": f"{updated_count} order(s) marked as paid for {month}/{year}."
    }, status=200)


class OrderCreateView(APIView):
    serializer_class = OrderSerializer
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
        # Get month and year from query params
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        india_timezone = pytz_timezone("Asia/Kolkata")
        now = timezone.now().astimezone(india_timezone)
        
        if year and month:
            # Use specified year and month
            try:
                target_date = india_timezone.localize(
                    datetime(int(year), int(month), 1)
                )
            except ValueError:
                return Response({"error": "Invalid month/year parameters"}, status=400)
        else:
            # Default to current month if no parameters provided
            target_date = now.replace(day=1)
        
        # Calculate date range for the whole month
        date_start = target_date.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        date_end = date_start + relativedelta(months=1)
        
        # Get the customer
        customer = get_object_or_404(Customer, id=id)
        
        # Filter orders
        orders = Order.objects.filter(
            customer=customer,
            date__gte=date_start,
            date__lt=date_end
        ).order_by('-date', '-id')
        
        is_month_paid = not orders.filter(is_paid=False).exists()
        # Calculate total amount
        total_amount = OrderItem.objects.filter(
            order__in=orders
        ).aggregate(total_amount=Sum(F('quantity') * F('product__price')))['total_amount'] or 0
        


        # Prepare response
        result = {
            "customer_id": customer.id,
            "customer_name": customer.name,
            "month_year": date_start.strftime("%B %Y"),  # e.g. "April 2023"
            "total_amount": float(total_amount),
            "is_month_paid": is_month_paid,
            "orders": []
        }

        for order in orders:
            items = order.items.select_related('product')
            item_list = []
            order_total = 0

            for item in items:
                price = item.product.price
                quantity = item.quantity
                item_total = price * quantity
                order_total += item_total

                item_list.append({
                    "product": item.product.name,
                    "quantity": quantity,
                    "price": float(price),
                    "total": float(item_total)
                })

            order_time_ist = order.date.astimezone(india_timezone)
            
            result["orders"].append({
                "order_id": order.id,
                "date": order_time_ist.strftime('%Y-%m-%d %I:%M:%S %p'),
                "total_amount": float(order_total),
                "items": item_list,
                "paid": order.is_paid,
                "paid_at": order.paid_at.strftime('%Y-%m-%d %I:%M:%S %p') if order.paid_at else None,
            })

        return Response(result, status=200)
    

@api_view(['GET'])
def monthly_payment_summary(request):
    """
    Returns a list of customers with total paid and due amounts for the specified month and year.
    """
    month = int(request.query_params.get('month'))
    year = int(request.query_params.get('year'))

    start_date = datetime(year, month, 1, tzinfo=timezone.get_current_timezone())
    end_date = start_date + relativedelta(months=1)

    customers = Customer.objects.all()
    data = []

    for customer in customers:
        orders = Order.objects.filter(
            customer=customer,
            date__gte=start_date,
            date__lt=end_date
        )

        paid_total = sum(order.total_amount() for order in orders if order.is_paid)
        unpaid_total = sum(order.total_amount() for order in orders if not order.is_paid)

        if paid_total > 0 or unpaid_total > 0:
            data.append({
                "customer_id": customer.id,
                "customer_name": customer.name,
                "paid_amount": float(paid_total),
                "due_amount": float(unpaid_total)
            })

    return Response(data)

class ProductListAPIView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
