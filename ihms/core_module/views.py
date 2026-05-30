from django.shortcuts import render
from django.http import FileResponse
import os
from django.conf import settings

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

def error_404(request, exception):
    return render(
        request,
        'core_module/404.html',
        {
            'title': 'Page Not Found'
        },
        status=404
    )

def error_500(request):
    return render(
        request,
        'core_module/500.html',
        {
            'title': 'Server Error'
        },
        status=500
    )

def error_403(request, exception=None):
    return render(
        request,
        'core_module/403.html',
        {
            'title': 'Permission Denied'
        },
        status=403
    )

def error_400(request, exception=None):
    return render(
        request,
        'core_module/400.html',
        {
            'title': 'Bad Request'
        },
        status=400
    )

def service_worker(request):
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'sw', 'service-worker.js')
    return FileResponse(open(sw_path, 'rb'), content_type='application/javascript')