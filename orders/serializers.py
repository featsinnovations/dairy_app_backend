from rest_framework import serializers
from .models import Customer, Product, Order, OrderItem

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['customer_id', 'name']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price']
        
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

    class Meta:
        model = Order
        fields = ['id', 'customer', 'date', 'items', 'total_amount']

    def get_total_amount(self, obj):
        return sum(item.product.price * item.quantity for item in obj.items.all())

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            OrderItem.objects.create(order=order, product=product, quantity=quantity)
        return order

