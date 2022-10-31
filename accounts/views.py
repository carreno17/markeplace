from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.urls import reverse
from django.contrib.auth import authenticate
from .models import User
from django.contrib.auth import login
from django.contrib import messages



class LoginUser(View):

    def get(self, request, *args, **kwargs):
        context = {
        }
        return render(request, 'account/login.html', context)

    def post(self, request, *args, **kwargs):
        username = request.POST['username']
        password = request.POST['password']
        print(username)
        print(password)

        user = authenticate(username=username, password=password)

        if user is None:

            messages.warning(request, 'Invalid username or password')
                    
            context = {


            }            
            return render(request, 'account/login.html', context)
                
        else:
            login(self.request, user)
            return redirect('home')

