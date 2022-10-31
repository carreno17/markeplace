from django.contrib import admin
from .models import Product, PurchasedProduct

admin.site.register(Product)
admin.site.register(PurchasedProduct)
