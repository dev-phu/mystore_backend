from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from mystore.models import Product
from mystore.serializers import ProductSerializer
from mystore.permissions import IsSeller


class ProductListCreateView(APIView):
    # get (buyer & seller)
    def get(self, request):
        keyword = request.query_params.get("search", None)
        min_price = request.query_params.get("min_price", None)
        max_price = request.query_params.get("max_price", None)

        products = Product.objects.filter(is_active=True)

        # 1. ค้นหาจากคีย์เวิร์ด
        if keyword:
            products = products.filter(
                Q(title__icontains=keyword) | Q(description__icontains=keyword)
            )

        # 2. คัดกรองจากราคา (ช่วงราคา)
        if min_price is not None:
            products = products.filter(unit_price__gte=min_price)

        if max_price is not None:
            products = products.filter(unit_price__lte=max_price)

        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    # product management
    # post (seller)
    def post(self, request):
        if not IsSeller().has_permission(request, self):
            return Response(
                {"detail": "Only sellers can create products."},
                status=status.HTTP_403_FORBIDDEN,
            )

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
            return Response(
                {"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductSerializer(product)
        # ข้อมูลที่ส่งกลับไปจะมีทั้ง description, unit_price และ available_quantity ในตัวอยู่แล้ว
        return Response(serializer.data)


class SellerProductListView(APIView):
    def get(self, request):
        if not IsSeller().has_permission(request, self):
            return Response(
                {"detail": "Only sellers can access this endpoint."},
                status=status.HTTP_403_FORBIDDEN,
            )

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
            return Response(
                {"detail": "Only sellers can modify products."},
                status=status.HTTP_403_FORBIDDEN,
            )

        product = self.get_object(pk, request.user)
        if product is None:
            return Response(
                {
                    "detail": "Product not found or you don't have permission to edit it."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProductSerializer(
            product, data=request.data, partial=True
        )  # partial=True อนุญาตให้ส่งมาแก้แค่บางฟิลด์ได้
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ลบสินค้า (DELETE)
    def delete(self, request, pk):
        if not IsSeller().has_permission(request, self):
            return Response(
                {"detail": "Only sellers can delete products."},
                status=status.HTTP_403_FORBIDDEN,
            )

        product = self.get_object(pk, request.user)
        if product is None:
            return Response(
                {
                    "detail": "Product not found or you don't have permission to delete it."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        product.is_active = False
        product.save()
        return Response({"detail": "Product hidden successfully."}, status=status.HTTP_200_OK)
