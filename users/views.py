from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views import View
from .forms import SigninForm, SignupForm
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request, 'home.html')

class SigninView(View):
    template_name = 'users/signin.html'

    def get(self, request):
        form = SigninForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = SigninForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('devices:list')
        print(f"=== FORM ERRORS: {form.errors}")
        return render(request, self.template_name, {'form': form})

class SignupView(View):
    template_name = 'users/signup.html'

    def get(self, request):
        form = SignupForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('devices:list')
        return render(request, self.template_name, {'form': form})
    
def signout(request):
    logout(request)
    return redirect('home')