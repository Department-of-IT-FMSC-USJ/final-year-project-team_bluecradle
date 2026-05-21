from django.shortcuts import render

def home(request):
    return render(request, 'core_module/home.html')

def features(request):
    return render(request, 'core_module/features.html')