from rest_framework import serializers
from .models import (
    Product,
    Collection,
)
from decimal import Decimal


class CollectionSerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Collection
        fields = ["id", "title", "products_count"]


class ProductSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        max_digits=6, decimal_places=2, source="unit_price"
    )
    price_with_tax = serializers.SerializerMethodField(method_name="calculate_tax")
    # images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "slug",
            "inventory",
            "price",
            "price_with_tax",
            "collection",
            "images",
        ]

    def calculate_tax(self, product: Product):
        return product.unit_price * Decimal(1.1)
