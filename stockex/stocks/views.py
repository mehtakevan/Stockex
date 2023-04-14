# from stocks.models import Profile
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib import messages
from .models import *
import uuid
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import authenticate,login
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

import requests
import json

import razorpay
from stockex.settings import RAZORPAY_API_KEY,RAZORPAY_API_SECRET_KEY

from .models import Stock
from .forms import StockForm
# Create your views here.

@login_required
def home(request):
    return render(request , 'home.html')


def login_attempt(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user_obj = User.objects.filter(username = username).first()
        if user_obj is None:
            messages.success(request, 'User not found.')
            return redirect('/stocks/login')
        
        
        profile_obj = Profile.objects.filter(user = user_obj ).first()

        if not profile_obj.is_verified:
            messages.success(request, 'Profile is not verified check your mail.')
            return redirect('/stocks/login')

        user = authenticate(username = username , password = password)
        if user is None:
            messages.success(request, 'Wrong password.')
            return redirect('/stocks/login')
        
        login(request , user)
        return redirect('/')

    return render(request , 'login.html')

def register_attempt(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        print(password)

        try:
            if User.objects.filter(username = username).first():
                messages.success(request, 'Username is taken.')
                return redirect('/register')

            if User.objects.filter(email = email).first():
                messages.success(request, 'Email is taken.')
                return redirect('/register')
            
            user_obj = User(username = username , email = email)
            user_obj.set_password(password)
            user_obj.save()
            auth_token = str(uuid.uuid4())
            profile_obj = Profile.objects.create(user = user_obj , auth_token = auth_token)
            profile_obj.save()
            send_mail_after_registration(email , auth_token)
            return redirect('/token')

        except Exception as e:
            print(e)


    return render(request , 'register.html')



def token_send(request):
    return render(request , 'token_send.html')



def verify(request , auth_token):
    try:
        profile_obj = Profile.objects.filter(auth_token = auth_token).first()
    

        if profile_obj:
            if profile_obj.is_verified:
                messages.success(request, 'Your account is already verified.')
                return redirect('/stocks/login')
            profile_obj.is_verified = True
            profile_obj.save()
            messages.success(request, 'Your account has been verified.')
            return redirect('/stocks/login')
        else:
            return redirect('/error')
    except Exception as e:
        print(e)
        return redirect('/')

def error_page(request):
    return  render(request , 'error.html')


def send_mail_after_registration(email , token):
    subject = 'Your accounts need to be verified'
    message = f'Welcome to Stockex,Hope you will earn and have fun investing!!! paste the link to verify your account http://127.0.0.1:8000/verify/{token}'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message , email_from ,recipient_list )

def search_stock(base_url, stock_ticker):
    try:
        token = settings.IEXCLOUD_TEST_API_TOKEN
        url = base_url + stock_ticker + '/quote?token=' + token
        data = requests.get(url)

        if data.status_code == 200:
            data = json.loads(data.content)
        else:
            data = {'Error' : 'There was a problem with your provided ticker symbol. Please try again'}
    except Exception as e:
        data = {'Error':'There has been some connection error. Please try again later.'}
    return data

def search_stock_batch(base_url, stock_tickers):
    data_list = []

    try:
        token = settings.IEXCLOUD_TEST_API_TOKEN
        url = base_url + stock_tickers + '&types=quote&token=' + token
        data = requests.get(url)

        if data.status_code == 200:
            data = json.loads(data.content)
            for item in data:
                data_list.append(data[item]['quote'])
        else:
            data = {'Error' : 'There has been an unexpected issues. Please try again'}
    except Exception as e:
        data = {'Error':'There has been some connection error. Please try again later.'}
    return data_list

def check_valid_stock_ticker(stock_ticker):
    base_url = 'https://cloud.iexapis.com/stable/stock/'
    stock = search_stock(base_url, stock_ticker)
    if 'Error' not in stock:
        return True
    return False


def getstock(request):
    if request.method == 'POST':
        stock_ticker = request.POST['stock_ticker']
        base_url = 'https://cloud.iexapis.com/stable/stock/'
        stocks = search_stock(base_url, stock_ticker)
        return render(request, 'home.html', {'stocks':stocks})
    return render(request, 'home.html')

def check_stock_ticker_existed(stock_ticker):
    try:
        stock = Stock.objects.get(ticker=stock_ticker)
        if stock:
            return True
    except Exception:
        return False

def about(request):
    return render(request, 'about.html')

def portfolio(request):
    if request.method == 'POST':
        ticker = request.POST['ticker']
        if ticker:
            form = StockForm(request.POST or None)

            if form.is_valid():
                if check_stock_ticker_existed(ticker):
                    messages.warning(request, f'{ticker} is already existed in Portfolio.')
                    return redirect('portfolio')

                if check_valid_stock_ticker(ticker):
                    #add stock                    
                    form.save()
                    messages.success(request, f'{ticker} has been added successfully.')
                    return redirect('portfolio')

        messages.warning(request, 'Please enter a valid ticker name.')
        return redirect('portfolio')
    else:
        stockdata = Stock.objects.all()
        if stockdata:
            ticker_list = [stock.ticker for stock in stockdata]
            ticker_list = list(set(ticker_list))
            
            tickers = ','.join(ticker_list)
            base_url = 'https://cloud.iexapis.com/stable/stock/market/batch?symbols='
            stockdata = search_stock_batch(base_url, tickers)
        else:
            messages.info(request, 'Currently, there are no stocks in your portfolio!')
        return render(request, 'portfolio.html', {'stockdata':stockdata})

def delete_stock(request, stock_symbol):
    stock = Stock.objects.get(ticker=stock_symbol)
    stock.delete()

    messages.success(request, f'{stock.ticker} has been deleted successfully.')
    return redirect('portfolio')

@csrf_exempt
def fund(request):
    return render(request,'fund.html')

client = razorpay.Client(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET_KEY))
@csrf_exempt
def add_funds(request):
    order_amount = request.POST.get('funds')
    order_currency = 'INR'
    data = { "amount": (order_amount), "currency": order_currency, "payment_capture":1}
    payment = client.order.create(data=data)
    payment_order_id = payment['id']
    context = {
        'amount' : order_amount, 'api_key' : RAZORPAY_API_KEY,'order_id' : payment_order_id,
    }
    return render(request,'pay.html',context)


@csrf_exempt
def success_funds(request):
    payment_id = request.POST.get('razorpay_payment_id')
    order_id = request.POST.get('razorpay_order_id')
    signature = request.POST.get('razorpay_signature')

    user_obj = request.user

    fund_obj = funds.objects.create(user=user_obj,fund=100,payment_id=payment_id,order_id=order_id,signature=signature)
    fund_obj.save()
    return render(request,'base2.html')

def buy_sell(request):
    return render(request,'buy_sell.html')


def searchstock(request):
    ticker = request.POST.get('ticker')
    if check_valid_stock_ticker(ticker):
        request.session['ticker'] = ticker
        base_url = 'https://cloud.iexapis.com/stable/stock/'
        stock = search_stock(base_url, ticker)
        return render(request,'stock.html',{'stocks':stock})
    else:
        messages.warning(request, 'Please enter a valid ticker name.')
        return render(request,'error.html')
    
    
def buy_sell_stock(request):
    act = request.POST.get('action')
    ticker = request.session['ticker']
    to_add = request.POST.get('quantity')
    user_obj = request.user
    if(act == 'Buy'):
        try:
            stock = Portfolio.objects.get(user=user_obj,ticker=ticker)
            print(stock)
            if stock:
                print(stock.quantity)
                qnt = stock.quantity
                qnt = qnt+int(to_add)
                Portfolio.objects.update(quantity = qnt)
                return redirect('portfolio2')
            else:
                portfolio_obj = Portfolio.objects.create(user=user_obj,ticker = ticker,quantity = to_add)
                portfolio_obj.save()
                return redirect('portfolio2')
        except Exception as e:
            print(e)
            portfolio_obj = Portfolio.objects.create(user=user_obj,ticker = ticker,quantity = to_add)
            portfolio_obj.save()
            return redirect('portfolio2')
    else:
        try:
            stock = Portfolio.objects.get(user=user_obj,ticker=ticker)
            print(stock)
            if stock:
                print(stock.quantity)
                qnt = stock.quantity
                if(qnt >= int(to_add)):
                    qnt = qnt - int(to_add)
                    Portfolio.objects.update(quantity = qnt)    
                    return redirect('portfolio2')
            else:
                # portfolio_obj = Portfolio.objects.create(user=user_obj,ticker = ticker,quantity = to_add)
                # portfolio_obj.save()
                return redirect(request,'error.html')
        except Exception as e:
            print(e)
            # portfolio_obj = Portfolio.objects.create(user=user_obj,ticker = ticker,quantity = to_add)
            # portfolio_obj.save()
            return redirect(request,'error.html')
        
def portfolio2(request):
    user_obj = request.user
    stock1 = Portfolio.objects.get(user=user_obj)
    ticker = request.session['ticker']
    base_url = 'https://cloud.iexapis.com/stable/stock/market/batch?symbols='
    stockdata = search_stock_batch(base_url, ticker)
    print(stock1)
    # stockdata.append({'quantity':stock1.quantity})
    print(stockdata)
    print(type(stockdata))
    return render(request,'successful.html',{'stockdata':stockdata,'stock1':stock1})

