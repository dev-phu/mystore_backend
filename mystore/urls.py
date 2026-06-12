from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView

from .views.auth import RegisterView
from .views.product import ProductListCreateView, ProductDetailView, SellerProductListView, SellerProductDetailView
from .views.order import CartView, CheckoutView, OrderHistoryView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Product Management
    # ========= get all product /post only seller ===========
    path("products/", ProductListCreateView.as_view()),
    
    # ========= get single product details (buyer & seller) ===========
    path("products/<int:pk>/", ProductDetailView.as_view(), name='product_detail_general'),
    # ========= get my product (seller) ===========
    path("products/mysellerproduct/", SellerProductListView.as_view(), name='my_products'),
    
    # ========= put/delete my product (seller) ===========
    path("products/mysellerproduct/<int:pk>/", SellerProductDetailView.as_view(), name='my_product_detail'),
    
    # Cart and Orders (Buyer)
    path("cart/", CartView.as_view(), name='cart'),
    path("orders/checkout/", CheckoutView.as_view(), name='checkout'),
    path("orders/", OrderHistoryView.as_view(), name='order_history'),
]