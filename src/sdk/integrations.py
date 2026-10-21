"""
LifeLens Ω - Client SDKs and Integration Examples

Includes:
- Python SDK
- JavaScript SDK
- API documentation
- Integration examples (WhatsApp, Slack, Chrome Extension)
"""

import requests
import json
import asyncio
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# PYTHON SDK
# ============================================================================

class LifeLensClient:
    """
    Python client library for LifeLens Ω Reality Integrity Intelligence System
    
    Installation:
        pip install lifelens-sdk
    
    Usage:
        client = LifeLensClient(api_key="your_api_key")
        result = client.check_message("Some suspicious message")
    """
    
    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.lifelens.io/v1",
        timeout: int = 10
    ):
        """
        Initialize LifeLens client.
        
        Args:
            api_key: API key for authentication
            api_url: Base URL for API (default: production)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def check_message(
        self,
        content: str,
        claimed_identity: Optional[str] = None,
        event_type: str = "message",
        source_channel: str = "api"
    ) -> Dict:
        """
        Check a message for reality integrity.
        
        Args:
            content: The message content to analyze
            claimed_identity: Who claims to be sending this (optional)
            event_type: Type of event (message, email, call, etc)
            source_channel: Channel it came through
        
        Returns:
            Assessment with risk level, integrity score, and recommendation
        
        Example:
            result = client.check_message(
                "Your account has been compromised. Click here to verify.",
                claimed_identity="Bank Support"
            )
            
            if result['risk_level'] == 'HIGH':
                print(f"Warning: {result['primary_concerns'][0]}")
        """
        
        payload = {
            "content": content,
            "claimed_identity": claimed_identity,
            "event_type": event_type,
            "source_channel": source_channel
        }
        
        try:
            response = self.session.post(
                f"{self.api_url}/reality-check",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise LifeLensAPIError(f"Failed to check message: {e}")
    
    def check_payment(
        self,
        amount: float,
        recipient: str,
        recipient_account: Optional[str] = None
    ) -> Dict:
        """
        Check a payment for safety.
        
        Args:
            amount: Amount being sent
            recipient: Recipient name or identifier
            recipient_account: Account number/details
        
        Returns:
            Assessment with payment safety analysis
        
        Example:
            result = client.check_payment(
                amount=50000,
                recipient="Unknown Contact",
                recipient_account="XXXX1234"
            )
            
            if result['reversibility'] < 0.2:
                print("Warning: This payment is difficult to reverse!")
        """
        
        payload = {
            "amount": amount,
            "recipient": recipient,
            "recipient_account": recipient_account
        }
        
        try:
            response = self.session.post(
                f"{self.api_url}/payment-check",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Payment check failed: {e}")
            raise LifeLensAPIError(f"Failed to check payment: {e}")
    
    def check_link(self, url: str) -> Dict:
        """
        Check if a link is safe to click.
        
        Args:
            url: The URL to check
        
        Returns:
            Assessment with link safety analysis
        
        Example:
            result = client.check_link("http://suspicious-bank.fake/verify")
            print(f"Link safety: {result['risk_level']}")
        """
        
        payload = {"url": url}
        
        try:
            response = self.session.post(
                f"{self.api_url}/link-check",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Link check failed: {e}")
            raise LifeLensAPIError(f"Failed to check link: {e}")
    
    def check_image(self, image_url: str) -> Dict:
        """
        Check if an image is authentic or manipulated.
        
        Args:
            image_url: URL of the image to check
        
        Returns:
            Assessment with authenticity analysis
        
        Example:
            result = client.check_image("https://example.com/image.jpg")
            if result['authenticity_score'] < 0.5:
                print("Warning: Image may be manipulated!")
        """
        
        payload = {"image_url": image_url}
        
        try:
            response = self.session.post(
                f"{self.api_url}/image-check",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Image check failed: {e}")
            raise LifeLensAPIError(f"Failed to check image: {e}")
    
    def get_safe_alternatives(self, action_type: str, goal: str) -> List[Dict]:
        """
        Get safer alternatives to achieve a user's goal.
        
        Args:
            action_type: Type of action (payment, verification, etc)
            goal: What the user is trying to accomplish
        
        Returns:
            List of safer alternative paths
        
        Example:
            alternatives = client.get_safe_alternatives(
                action_type="payment",
                goal="Pay electricity bill"
            )
            
            for alt in alternatives:
                print(f"Risk: {alt['risk_level']}, Path: {alt['description']}")
        """
        
        payload = {
            "action_type": action_type,
            "goal": goal
        }
        
        try:
            response = self.session.post(
                f"{self.api_url}/alternatives",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get alternatives: {e}")
            raise LifeLensAPIError(f"Failed to get alternatives: {e}")


# ============================================================================
# ASYNC CLIENT
# ============================================================================

class LifeLensAsyncClient:
    """
    Async Python client for LifeLens API
    
    Usage:
        async with LifeLensAsyncClient(api_key="key") as client:
            result = await client.check_message("message")
    """
    
    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.lifelens.io/v1"
    ):
        import aiohttp
        
        self.api_key = api_key
        self.api_url = api_url
        self.session = None
    
    async def __aenter__(self):
        import aiohttp
        
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    async def check_message(self, content: str) -> Dict:
        """Async version of check_message."""
        
        payload = {"content": content}
        
        async with self.session.post(
            f"{self.api_url}/reality-check",
            json=payload
        ) as response:
            return await response.json()


# ============================================================================
# EXCEPTIONS
# ============================================================================

class LifeLensAPIError(Exception):
    """Base exception for LifeLens API errors."""
    pass


class LifeLensAuthError(LifeLensAPIError):
    """Authentication failed."""
    pass


class LifeLensValidationError(LifeLensAPIError):
    """Input validation failed."""
    pass


# ============================================================================
# JAVASCRIPT SDK
# ============================================================================

# lifelens-sdk.js (JavaScript/TypeScript)

"""
LifeLens SDK for JavaScript/TypeScript

Installation:
    npm install @lifelens/sdk

Usage:
    import { LifeLensClient } from '@lifelens/sdk';
    
    const client = new LifeLensClient({ apiKey: 'your_api_key' });
    const result = await client.checkMessage('Suspicious message');
"""

JAVASCRIPT_SDK = """
// lifelens-sdk.js

class LifeLensClient {
    constructor({ apiKey, apiUrl = 'https://api.lifelens.io/v1' }) {
        this.apiKey = apiKey;
        this.apiUrl = apiUrl;
    }

    async checkMessage(content, { claimedIdentity = null, eventType = 'message' } = {}) {
        const response = await fetch(`${this.apiUrl}/reality-check`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content,
                claimed_identity: claimedIdentity,
                event_type: eventType
            })
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        return response.json();
    }

    async checkLink(url) {
        const response = await fetch(`${this.apiUrl}/link-check`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url })
        });

        return response.json();
    }

    async checkPayment(amount, recipient) {
        const response = await fetch(`${this.apiUrl}/payment-check`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ amount, recipient })
        });

        return response.json();
    }
}

export { LifeLensClient };
"""


# ============================================================================
# INTEGRATION EXAMPLES
# ============================================================================

# ============================================================================
# 1. WHATSAPP INTEGRATION
# ============================================================================

class WhatsAppIntegration:
    """
    LifeLens integration with WhatsApp Business API
    
    Setup:
        1. Create WhatsApp Business Account
        2. Set up webhook for incoming messages
        3. Configure LifeLens API credentials
    """
    
    def __init__(self, lifelens_client: LifeLensClient, whatsapp_token: str):
        """Initialize WhatsApp integration."""
        self.lifelens = lifelens_client
        self.whatsapp_token = whatsapp_token
    
    def handle_incoming_message(self, event: Dict) -> Optional[Dict]:
        """
        Handle incoming WhatsApp message.
        
        Args:
            event: WhatsApp webhook event
        
        Returns:
            Response to send to user (if high risk detected)
        """
        
        try:
            # Extract message details
            message = event['messages'][0]
            sender = message['from']
            text = message['text']['body']
            
            # Analyze with LifeLens
            assessment = self.lifelens.check_message(text, event_type="whatsapp")
            
            # If high risk, send warning
            if assessment['risk_level'] in ['HIGH', 'CRITICAL']:
                warning = self._generate_warning(assessment)
                return self._send_whatsapp_message(sender, warning)
            
            return None
        
        except Exception as e:
            logger.error(f"Error handling WhatsApp message: {e}")
            return None
    
    def _generate_warning(self, assessment: Dict) -> str:
        """Generate user-friendly warning message."""
        
        return f"""⚠️ CAUTION ADVISED

Risk Level: {assessment['risk_level']}
Integrity Score: {assessment['integrity_score']:.0%}

Concerns:
{chr(10).join(f"• {c}" for c in assessment['primary_concerns'])}

Recommendation: {assessment['recommendation']}

Safe Alternative:
{assessment['safe_alternative']}
"""
    
    def _send_whatsapp_message(self, phone: str, message: str) -> Dict:
        """Send message via WhatsApp API."""
        
        # WhatsApp API call (simplified)
        pass


# ============================================================================
# 2. SLACK INTEGRATION
# ============================================================================

class SlackIntegration:
    """
    LifeLens integration with Slack for suspicious message detection
    
    Setup:
        1. Create Slack app
        2. Enable message events
        3. Configure LifeLens credentials
    """
    
    def __init__(self, lifelens_client: LifeLensClient, slack_token: str):
        """Initialize Slack integration."""
        self.lifelens = lifelens_client
        self.slack_token = slack_token
    
    def analyze_message(self, text: str, user: str) -> Optional[str]:
        """
        Analyze Slack message and return warning if needed.
        
        Args:
            text: Message text
            user: Slack user ID
        
        Returns:
            Warning message to thread (if high risk)
        """
        
        try:
            assessment = self.lifelens.check_message(
                text,
                claimed_identity=user,
                source_channel="slack"
            )
            
            if assessment['risk_level'] == 'HIGH':
                return f"""🚨 Potential security concern detected in this message.
Risk Level: {assessment['risk_level']}
Integrity: {assessment['integrity_score']:.0%}

Please verify before acting on this message."""
            
            return None
        
        except Exception as e:
            logger.error(f"Slack analysis failed: {e}")
            return None


# ============================================================================
# 3. CHROME EXTENSION
# ============================================================================

CHROME_EXTENSION_MANIFEST = """
// manifest.json

{
  "manifest_version": 3,
  "name": "LifeLens Reality Integrity Check",
  "version": "1.0.0",
  "description": "Check the reality integrity of any message before you act",
  "permissions": [
    "activeTab",
    "scripting",
    "storage"
  ],
  "host_permissions": [
    "https://api.lifelens.io/*"
  ],
  "action": {
    "default_popup": "popup.html",
    "default_scripts": ["popup.js"]
  },
  "background": {
    "service_worker": "background.js"
  },
  "icons": {
    "16": "images/icon-16.png",
    "48": "images/icon-48.png",
    "128": "images/icon-128.png"
  }
}
"""

CHROME_EXTENSION_POPUP = """
// popup.html

<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto; }
    .container { width: 400px; padding: 16px; }
    .high-risk { color: #d32f2f; background: #ffebee; padding: 12px; border-radius: 4px; }
    .low-risk { color: #388e3c; background: #e8f5e9; padding: 12px; border-radius: 4px; }
    .button { padding: 8px 16px; margin-top: 8px; cursor: pointer; }
  </style>
</head>
<body>
  <div class="container">
    <h2>LifeLens Reality Check</h2>
    <div id="result"></div>
    <button class="button" id="analyze">Check This Message</button>
    <button class="button" id="settings">Settings</button>
  </div>
  <script src="popup.js"></script>
</body>
</html>
"""

CHROME_EXTENSION_POPUP_JS = """
// popup.js

document.getElementById('analyze').addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    
    // Get selected text
    chrome.tabs.sendMessage(tab.id, {action: 'getSelectedText'}, async (response) => {
        if (!response || !response.text) {
            document.getElementById('result').innerText = 'Select text to analyze';
            return;
        }
        
        try {
            const apiKey = await chrome.storage.sync.get('apiKey');
            const result = await fetch('https://api.lifelens.io/v1/reality-check', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${apiKey.value}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({content: response.text})
            }).then(r => r.json());
            
            const resultDiv = document.getElementById('result');
            const riskClass = result.risk_level === 'HIGH' ? 'high-risk' : 'low-risk';
            resultDiv.innerHTML = `
                <div class="${riskClass}">
                    <strong>Risk Level:</strong> ${result.risk_level}<br>
                    <strong>Integrity:</strong> ${(result.integrity_score * 100).toFixed(0)}%<br>
                    <strong>Recommendation:</strong> ${result.recommendation}
                </div>
            `;
        } catch (error) {
            document.getElementById('result').innerText = 'Error analyzing message';
        }
    });
});
"""


# ============================================================================
# 4. BANKING API INTEGRATION
# ============================================================================

class BankingIntegration:
    """
    Integration with banking apps to check payment safety
    
    Example: Prevent fraudulent payments before they're sent
    """
    
    def __init__(self, lifelens_client: LifeLensClient):
        self.lifelens = lifelens_client
    
    def validate_payment(self, amount: float, recipient: str, context: Dict) -> Dict:
        """
        Validate payment before execution.
        
        Args:
            amount: Payment amount
            recipient: Recipient identifier
            context: Additional context (contact history, etc)
        
        Returns:
            Validation result with safety assessment
        """
        
        # Check payment safety
        payment_check = self.lifelens.check_payment(amount, recipient)
        
        # Check recipient context
        if 'claimed_identity' in context:
            message_check = self.lifelens.check_message(
                f"Payment request from {context['claimed_identity']}",
                claimed_identity=context['claimed_identity']
            )
        else:
            message_check = None
        
        # Combine assessments
        return {
            "payment_safe": payment_check['risk_level'] not in ['HIGH', 'CRITICAL'],
            "payment_assessment": payment_check,
            "context_assessment": message_check,
            "reversibility": payment_check.get('reversibility', 0),
            "recommended_action": self._get_action(payment_check, message_check)
        }
    
    def _get_action(self, payment_check: Dict, message_check: Optional[Dict]) -> str:
        """Determine recommended action."""
        
        if payment_check['risk_level'] == 'CRITICAL':
            return "BLOCK"
        elif payment_check['risk_level'] == 'HIGH':
            return "REQUIRE_VERIFICATION"
        elif message_check and message_check['risk_level'] == 'HIGH':
            return "ADD_FRICTION"
        else:
            return "ALLOW"


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Example 1: Basic message check
    print("=" * 60)
    print("Example 1: Basic Message Check")
    print("=" * 60)
    
    client = LifeLensClient(api_key="your_api_key_here")
    
    suspicious_message = """
    Urgent! Your bank account has been compromised.
    Click here immediately to verify your identity:
    http://verify-account.fake-bank.com
    Do NOT tell anyone about this message.
    """
    
    try:
        result = client.check_message(suspicious_message, claimed_identity="Bank Support")
        print(json.dumps(result, indent=2))
    except LifeLensAPIError as e:
        print(f"Error: {e}")
    
    # Example 2: Payment check
    print("\n" + "=" * 60)
    print("Example 2: Payment Check")
    print("=" * 60)
    
    try:
        result = client.check_payment(
            amount=50000,
            recipient="Unknown Contact",
            recipient_account="XXXX1234"
        )
        print(json.dumps(result, indent=2))
    except LifeLensAPIError as e:
        print(f"Error: {e}")
    
    # Example 3: Async usage
    print("\n" + "=" * 60)
    print("Example 3: Async Usage")
    print("=" * 60)
    
    async def async_example():
        async with LifeLensAsyncClient(api_key="your_api_key") as client:
            result = await client.check_message("Check this message")
            print(json.dumps(result, indent=2))
    
    # asyncio.run(async_example())

