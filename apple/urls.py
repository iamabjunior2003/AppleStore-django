"""
URL configuration for apple project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from products import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.display_products, name='home'),
    path('products/', views.display_products, name='products'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('add/', views.add_product, name='add_product'),
    path('category/<int:category_id>/', views.filter_products, name='filter_products'),
    path('cart/add/<int:id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/remove/<int:id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/increase/<int:id>/', views.increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:id>/', views.decrease_quantity, name='decrease_quantity'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path("checkout/", views.checkout, name="checkout"),
    path("payment/upi/", views.upi_payment, name="upi_payment"),
    path("payment/card/", views.card_payment, name="card_payment"),
    path("payment/cod/", views.cod_success, name="cod_success"),
    path("payment/success/", views.payment_success, name="payment_success"),

]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
