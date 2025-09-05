import os
import requests
import logging
from dotenv import load_dotenv
import hmac
import hashlib
import time

load_dotenv()
logger = logging.getLogger(__name__)

def verify_webhook_signature(signature_header: str, body: bytes) -> bool:
    webhook_secret = os.getenv("CALENDLY_WEBHOOK_SECRET")
    if not webhook_secret or webhook_secret == "your_webhook_secret_here":
        logger.warning("CALENDLY_WEBHOOK_SECRET is not properly set - skipping signature verification")
        return True 
    
    if not signature_header:
        logger.error("No signature header provided")
        return False

    try:
        parts = {}
        for item in signature_header.split(","):
            if "=" in item:
                key, value = item.split("=", 1)
                parts[key] = value
        
        timestamp = parts.get("t")
        signature = parts.get("v1")

        if not timestamp or not signature:
            logger.error(f"Missing timestamp or signature in header: {signature_header}")
            return False
        if int(timestamp) < time.time() - 300:
            logger.error("Webhook timestamp too old")
            return False
        signed_payload = f"{timestamp}.{body.decode('utf-8')}"
        expected_signature = hmac.new(
            webhook_secret.encode(), 
            msg=signed_payload.encode(), 
            digestmod=hashlib.sha256
        ).hexdigest()
        
        is_valid = hmac.compare_digest(expected_signature, signature)
        if not is_valid:
            logger.error(f"Signature mismatch. Expected: {expected_signature}, Got: {signature}")
        
        return is_valid
    
    except Exception as e:
        logger.error(f"Webhook signature verification error: {e}")
        return False

class CalendlyService:
    def __init__(self):
        self.api_token = os.getenv('CALENDLY_API_TOKEN')
        self.user_uri = os.getenv('CALENDLY_USER_URI')
        self.webhook_secret = os.getenv('CALENDLY_WEBHOOK_SECRET', 'default_secret')
        
        if not self.api_token or not self.user_uri:
            logger.warning("Calendly API token and user URI not properly configured")
            return
        
        self.base_url = "https://api.calendly.com"
        self.headers = {
            'Authorization': f'Bearer {self.api_token}', 
            'Content-Type': 'application/json'
        }
        
        try:
            self.organization_uri = self._get_organization_uri()
        except Exception as e:
            logger.error(f"Error getting organization URI: {e}")
            self.organization_uri = None
        try:
            self.setup_webhooks()
        except Exception as e:
            logger.warning(f"Webhook setup failed (this is OK for development): {e}")

    def _get_organization_uri(self) -> str:
        """Get organization URI from user info (required for webhook creation)"""
        try:
            response = requests.get(f"{self.base_url}/users/me", headers=self.headers)
            response.raise_for_status()
            user_data = response.json()
            org_uri = user_data['resource']['current_organization']
            logger.info(f"Found organization URI: {org_uri}")
            return org_uri
        except Exception as e:
            logger.error(f"Error getting organization URI: {e}")
            return self.user_uri.replace('/users/', '/organizations/')

    def get_event_type_from_uri(self, event_uri: str) -> dict:
        """Fetch event type details from Calendly API"""
        try:
            response = requests.get(event_uri, headers=self.headers)
            response.raise_for_status()
            result = response.json().get("resource")
            logger.info(f"Successfully fetched event type: {result.get('name', 'Unknown')}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch event type from URI {event_uri}: {e}")
            return None

    def create_webhook(self, webhook_url: str, events: list) -> dict:
        """Create a webhook subscription"""
        try:
            data = {
                'url': webhook_url,
                'events': events,
                'organization': self.organization_uri,
                'scope': 'organization'
            }
            
            logger.info(f"Creating webhook with data: {data}")
            
            response = requests.post(
                f"{self.base_url}/webhook_subscriptions",
                headers=self.headers,
                json=data
            )
            
            if response.status_code == 409:
                logger.info("Webhook with this URL already exists - this is OK")
                return {"status": "already_exists"}
            
            response.raise_for_status()
            result = response.json()
            logger.info(f"Webhook created successfully: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating webhook: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
                if e.response.status_code == 409:
                    logger.info("Webhook already exists - continuing without error")
                    return {"status": "already_exists"}
            raise

    def get_webhooks(self) -> list:
        """Get all webhook subscriptions"""
        try:
            if not self.organization_uri:
                logger.warning("Organization URI not available, cannot fetch webhooks")
                return []
                
            params = {'organization': self.organization_uri}
            response = requests.get(
                f"{self.base_url}/webhook_subscriptions",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            webhooks = response.json().get('collection', [])
            logger.info(f"Found {len(webhooks)} existing webhooks")
            return webhooks
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching webhooks: {e}")
            return []

    def delete_webhook(self, webhook_uuid: str) -> bool:
        """Delete a webhook subscription"""
        try:
            response = requests.delete(
                f"{self.base_url}/webhook_subscriptions/{webhook_uuid}",
                headers=self.headers
            )
            response.raise_for_status()
            logger.info(f"Webhook {webhook_uuid} deleted successfully")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting webhook {webhook_uuid}: {e}")
            return False

    def setup_webhooks(self) -> bool:
        """Setup required webhooks for the application"""
        try:
            if not self.organization_uri:
                logger.warning("Organization URI not available, skipping webhook setup")
                return False
            webhook_events = [
                'invitee.created',
                'invitee.canceled'
            ]
            
            
            ngrok_url = os.getenv('NGROK_URL')
            if not ngrok_url or ngrok_url == 'your_ngrok_url_here' or 'ngrok-free.app' not in ngrok_url:
                logger.info("NGROK_URL not properly configured. Skipping webhook setup.")
                logger.info("To enable webhooks:")
                logger.info("1. Install ngrok: https://ngrok.com/download")
                logger.info("2. Run: ngrok http 8000")
                logger.info("3. Update NGROK_URL in .env with the https URL")
                return False
            
            webhook_url = f"{ngrok_url}/api/webhooks/calendly"
            logger.info(f"Setting up webhook for URL: {webhook_url}")
            existing_webhooks = self.get_webhooks()
            for webhook in existing_webhooks:
                callback_url = webhook.get('callback_url', '')
                if callback_url == webhook_url:
                    logger.info("Webhook already exists and is active")
                    return True
                elif webhook_url.replace('https://', '') in callback_url or ngrok_url in callback_url:
                    webhook_uuid = webhook['uri'].split('/')[-1]
                    logger.info(f"Deleting outdated webhook: {callback_url}")
                    self.delete_webhook(webhook_uuid)
            result = self.create_webhook(webhook_url, webhook_events)
            if result.get("status") == "already_exists":
                logger.info("Webhook setup completed (already existed)")
            else:
                logger.info("Webhook setup completed successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Webhook setup failed: {e}")
            return False

    def test_webhook_connection(self) -> bool:
        """Test if webhook URL is accessible"""
        try:
            ngrok_url = os.getenv('NGROK_URL')
            if not ngrok_url:
                return False
                
            test_url = f"{ngrok_url}/api/webhooks/calendly"
            response = requests.post(test_url, json={'test': True}, timeout=5)
            return True 
        except:
            return False