from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from mystore.models import Product, Cart, Order, OrderItem
from mystore.serializers import OrderSerializer
from mystore.permissions import IsBuyer

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

class OrderHistoryView(APIView):
    def get(self, request):
        if not IsBuyer().has_permission(request, self):
            return Response({"detail": "Only buyers can view their order history."}, status=status.HTTP_403_FORBIDDEN)
            
        # ดึงประวัติการสั่งซื้อของ buyer คนนี้ทั้งหมด พร้อม OrderItem 
        orders = Order.objects.filter(buyer=request.user).order_by('-create_at') # เรียงจากใหม่ไปเก่า
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
