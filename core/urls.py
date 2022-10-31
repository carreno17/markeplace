from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.urls.conf import include

from  .views import ( HomeView, 
ProductUserList,
ProductUpdate, 
ProductDetailView, 
CreateCheckoutSessionView, 
SuccessView,
stripe_webhook,
LibraryUserList,
CreateProduct,
)

from accounts.views import LoginUser
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name="home"),
    path('accounts/login/', LoginUser.as_view(), name="login"),
    
    path('create-checkout-session/<id>/', CreateCheckoutSessionView.as_view(), name="create-checkout-session"),
    path('library/<username>/', LibraryUserList.as_view(), name="user-library"),
    path('create/product', CreateProduct, name="create-product"),
    path('products/', ProductUserList.as_view(), name="product-list"),
    path('products/<id>/detail/', ProductDetailView.as_view(), name="product-detail"),
    path('products/<pk>/update/', ProductUpdate.as_view(), name="product-update"),
    path("webhooks/stripe/", stripe_webhook, name="stripe-webhook"),

    
    path('success/', SuccessView.as_view(), name="success"),
    




    path('accounts/', include('allauth.urls')),
    path('user/', include("accounts.urls", namespace='accounts')),

    path('markeplace/', include("markeplace.urls", namespace='markeplace'))
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)