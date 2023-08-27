from django.db import models
from django.db.models import CharField
from django.core.validators import MinValueValidator


class Collection(models.Model):
    title = models.CharField(max_length=255)
    # products

    def __str__(self) -> CharField:
        return self.title

    class Meta:
        ordering = ["title"]


class Product(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(null=True, blank=True)
    unit_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(1, message="unit price cannot less than 1")],
    )
    inventory = models.IntegerField()
    last_update = models.DateTimeField(auto_now=True)
    collection = models.ForeignKey(
        Collection, related_name="products", on_delete=models.PROTECT
    )

    def __str__(self) -> CharField:
        return self.title

    class Meta:
        ordering = ["title"]
