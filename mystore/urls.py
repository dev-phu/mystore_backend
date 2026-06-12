from django.urls import path
# ใช้code สำเร็จรูปไม่ต้องเขียนloginเอง
from rest_framework_simplejwt.views import TokenObtainPairView

from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Product Management
    # ========= get all product /post only seller ===========
    path("products/", views.ProductListCreateView.as_view()),
    
    # ========= get single product details (buyer & seller) ===========
    path("products/<int:pk>/", views.ProductDetailView.as_view(), name='product_detail_general'),
    # ========= get my product (seller) ===========
    path("products/mysellerproduct/", views.SellerProductListView.as_view(), name='my_products'),
    
    # ========= put/delete my product (seller) ===========
    path("products/mysellerproduct/<int:pk>/", views.SellerProductDetailView.as_view(), name='my_product_detail'),
    
    # Cart and Orders (Buyer)
    path("cart/", views.CartView.as_view(), name='cart'),
    path("orders/checkout/", views.CheckoutView.as_view(), name='checkout'),
]