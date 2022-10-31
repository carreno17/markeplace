from email import message
from itertools import product
from django.contrib import messages
from multiprocessing.sharedctypes import Value
import stripe
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import UpdateView, DetailView
from django.views.generic.base import TemplateView
from django.core.paginator import Paginator
from markeplace.models import Product
from markeplace.forms import ProductModelForm
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from stripe.error import SignatureVerificationError
from accounts.models import PurchasedProduct, UserLibrary
from django.core.mail import send_mail
from django.contrib.auth import get_user_model




stripe.api_key = settings.STRIPE_SECRET_KEY
User = get_user_model()

class HomeView(View):
    def get(self, request, *args, **kwargs):
        products = Product.objects.filter(active=True)
        form = ProductModelForm()

        digital_products_data = None

        if products:
            paginator = Paginator(products, 9)
            page_number = request.GET.get('page')
            digital_products_data = paginator.get_page(page_number)
        
        context={
            'products':digital_products_data,
            'form':form
        }
        return render(request, 'pages/index.html', context)

    def post(self, request, *args, **kwargs):
        products = Product.objects.filter(active=True)

        form=ProductModelForm()

        if request.method == "POST":
            form=ProductModelForm(request.POST, request.FILES)

            if form.is_valid():
                form.user=request.user
                name = form.cleaned_data.get('name')
                description = form.cleaned_data.get('description')
                thumbnail = form.cleaned_data.get('thumbnail')
                slug = form.cleaned_data.get('slug')
                content_url = form.cleaned_data.get('content_url')
                content_file = form.cleaned_data.get('content_file')
                price = form.cleaned_data.get('price')
                active = form.cleaned_data.get('active')

                p, created = Product.objects.get_or_create(user=form.user,name=name,description=description, thumbnail=thumbnail, slug=slug, content_url=content_url, content_file=content_file,price=price, active=active)
                p.save()
                return redirect('home')




        digital_products_data = None

        if products:
            paginator = Paginator(products, 9)
            page_number = request.GET.get('page')
            digital_products_data = paginator.get_page(page_number)
        
        context={
            'products':digital_products_data
        }
        return render(request, 'pages/index.html', context)



class ProductUserList(View):
    def get(self, request, *args, **kwargs):
        try:
            products = Product.objects.filter(user=self.request.user) 
            context={
            
            'products': products,

            } 
            return render(request, 'pages/product/user_productlist.html', context) 
        
        except:
            messages.warning('No has creado productos')


class LibraryUserList(LoginRequiredMixin, View):
    def get(self, request, username, *args, **kwargs):
        user = get_object_or_404(User, username=username)
        library=UserLibrary.objects.get(user=user)
        context={
            'library': library,
       }
        return render(request, 'pages/product/library_user.html', context)
     

class ProductUpdate(LoginRequiredMixin, UpdateView):
    template_name = 'pages/product/edit_product.html'
    form_class = ProductModelForm

    
    def get_queryset(self):
        return Product.objects.filter(user=self.request.user) 

    def get_success_url(self):
        return reverse('product-list')


class ProductDetailView(View):


    def get(self, request,*args, **kwargs):
        product = get_object_or_404(Product, id=self.kwargs["id"])

        has_access=None
        
        if self.request.user.is_authenticated:
            if product in self.request.user.rlibrary.products.all():
                has_access= True

                
        context={
            'product':product,
            
        }
        context.update({
            'STRIPE_PUBLIC_KEY':settings.STRIPE_PUBLIC_KEY,
            'has_access': has_access
        })
        return render(request, 'pages/product/detail_product.html', context)


class CreateCheckoutSessionView(View):
      def post(self, request, *args, **kwargs):
        product_id = self.kwargs["id"]
        product = Product.objects.get(id=product_id)
        YOUR_DOMAIN = "http://127.0.0.1:8000"
        customer=None
        customer_email=None

        if request.user.is_authenticated:
            if request.user.stripe_customer_id:
                customer = request.user.stripe_customer_id
            else:
                customer_email=request.user.email

        checkout_session = stripe.checkout.Session.create(
            customer=customer,
            customer_email=customer_email,
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': product.price,
                        'product_data': {
                            'name': product.name,
                            # 'images': ['https://i.imgur.com/EHyR2nP.png'],
                        },
                    },
                    'quantity': 1,
                },
            ],
            metadata={
                "product_id": product.id
            },
            mode='payment',

            success_url=YOUR_DOMAIN + reverse("success"),
            cancel_url=YOUR_DOMAIN + reverse("home")
        )
        return JsonResponse({
            'id': checkout_session.id
        })


class SuccessView(TemplateView):
    template_name='pages/product/success.html'

class CancelView(TemplateView):
    template_name='pages/product/cancel.html'

@csrf_exempt
def stripe_webhook(request, *args, **kwargs):
    CHECKOUT_SESSION_COMPLETED = "checkout.session.completed"
    payload=request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]

    try:
        event=stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        print(e)
        return HttpResponse(status=400)
    
    except SignatureVerificationError as e:
        print(e)
        return HttpResponse(status=400)

    # escuchar por pago exitoso
    if event["type"] == CHECKOUT_SESSION_COMPLETED:
        print(event)
    
        # quien pago por que cosa?
        product_id=event["data"]["object"]["metadata"]["product_id"]
        product=Product.objects.get(id=product_id)

        stripe_customer_id=event["data"]["object"]["customer"]

        # dar acceso al producto
        try:
            #revisar si el usuario ya tiene un customer ID
            user = User.objects.get(stripe_customer_id=stripe_customer_id)

            user.rlibrary.products.add(product)
            user.rlibrary.save()

        except:
            #si el usuario no tiene customer ID, pero este si esta registrado en el sitio web
            stripe_customer_email = event["data"]["object"]["customer_details"]["email"]
            try:
                user = User.objects.get(email=stripe_customer_email)
                
                user.stripe_customer_id = stripe_customer_email
                user.rlibrary.products.add(product)
                user.rlibrary.save()
                user.save()

            except User.DoesNotExist:

                PurchasedProduct.objects.get_or_create(
                    email=stripe_customer_email,
                    product=product
                )

                send_mail(
                    subject="Create an account to access your content",
                    message="Please signup to access your products",
                    recipient_list=[stripe_customer_email],
                    from_email="Vudera <mail@vudera.com>"
                )

                pass




    return HttpResponse()

def CreateProduct(request):

        form=ProductModelForm()

        if request.method == "POST":
            form=ProductModelForm(request.POST, request.FILES)

            if form.is_valid():
                form.user=request.user
                name = form.cleaned_data.get('name')
                description = form.cleaned_data.get('description')
                thumbnail = form.cleaned_data.get('thumbnail')
                content_url = form.cleaned_data.get('content_url')
                content_file = form.cleaned_data.get('content_file')
                price = form.cleaned_data.get('price')
                active = form.cleaned_data.get('active')

                p, created = Product.objects.get_or_create(user=form.user,name=name,description=description, thumbnail=thumbnail, content_url=content_url, content_file=content_file,price=price, active=active)
                p.save()
                return redirect('home')
            
        return render(request, 'pages/product/create_product.html', {'form':form})

    