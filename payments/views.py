import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging

# Set up logging
logger = logging.getLogger(__name__)

@csrf_exempt
def start_payment(request):
    """
    Initiate payment with Flouci payment gateway
    """
    if request.method != 'POST':
        return JsonResponse(
            {"error": "Method not allowed"}, 
            status=405
        )

    # Configuration from settings with fallbacks
    import os

    flouci_config = {
        "app_token": os.environ.get('FLOUCI_APP_TOKEN', ''),
        "app_secret": os.environ.get('FLOUCI_APP_SECRET', ''),
        "redirect_url": os.environ.get('FLOUCI_REDIRECT_URL', ''),
    }


    # Validate required settings
    if not all(flouci_config.values()):
        logger.error("Flouci configuration missing in settings")
        return JsonResponse(
            {"error": "Payment gateway configuration error"},
            status=500
        )

    # Prepare payment payload
    payload = {
        "app_token": flouci_config['app_token'],
        "app_secret": flouci_config['app_secret'],
        "amount": "30500",  # Consider making this dynamic from request
        "accept_card": "true",
        "session_timeout_secs": 1200,
        "success_link": f"{flouci_config['redirect_url']}?status=success",
        "fail_link": f"{flouci_config['redirect_url']}?status=fail",
        "developer_tracking_id": "tracking_001"
    }

    headers = {'Content-Type': 'application/json'}
    api_url = 'https://developers.flouci.com/api/generate_payment'

    try:
        # Timeout after 10 seconds if no response
        response = requests.post(
            api_url, 
            json=payload, 
            headers=headers,
            timeout=10
        )
        response.raise_for_status()  # Raises exception for 4XX/5XX responses
        
        response_data = response.json()
        logger.info("Flouci payment initiated", extra={'response': response_data})
        
        payment_url = response_data.get("result", {}).get("link")
        
        if payment_url:
            return JsonResponse({
                "status": "success",
                "payment_url": payment_url,
                "details": response_data
            })
            
        logger.error("No payment URL in Flouci response", extra={'response': response_data})
        return JsonResponse({
            "error": "No payment URL returned by Flouci",
            "details": response_data
        }, status=500)

    except requests.exceptions.RequestException as e:
        logger.error("Flouci API request failed", exc_info=True)
        return JsonResponse({
            "error": "Payment gateway communication error",
            "details": str(e)
        }, status=500)
        
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON response from Flouci", exc_info=True)
        return JsonResponse({
            "error": "Invalid response from payment gateway",
            "raw_response": response.text
        }, status=500)


@csrf_exempt
def payment_callback(request):
    if request.method == "POST":
        data = json.loads(request.body)
      
        print("Callback received:", data)
        
        return JsonResponse({"status": "received"})
    return JsonResponse({"error": "Invalid method"}, status=405)
