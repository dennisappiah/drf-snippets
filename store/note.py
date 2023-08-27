from django.shortcuts import render
from .models import Product, OrderItem, Order, Customer, Collection
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, F, Value, ExpressionWrapper, DecimalField
from django.db import transaction
from django.db.models.aggregates import Count
from django.db.models.functions import Concat
from tags.models import TaggedItem

# -------------------------------------------------------------
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from .models import Product
from .serializers import ProductSerializer, CollectionSerializer


# Create your views here.
# def say_hello(request):
#     return render(request, "index.html", {"name": "Dennis", "age": 20})
def say_hello(request):
    try:
        product = Product.objects.get(pk=0)
    except ObjectDoesNotExist:
        pass

    """Filtering objects """
    # products equal to 20
    queryset = Product.objects.filter(unit_price__gt=20)

    # products equal to range
    queryset = Product.objects.filter(unit_price__range=(20, 30))

    # querying all products in collection 1
    queryset = Product.objects.filter(collection__id__gt=1)

    # products whose title coffee
    queryset = Product.objects.filter(title__startswith="coffee")

    # COMPLEX QUERIES

    # Products where inventory < 10 and price < 20
    queryset = Product.objects.filter(Q(inventory__lt=10) & Q(unit_price__lt=10))

    # Products where inventory < 10 OR price < 20
    queryset = Product.objects.filter(Q(inventory__lt=10) | Q(unit_price__lt=10))

    # Products where  inventory = price (Referencing Fields using F)
    queryset = Product.objects.filter(inventory=F("unit_price"))

    """Sorting objects """
    queryset = Product.objects.order_by("unit_price", "-title")

    """Selecting fields to query"""
    queryset = Product.objects.values("id", "title", "collection__title")

    # Select products that have been ordered and sort them by title
    queryset = Product.objects.filter(
        id__in=OrderItem.objects.values("product_id").distinct()
    ).order_by("title")

    """
    Selecting related objects 
    - collection attribute is a related object which belong to a different table so should be selected
    - we use `select_related` when the other end of the relationship has only one instance like Product can
    have only one collection
    
    - we use `prefetch_related` when the other end of the relationship has many instances like a product can have 
    many promotions
    """

    queryset = (
        Product.objects.select_related("collection")
        .prefetch_related("promotions")
        .all()
    )

    """Get the last 5 orders with the customer and their items (include product)"""
    "an order can belong to only one customer, also an order can have many items"
    orders = (
        Order.objects.select_related("customer")
        .prefetch_related("orderitems__product")
        .order_by("-placed_at")[:5]
    )

    """Aggregating objects"""
    result = Product.objects.aggregate(count=Count("id"))

    "Annotating objects - we can add new attributes while querying them"
    queryset = Customer.objects.annotate(is_new=Value(True))
    queryset = Customer.objects.annotate(new_id=F("id") + 1)

    queryset = Customer.objects.annotate(
        full_name=Concat("first_name", Value(" "), "last_name")
    )
    """ Grouping - Retrieve number of orders by each customer"""
    queryset = Customer.objects.annotate(orders_count=Count("order"))

    """Expression Wrapper """
    discounted_price = ExpressionWrapper(
        F("unit_price") * 0.8, output_field=DecimalField()
    )
    products = (
        Product.objects.select_related("collection")
        .values("id", "title")
        .annotate(discounted_price=discounted_price)
    )

    """Querying generic relationships"""
    tags = TaggedItem.objects.get_tags_for(Product, 1)

    """ Creating objects in django"""
    collection = Collection()
    collection.title = "Video Game"
    collection.save()

    collection = Collection(title="Video Game")
    collection.save()

    collection = Collection.objects.create(title="Video Game")

    """ Updating objects """
    collection1 = Collection.objects.get(pk=1)
    collection1.title = "Video Games 2"
    collection1.save()

    collection1 = Collection.objects.filter(pk=1).update(title="Video Games 2")
    collection1.save()

    """Transaction"""
    with transaction.atomic():
        order = Order()
        order.customer_id = 1
        order.save()

        item = OrderItem()
        item.order = order
        item.product_id = 1
        item.quantity = 20
        item.save()

    return render(request, "index.html", {"name": "Dennis", "products": list(products)})


# Create your views here.
@api_view(["GET", "POST"])
def product_list(request: Request) -> Response:
    if request.method == "GET":
        # early loading to display collection object
        queryset = Product.objects.select_related("collection").all()
        # context argument adds `request` object to the serializer object when instantiated
        serializer = ProductSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)
    elif request.method == "POST":
        # deserializing the product object
        serializer = ProductSerializer(data=request.data)
        # validating request data
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def product_detail(request: Request, id: int) -> Response:
    product = get_object_or_404(Product, pk=id)
    if request.method == "GET":
        # serializer converts Product object into a json object
        serializer = ProductSerializer(product)
        return Response(serializer.data)
    elif request.method == "PUT":
        # deserializing the product object
        serializer = ProductSerializer(product, data=request.data)
        # validating request data
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == "DELETE":
        if product.orderitems.count() > 0:
            return Response(
                {
                    "error": "Product cannot be deleted because it is associated with an order item"
                },
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "POST"])
def collection_list(request: Request) -> Response:
    if request.method == "GET":
        queryset = Collection.objects.annotate(products_count=Count("products")).all()
        # context argument adds `request` object to the serializer object when instantiated
        serializer = CollectionSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)
    elif request.method == "POST":
        # deserializing the product object
        serializer = CollectionSerializer(data=request.data)
        # validating request data
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
def collection_detail(request: Request, pk: int) -> Response:
    collection = get_object_or_404(
        Collection.objects.annotate(products_count=Count("products")), pk=id
    )
    if request.method == "GET":
        # serializer converts Product object into a json object
        serializer = CollectionSerializer(collection)
        return Response(serializer.data)
    elif request.method == "PUT":
        # deserializing the product object
        serializer = CollectionSerializer(collection, data=request.data)
        # validating request data
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == "DELETE":
        if collection.products.count() > 0:
            return Response(
                {
                    "error": "Collection cannot be deleted because it is associated with product "
                },
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


# def get_queryset(self):
#     queryset = Product.objects.all()
#     collection_id = self.request.query_params.get('collection_id')
#     if collection_id is not None:
#         queryset = queryset.filter(collection_id=collection_id)
#     return queryset

# /carts/:id -> response

# {
#     "id": "d44059c9-a855-44fa-b2bc-58478a7ef110",
#     "items": [
#         {
#             "id": 1,
#             "product": {
#                 "id": 4,
#                 "title": "Wood Chips - Regular",
#                 "unit_price": 73.47
#             },
#             "quantity": 10,
#             "total_price": 734.7
#         },
#         {
#             "id": 2,
#             "product": {
#                 "id": 6,
#                 "title": "Mustard - Individual Pkg",
#                 "unit_price": 76.62
#             },
#             "quantity": 20,
#             "total_price": 1532.4
#         }
#     ],
#     "total_price": 2267.1
# }
