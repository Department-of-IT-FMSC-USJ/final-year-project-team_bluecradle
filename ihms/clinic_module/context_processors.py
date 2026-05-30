from .models import FHBAtomicEvent
from django.conf import settings

def unsynced_count(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'phm_profile'):
        return {'unsynced_count': 0}
    
    if request.user.is_authenticated and hasattr(request.user, 'phm_profile'):
        return {
            'unsynced_count': FHBAtomicEvent.objects.filter(
                phm=request.user.phm_profile,
                is_synced=False
            ).count()
        }
    return {'unsynced_count': 0}

def vapid_key(request):
    return {
        'vapid_public_key': getattr(settings, 'VAPID_PUBLIC_KEY', '')
    }