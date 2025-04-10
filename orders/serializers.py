from rest_framework import serializers
from .models import Customer, Product, Order, OrderItem
from django.utils import timezone
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from datetime import datetime
from drf_spectacular.utils import extend_schema_field



class CustomerMonthlyTotalSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    total_amount = serializers.FloatField()


class CustomerSerializer(serializers.ModelSerializer):
    total_amount = serializers.SerializerMethodField()

    @extend_schema_field(serializers.FloatField())

    def get_total_amount(self, obj) -> float:
        today = datetime.today()
        first_day = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)

        items = OrderItem.objects.filter(
            order__customer=obj,
            order__date__gte=first_day,
            order__date__lt=next_month
        ).select_related("product")

        return sum(item.quantity * item.product.price for item in items)

    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone_number','total_amount']
    

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        image_path = serializers.ImageField(use_url=True)
        fields = ['id', 'name', 'nickname', 'price', 'image_path', 'quentity']
        
class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )

    class Meta:
        model = OrderItem
        fields = ['product', 'product_id', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    total_amount = serializers.SerializerMethodField()
    @extend_schema_field(serializers.FloatField())
    class Meta:
        model = Order
        fields = ['id', 'customer', 'date', 'items', 'total_amount']

    def get_total_amount(self, obj) -> float:
        return sum(item.product.price * item.quantity for item in obj.items.all())

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            OrderItem.objects.create(order=order, product=product, quantity=quantity)
        return order

