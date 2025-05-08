from django.shortcuts import render
from django.contrib.auth import authenticate,login
from django.contrib import messages
# Create your views here.


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password =request.POST['password']
        user_type =request.POST['user_type']

        user=authenticate(request,username = username,password = password)