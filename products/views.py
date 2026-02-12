from django.shortcuts import render, redirect, get_object_or_404
from .models import Products
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
import qrcode
import io
import base64


# ---------------------------
# PRODUCTS
# ---------------------------

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
    product = get_object_or_404(Products, id=id)
    return render(request, 'product_details.html', {'product': product})


def add_product(request):
    if not request.user.is_authenticated:
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


# ---------------------------
# CART
# ---------------------------

def add_to_cart(request, id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'auth_required'}, status=401)

    product = get_object_or_404(Products, id=id)
    cart = request.session.get('cart', {})

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
    if not request.user.is_authenticated:
        return redirect('login')

    cart = request.session.get('cart', {})
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
    if not request.user.is_authenticated:
        return redirect('login')

    cart = request.session.get('cart', {})
    product_id = str(id)

    if product_id in cart:
        del cart[product_id]
        request.session['cart'] = cart
        request.session.modified = True

    return JsonResponse({
        'status': 'success',
        'cart_count': sum(cart.values())
    })


def increase_quantity(request, id):
    if not request.user.is_authenticated:
        return redirect('login')

    cart = request.session.get('cart', {})
    product_id = str(id)

    cart[product_id] = cart.get(product_id, 0) + 1

    request.session['cart'] = cart
    request.session.modified = True

    return JsonResponse({'status': 'success'})


def decrease_quantity(request, id):
    if not request.user.is_authenticated:
        return redirect('login')

    cart = request.session.get('cart', {})
    product_id = str(id)

    if product_id in cart:
        cart[product_id] -= 1
        if cart[product_id] <= 0:
            del cart[product_id]

    request.session['cart'] = cart
    request.session.modified = True

    return JsonResponse({'status': 'success'})


# ---------------------------
# AUTHENTICATION (SECURE)
# ---------------------------

def register(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            return HttpResponse("Passwords do not match")

        if User.objects.filter(username=username).exists():
            return HttpResponse("Username already exists")

        User.objects.create_user(
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

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)

            # Optional session values (if you still want them)
            request.session['user_id'] = user.id
            request.session['username'] = user.username
            request.session['email'] = user.email

            return redirect('home')
        else:
            return HttpResponse("Invalid username or password")

    return render(request, 'login.html')


def logout(request):
    username = request.user.username if request.user.is_authenticated else None
    auth_logout(request)

    if username:
        messages.success(request, f"Logged out: {username}")

    return redirect('home')


# ---------------------------
# CHECKOUT & PAYMENT
# ---------------------------

def checkout(request):
    if not request.user.is_authenticated:
        return redirect('login')

    cart = request.session.get('cart', {})
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

    if request.method == "POST":
        payment_method = request.POST.get("payment")
        request.session["payment_amount"] = total_price

        if payment_method == "upi":
            return redirect("upi_payment")
        elif payment_method == "card":
            return redirect("card_payment")
        elif payment_method == "cod":
            request.session['cart'] = {}
            return redirect("cod_success")

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })


def upi_payment(request):
    amount = request.session.get("payment_amount")
    if not amount:
        return redirect("checkout")

    upi_id = "iamabjunior-3@okhdfcbank"
    payee_name = "Game Of Codes"
    note = "Order Payment"

    upi_url = (
        f"upi://pay?pa={upi_id}&pn={payee_name}&am={amount}&cu=INR&tn={note}"
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
    if request.method == "POST":
        request.session['cart'] = {}
        return redirect("payment_success")

    return render(request, "card_payment.html")


def cod_success(request):
    return render(request, "cod_success.html")


def payment_success(request):
    return render(request, "payment_success.html")
