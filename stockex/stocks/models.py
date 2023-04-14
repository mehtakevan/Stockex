from django.db import models
from django.db import models
from django.contrib.auth.models import User

class Stock(models.Model):
    ticker = models.CharField(max_length=10)

    def clean(self):
        self.ticker = self.ticker.upper()

    def __str__(self):
        return self.ticker

class Profile(models.Model):
    user = models.OneToOneField(User , on_delete=models.CASCADE)
    auth_token = models.CharField(max_length=100 )
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

class funds(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    fund = models.BigIntegerField(max_length=20)
    payment_id = models.CharField(max_length=100)
    order_id = models.CharField(max_length=100)
    signature = models.CharField(max_length=100)

class Portfolio(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,null=True)
    ticker = models.CharField(max_length=100)
    quantity = models.IntegerField(max_length=10)

    def clean(self):
        self.ticker = self.ticker.upper()
    
    def __str__(self):
        return self.ticker


