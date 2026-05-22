from django.shortcuts import render

def home(request):
    return render(
        request,
        'core_module/home.html',
        {
            'title':"BlueCradle - Empowering Sri Lanka's Public Health Excellence"
        }
    )

def features(request):
    return render(
        request,
        'core_module/features.html',
        {
            'title':'Features - BlueCradle'
        }
    )