from django.urls import path
from django.contrib import admin
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('register' , register_attempt , name="register_attempt"),
    path('stocks/login/' , login_attempt , name="login_attempt"),
    path('token' , token_send , name="token_send"),
    path('verify/<auth_token>' , verify , name="verify"),
    path('error' , error_page , name="error"),
    path('about/', about, name='about'),
    path('portfolio/', portfolio, name='portfolio'),
    path('deletestock/<stock_symbol>', delete_stock, name='delete_stock'),
    path('getstock',getstock,name = "getstock"),
]
