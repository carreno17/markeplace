from django.db import models
from django.conf import settings
import os

User = settings.AUTH_USER_MODEL
#Indicando en que carpeta se van a encontrar las fotos subidas por el usuario
def marketplace_directory_path(instance, filename):
    banner_pic_name='markeplace/products/{0}/{1}'.format(instance.name, filename)
    full_path = os.path.join(settings.MEDIA_ROOT, banner_pic_name)

    #Por si el usuario quiere cambiar la foto del producto
    if os.path.exists(full_path):
    	os.remove(full_path)

    return banner_pic_name



# Create your models here.
class Product(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=100)
    description=models.TextField()
    thumbnail = models.ImageField(blank=True, null=True, upload_to=marketplace_directory_path)
    timestamp =  models.DateTimeField(auto_now_add=True)


    content_url = models.URLField(blank=True, null=True)
    content_file = models.FileField(blank=True, null=True)

    active = models.BooleanField(default=False)

    price = models.PositiveIntegerField(default=100) #cents Cant be lower than 50 cents@!

    def __str__(self):
        return self.name

    def price_display(self):
        return "{0:.2f}".format(self.price / 100)


class PurchasedProduct(models.Model):
    email = models.EmailField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    date_purchased = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self
