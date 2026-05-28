from .models import FHBAtomicEvent

def unsynced_count(request):
    if request.user.is_authenticated and hasattr(request.user, 'phm_profile'):
        return {
            'unsynced_count': FHBAtomicEvent.objects.filter(
                phm=request.user.phm_profile,
                is_synced=False
            ).count()
        }
    return {'unsynced_count': 0}