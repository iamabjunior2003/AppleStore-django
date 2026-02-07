from django.shortcuts import render,redirect,get_object_or_404
from .models import Products,Users
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.contrib import messages
import qrcode
import io
import base64

def display_products(request):
    data = Products.objects.all()

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort = request.GET.get('sort')

    if min_price:
        data = data.filter(product_price__gte=min_price)
    if max_price:
        data = data.filter(product_price__lte=max_price)

    if sort == "price_asc":
        data = data.order_by('product_price')
    elif sort == "price_desc":
        data = data.order_by('-product_price')

    return render(request, 'Home.html', {
        'data': data,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort
    })



def product_detail(request, id):
    product = Products.objects.get(id=id)
    return render(request, 'product_details.html', {'product': product})

def add_product(request):
    if not request.session.get('user_id'):
        return redirect('login')

    if request.method == "POST":
        Products.objects.create(
            product_name=request.POST['product_name'],
            product_price=request.POST['product_price'],
            product_category=request.POST['product_category'],
            product_description=request.POST['product_description'],
            is_available='is_available' in request.POST,
            product_image=request.FILES['product_image']
        )
        return redirect('home')

    return render(request, 'add_product.html')



def filter_products(request, category_id):
    data = Products.objects.filter(product_category=category_id)

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort = request.GET.get('sort')

    if min_price:
        data = data.filter(product_price__gte=min_price)
    if max_price:
        data = data.filter(product_price__lte=max_price)

    if sort == "price_asc":
        data = data.order_by('product_price')
    elif sort == "price_desc":
        data = data.order_by('-product_price')

    return render(request, 'filter_products.html', {
        'data': data,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort
    })

def add_to_cart(request, id):
    if not request.session.get('user_id'):
        return JsonResponse({'status': 'auth_required'}, status=401)

    product = get_object_or_404(Products, id=id)
    cart = request.session.get('cart', {})

    if not isinstance(cart, dict):
        cart = {}

    pid = str(id)
    cart[pid] = cart.get(pid, 0) + 1

    request.session['cart'] = cart
    request.session.modified = True

    return JsonResponse({
        'status': 'success',
        'product_name': product.product_name,
        'cart_count': sum(cart.values())
    })

def cart_view(request):
    if not request.session.get('user_id'):
        return redirect('login')
    cart = request.session.get('cart')

    if not isinstance(cart, dict):
        cart = {}

    cart_items = []
    total_price = 0

    for product_id, quantity in cart.items():
        product = get_object_or_404(Products, id=int(product_id))
        subtotal = product.product_price * quantity
        total_price += subtotal

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal
        })

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })


def remove_from_cart(request, id):
    if not request.session.get('user_id'):
        return redirect('login')
    cart = request.session.get('cart', {})

    product_id = str(id)

    if isinstance(cart, dict) and product_id in cart:
        del cart[product_id]
        request.session['cart'] = cart
        request.session.modified = True

    return JsonResponse({
        'status': 'success',
        'cart_count': sum(cart.values()) if isinstance(cart, dict) else 0
    })


def increase_quantity(request, id):
    if not request.session.get('user_id'):
        return redirect('login')
    
    cart = request.session.get('cart', {})
    product_id = str(id)

    if isinstance(cart, dict):
        cart[product_id] = cart.get(product_id, 0) + 1
        request.session['cart'] = cart
        request.session.modified = True

    return JsonResponse({
        'status': 'success'
    })


def decrease_quantity(request, id):
    if not request.session.get('user_id'):
        return redirect('login')
    
    cart = request.session.get('cart', {})
    product_id = str(id)

    if isinstance(cart, dict) and product_id in cart:
        cart[product_id] -= 1

        if cart[product_id] <= 0:
            del cart[product_id]

        request.session['cart'] = cart
        request.session.modified = True

    return JsonResponse({
        'status': 'success'
    })


def register(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            return HttpResponse("Passwords do not match")

        if Users.objects.filter(username=username).exists():
            return HttpResponse("Username already exists")

        Users.objects.create(
            username=username,
            email=email,
            password=password   
        )

        return redirect('login')

    return render(request, 'register.html')


def login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']


        try:
            user = Users.objects.get(username=username, password=password)

            # ✅ store login state
            request.session['user_id'] = user.id
            request.session['username'] = user.username
            request.session['email'] = user.email

            return redirect('home')

        except Users.DoesNotExist:
            return HttpResponse("Invalid username or password")

    return render(request, 'login.html')

def logout(request):
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    email = request.session.get('email')

    # Optional flash (for testing / dev)
    if username:
        messages.success(request, f"Logged out: {username}")


    request.session.pop('user_id', None)
    request.session.pop('username', None)
    request.session.pop('email', None)

    request.session.modified = True

    return redirect('home')

from django.shortcuts import render, redirect, get_object_or_404
from .models import Products

def checkout(request):
    # Require login
    if not request.session.get('user_id'):
        return redirect('login')

    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    # Calculate cart total
    for product_id, quantity in cart.items():
        product = get_object_or_404(Products, id=int(product_id))
        subtotal = product.product_price * quantity
        total_price += subtotal

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal
        })

    # Handle payment selection
    if request.method == "POST":
        payment_method = request.POST.get("payment")

        # Store total for payment pages
        request.session["payment_amount"] = total_price

        if payment_method == "upi":
            return redirect("upi_payment")

        elif payment_method == "card":
            return redirect("card_payment")

        elif payment_method == "cod":
            # COD → Order confirmed
            request.session['cart'] = {}
            return redirect("cod_success")

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })


def upi_payment(request):
    """
    Generate UPI QR dynamically for cart amount
    """

    amount = request.session.get("payment_amount")
    if not amount:
        return redirect("checkout")

    upi_id = "iamabjunior-3@okhdfcbank"
    payee_name = "Game Of Codes"
    note = "Order Payment"

    upi_url = (
        f"upi://pay?"
        f"pa={upi_id}&"
        f"pn={payee_name}&"
        f"am={amount}&"
        f"cu=INR&"
        f"tn={note}"
    )

    qr = qrcode.make(upi_url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")

    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, "upi_payment.html", {
        "qr_code": qr_base64,
        "amount": amount,
        "upi_id": upi_id
    })


def card_payment(request):
    """
    Card payment UI (no gateway yet)
    """

    if request.method == "POST":
        # later integrate Razorpay / Stripe
        return redirect("payment_success")

    return render(request, "card_payment.html")


def cod_success(request):
    """
    Cash on Delivery success page
    """
    return render(request, "cod_success.html")


def payment_success(request):
    """
    Common success page
    """
    return render(request, "payment_success.html")
