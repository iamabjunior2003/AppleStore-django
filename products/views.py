import re
from django.shortcuts import render, redirect, get_object_or_404
from .models import Products, Address, Order, OrderItem, Cart, CartItem
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

    return render(request, 'home.html', {
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
# CART (DATABASE VERSION)
# ---------------------------

def add_to_cart(request, id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'auth_required'}, status=401)

    product = get_object_or_404(Products, id=id)

    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return JsonResponse({
        'status': 'success',
        'product_name': product.product_name
    })


def cart_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    cart = Cart.objects.filter(user=request.user).first()
    cart_items = []
    total_price = 0

    if cart:
        items = CartItem.objects.filter(cart=cart)

        for item in items:
            subtotal = item.product.product_price * item.quantity
            total_price += subtotal

            cart_items.append({
                'product': item.product,
                'quantity': item.quantity,
                'subtotal': subtotal
            })

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })


def remove_from_cart(request, id):
    if not request.user.is_authenticated:
        return redirect('login')

    cart = Cart.objects.filter(user=request.user).first()
    if cart:
        CartItem.objects.filter(cart=cart, product_id=id).delete()

    return JsonResponse({'status': 'success'})


def increase_quantity(request, id):
    if not request.user.is_authenticated:
        return redirect('login')

    cart = Cart.objects.get(user=request.user)
    item = CartItem.objects.get(cart=cart, product_id=id)

    item.quantity += 1
    item.save()

    return JsonResponse({'status': 'success'})


def decrease_quantity(request, id):
    if not request.user.is_authenticated:
        return redirect('login')

    cart = Cart.objects.get(user=request.user)
    item = CartItem.objects.get(cart=cart, product_id=id)

    item.quantity -= 1

    if item.quantity <= 0:
        item.delete()
    else:
        item.save()

    return JsonResponse({'status': 'success'})


# ---------------------------
# AUTHENTICATION
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

            # ✅ SESSION VALID 1 DAY
            request.session.set_expiry(86400)

            request.session['user_id'] = user.id
            request.session['username'] = user.username
            request.session['email'] = user.email

            return redirect('home')
        else:
            return HttpResponse("Invalid username or password")

    return render(request, 'login.html')


def logout(request):
    auth_logout(request)
    return redirect('home')


# ---------------------------
# CHECKOUT & PAYMENT
# ---------------------------
def checkout(request):
    if not request.user.is_authenticated:
        return redirect('login')

    cart = Cart.objects.filter(user=request.user).first()
    addresses = Address.objects.filter(user_id=request.user)

    cart_items = []
    total_price = 0

    if cart:
        items = CartItem.objects.filter(cart=cart)
        for item in items:
            subtotal = item.product.product_price * item.quantity
            total_price += subtotal

            cart_items.append({
                'product': item.product,
                'quantity': item.quantity,
                'subtotal': subtotal
            })

    if request.method == "POST":

        selected_address_id = request.POST.get("selected_address")

        # 🟢 CASE 1: User selected existing address
        if selected_address_id:
            selected_address = get_object_or_404(
                Address,
                id=selected_address_id,
                user_id=request.user
            )

        # 🟢 CASE 2: User added new address
        else:
            fullname = request.POST.get("fullname")
            address_text = request.POST.get("address")
            city = request.POST.get("city")
            pincode = request.POST.get("pincode")
            state = request.POST.get("state", "")
            mobile = request.POST.get("mobile")

            if not fullname or not address_text:
                messages.error(request, "Please select or add an address.")
                return redirect("checkout")

            if not re.match(r'^\d{10}$', mobile):
                messages.error(request, "Invalid Mobile Number")
                return redirect("checkout")

            selected_address = Address.objects.create(
                user_id=request.user,
                fullname=fullname,
                address=address_text,
                city=city,
                pincode=pincode,
                state=state,
                mobile=mobile
            )

        # ✅ CREATE ORDER
        order = Order.objects.create(
            user_id=request.user,
            address=selected_address,
            total_amount=total_price,
            status="Pending"
        )

        # ✅ CREATE ORDER ITEMS
        items = CartItem.objects.filter(cart=cart)
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.product_price
            )

        # ✅ CLEAR CART
        cart.delete()

        payment_method = request.POST.get("payment")

        if payment_method == "upi":
            return redirect("upi_payment")
        elif payment_method == "card":
            return redirect("card_payment")
        elif payment_method == "cod":
            return redirect("cod_success")

    return render(request, "checkout.html", {
        "cart_items": cart_items,
        "total_price": total_price,
        "addresses": addresses
    })

def card_payment(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == "POST":
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart.delete()
        return redirect("payment_success")

    return render(request, "card_payment.html")


def upi_payment(request):
    if not request.user.is_authenticated:
        return redirect('login')

    amount = request.session.get("payment_amount")
    if not amount:
        return redirect("checkout")

    upi_id = "iamabjunior-3@okhdfcbank"
    payee_name = "Game Of Codes"
    note = "Order Payment"

    upi_url = f"upi://pay?pa={upi_id}&pn={payee_name}&am={amount}&cu=INR&tn={note}"

    qr = qrcode.make(upi_url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, "upi_payment.html", {
        "qr_code": qr_base64,
        "amount": amount,
        "upi_id": upi_id
    })


def cod_success(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, "cod_success.html")


def payment_success(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, "payment_success.html")

def address(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    addresses = Address.objects.filter(user_id=user)

    if request.method == "POST":
        mobile = request.POST.get('mobile')

        if not re.match(r'^\d{10}$', mobile):
            return HttpResponse("Invalid Mobile Number")

        Address.objects.create(
            user_id=user,
            fullname=request.POST.get('fullname'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            pincode=request.POST.get('pincode'),
            state=request.POST.get('state'),
            mobile=mobile
        )

        return redirect("checkout")

    return render(request, "address.html", {
        "addresses": addresses
    })

def edit_address(request, id):
    if not request.user.is_authenticated:
        return redirect('login')

    address = get_object_or_404(Address, id=id, user_id=request.user)

    if request.method == "POST":
        address.fullname = request.POST['fullname']
        address.address = request.POST['address']
        address.city = request.POST['city']
        address.pincode = request.POST['pincode']
        address.state = request.POST['state']
        address.mobile = request.POST['mobile']
        address.save()

        return redirect("checkout")

    return render(request, "edit_address.html", {"address": address})


def delete_address(request, id):
    if not request.user.is_authenticated:
        return redirect('login')

    address = get_object_or_404(Address, id=id, user_id=request.user)
    address.delete()

    return redirect("checkout")

def set_default_address(request, id):
    if not request.user.is_authenticated:
        return redirect('login')

    Address.objects.filter(user_id=request.user).update(is_default=False)

    address = get_object_or_404(Address, id=id, user_id=request.user)
    address.is_default = True
    address.save()

    return redirect("checkout")
