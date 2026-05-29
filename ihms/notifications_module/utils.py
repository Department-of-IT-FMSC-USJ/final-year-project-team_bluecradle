import logging
from pywebpush import webpush, WebPushException
import json
from django.conf import settings

logger = logging.getLogger(__name__)

def send_web_push(user, title, body):
    # Send a Web Push notification to a user.
    # Resolves the correct push_subscription based on user role.
    # Returns True on success, False on failure.
    subscription_info = __get_subscription(user)

    if not subscription_info:
        logger.warning(f'No push subscription found for user {user.id} ({user.email})')
        return False
    
    payload = json.dumps(
        {
            'title': title,
            'body': body,
        }
    )

    try:
        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={
                'sub': settings.VAPID_ADMIN_EMAIL
            }
        )

        return True
    
    except WebPushException as e:
        logger.error(f'Web Push failed for user {user.id}: {e}')
        return False
    
def __get_subscription(user):
    # Resolve push_subscription from the correct profile based on role. 
    # Returns the subscription dict or None.
    if hasattr(user, 'phm_profile') and user.phm_profile.push_subscription:
        return user.phm_profile.push_subscription
    
    if hasattr(user, 'parent_profile') and user.parent_profile.push_subscription:
        return user.parent_profile.push_subscription
    
    return None
