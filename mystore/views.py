from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Product, Cart, Order, OrderItem
from .serializers import ProductSerializer, UserRegistrationSerializer
from .permissions import IsSeller, IsBuyer
from django.db import transaction


class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.db.models import Q

class ProductListCreateView(APIView):
    # get (buyer & seller)
    def get(self, request):
        keyword = request.query_params.get('search', None)
        min_price = request.query_params.get('min_price', None)
        max_price = request.query_params.get('max_price', None)
        
        products = Product.objects.all()
        
        # 1. ค้นหาจากคีย์เวิร์ด
        if keyword:
            products = products.filter(
                Q(title__icontains=keyword) | 
                Q(description__icontains=keyword)
            )
            
        # 2. คัดกรองจากราคา (ช่วงราคา)
        if min_price is not None:
            products = products.filter(unit_price__gte=min_price) # gte = Greater Than or Equal (>=)
            
        if max_price is not None:
            products = products.filter(unit_price__lte=max_price) # lte = Less Than or Equal (<=)
            
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
    
    # product management
    # post (seller)
    def post(self, request):
        if not IsSeller().has_permission(request, self):
            return Response({"detail": "Only sellers can create products."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(seller=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductDetailView(APIView):
    # get (buyer & seller) สำหรับดูรายละเอียดสินค้าทีละชิ้น
    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = ProductSerializer(product)
        # ข้อมูลที่ส่งกลับไปจะมีทั้ง description, unit_price และ available_quantity ในตัวอยู่แล้ว
        return Response(serializer.data)

class SellerProductListView(APIView):
    def get(self, request):
        if not IsSeller().has_permission(request, self):
            return Response({"detail": "Only sellers can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)
        
        # ค้นหาเฉพาะสินค้าที่ seller คนนี้เป็นเจ้าของ (อิงจาก Token ที่แนบมา)
        products = Product.objects.filter(seller=request.user)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class SellerProductDetailView(APIView):
    def get_object(self, pk, user):
        try:
            # ค้นหาสินค้าจาก id และต้องเป็นของ seller คนนี้เท่านั้น
            return Product.objects.get(pk=pk, seller=user)
        except Product.DoesNotExist:
            return None

    # แก้ไขสินค้า (PUT)
    def put(self, request, pk):
        if not IsSeller().has_permission(request, self):
            return Response({"detail": "Only sellers can modify products."}, status=status.HTTP_403_FORBIDDEN)
            
        product = self.get_object(pk, request.user)
        if product is None:
            return Response({"detail": "Product not found or you don't have permission to edit it."}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = ProductSerializer(product, data=request.data, partial=True) # partial=True อนุญาตให้ส่งมาแก้แค่บางฟิลด์ได้
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ลบสินค้า (DELETE)
    def delete(self, request, pk):
        if not IsSeller().has_permission(request, self):
            return Response({"detail": "Only sellers can delete products."}, status=status.HTTP_403_FORBIDDEN)
            
        product = self.get_object(pk, request.user)
        if product is None:
            return Response({"detail": "Product not found or you don't have permission to delete it."}, status=status.HTTP_404_NOT_FOUND)
            
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CartView(APIView):
    def post(self, request):
        if not IsBuyer().has_permission(request, self):
            return Response({"detail": "Only buyers can add to cart."}, status=status.HTTP_403_FORBIDDEN)
            
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        
        if quantity <= 0:
            return Response({"detail": "Quantity must be greater than 0."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
            
        # ตรวจสอบว่าสินค้ามีพอไหม
        if product.available_quantity < quantity:
            return Response({"detail": "Not enough stock available."}, status=status.HTTP_400_BAD_REQUEST)
            
        # ตรวจสอบว่ามีสินค้านี้ในตะกร้าหรือยัง
        cart_item, created = Cart.objects.get_or_create(buyer=request.user, product=product)
        
        if not created:
            # ถ้ามีอยู่แล้วให้บวกจำนวนเพิ่ม และเช็คสต็อกอีกรอบ
            if product.available_quantity < (cart_item.quantity + quantity):
                return Response({"detail": "Not enough stock to add more of this item to your cart."}, status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
            
        cart_item.save()
        
        return Response({
            "detail": "Item added to cart.",
            "cart_item": {
                "product_id": product.product_id,
                "title": product.title,
                "quantity": cart_item.quantity
            }
        }, status=status.HTTP_201_CREATED)

class CheckoutView(APIView):
    def post(self, request):
        if not IsBuyer().has_permission(request, self):
            return Response({"detail": "Only buyers can checkout."}, status=status.HTTP_403_FORBIDDEN)
            
        buyer = request.user
        
        try:
            with transaction.atomic():
                # ดึงสินค้าในตะกร้าทั้งหมดมา (select_for_update ล็อกแถวใน Database ให้ระหว่างทำ Transaction เพื่อป้องกัน Race Condition)
                cart_items = Cart.objects.filter(buyer=buyer).select_related('product')
                
                if not cart_items.exists():
                    return Response({"detail": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)
                    
                total_amount = 0
                
                # ตรวจสอบสต็อกอีกรอบ (Double check) สำหรับสินค้าทุกชิ้นในตะกร้า
                for item in cart_items:
                    product = Product.objects.select_for_update().get(pk=item.product.product_id)
                    if product.available_quantity < item.quantity:
                        raise ValueError(f"Not enough stock for product: {product.title}")
                    
                    total_amount += (item.quantity * product.unit_price)
                    
                # สร้าง Order
                order = Order.objects.create(
                    buyer=buyer,
                    total_amount=total_amount,
                    status='paid' # สมมติว่าจ่ายเงินสำเร็จทันที
                )
                
                # สร้าง OrderItems และหักลบ Stock ของ Products
                for item in cart_items:
                    product = Product.objects.select_for_update().get(pk=item.product.product_id)
                    
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item.quantity,
                        unit_price=product.unit_price
                    )
                    
                    # ลดสต็อก
                    product.available_quantity -= item.quantity
                    product.save()
                    
                # ล้างตะกร้า
                cart_items.delete()
                
                return Response({
                    "detail": "Checkout successful. Order placed.",
                    "order_id": order.order_id,
                    "total_amount": str(order.total_amount)
                }, status=status.HTTP_201_CREATED)
                
        except ValueError as e:
            # ถ้ามีสินค้าตัวไหนในตะกร้าหมดระหว่างทำรายการ transaction จะถูก rollback อัตโนมัติ (ไม่เซฟอะไรเลย)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": "An error occurred during checkout."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)