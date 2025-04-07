from django.db import models

# Create your models here.

class Customer(models.Model):
    customer_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.customer_id


class Product(models.Model):
  
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.name


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.customer_id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"