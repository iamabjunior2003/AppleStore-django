from django.db import models
from django.contrib.auth.models import User

class Products(models.Model):

    CAT = (
        (1, 'Iphone'),
        (2, 'Macbook'),
        (3, 'Ipad'),
        (4, 'Watch'),
        (5, 'AirPods'),
        (6, 'TV & Home'),
        (7, 'Entertainment')
    )

    product_name = models.CharField(max_length=100)
    product_price = models.FloatField()
    product_category = models.IntegerField(choices=CAT, default=1)
    product_description = models.TextField()
    is_available = models.BooleanField(default=True)
    product_image = models.ImageField(upload_to='images/')

    @property
    def original_price(self):
        return self.product_price + (self.product_price * 0.46)

    def __str__(self):
        return self.product_name


class Address(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    state = models.CharField(max_length=100)
    mobile = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.fullname} - {self.city}"



class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    address = models.ForeignKey("Address", on_delete=models.SET_NULL, null=True)
    ordered_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.FloatField()
    status = models.CharField(max_length=20, default="Pending")

    def __str__(self):
        return f"Order {self.order_id}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.FloatField()

    def __str__(self):
        return self.product.product_name

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Cart"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.product.product_name} ({self.quantity})"