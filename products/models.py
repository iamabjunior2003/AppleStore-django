from django.db import models


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
