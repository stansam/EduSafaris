import requests
import base64
from datetime import datetime
from flask import current_app


class MpesaClient:
    """M-Pesa API Client for STK Push payments"""
    
    def __init__(self):
        self.consumer_key = current_app.config.get('MPESA_CONSUMER_KEY')
        self.consumer_secret = current_app.config.get('MPESA_CONSUMER_SECRET')
        self.business_short_code = current_app.config.get('MPESA_BUSINESS_SHORT_CODE')
        self.passkey = current_app.config.get('MPESA_PASSKEY')
        self.callback_url = current_app.config.get('MPESA_CALLBACK_URL')
        self.environment = current_app.config.get('MPESA_ENVIRONMENT', 'sandbox')
        
        # Set API URLs based on environment
        if self.environment == 'production':
            self.base_url = 'https://api.safaricom.co.ke'
        else:
            self.base_url = 'https://sandbox.safaricom.co.ke'
    
    def get_access_token(self):
        """Get OAuth access token from M-Pesa API"""
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        
        try:
            response = requests.get(
                url,
                auth=(self.consumer_key, self.consumer_secret)
            )
            
            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                raise Exception(f"Failed to get access token: {response.text}")
        
        except Exception as e:
            raise Exception(f"M-Pesa authentication error: {str(e)}")
    
    def generate_password(self):
        """Generate password for STK Push"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        data_to_encode = f"{self.business_short_code}{self.passkey}{timestamp}"
        encoded = base64.b64encode(data_to_encode.encode())
        return encoded.decode('utf-8'), timestamp
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """
        Initiate STK Push payment
        
        Args:
            phone_number: string (format: 254XXXXXXXXX)
            amount: float
            account_reference: string
            transaction_desc: string
        
        Returns:
            Dictionary with M-Pesa response
        """
        access_token = self.get_access_token()
        password, timestamp = self.generate_password()
        
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'BusinessShortCode': self.business_short_code,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(amount),
            'PartyA': phone_number,
            'PartyB': self.business_short_code,
            'PhoneNumber': phone_number,
            'CallBackURL': self.callback_url,
            'AccountReference': account_reference,
            'TransactionDesc': transaction_desc
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            data = response.json()
            
            if response.status_code == 200 and data.get('ResponseCode') == '0':
                return {
                    'success': True,
                    'CheckoutRequestID': data.get('CheckoutRequestID'),
                    'MerchantRequestID': data.get('MerchantRequestID'),
                    'ResponseCode': data.get('ResponseCode'),
                    'ResponseDescription': data.get('ResponseDescription')
                }
            else:
                return {
                    'success': False,
                    'errorCode': data.get('errorCode'),
                    'errorMessage': data.get('errorMessage', 'STK Push failed')
                }
        
        except Exception as e:
            return {
                'success': False,
                'errorMessage': f"Request failed: {str(e)}"
            }
    
    def query_stk_status(self, checkout_request_id):
        """
        Query STK Push payment status
        
        Args:
            checkout_request_id: string
        
        Returns:
            Dictionary with payment status
        """
        access_token = self.get_access_token()
        password, timestamp = self.generate_password()
        
        url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'BusinessShortCode': self.business_short_code,
            'Password': password,
            'Timestamp': timestamp,
            'CheckoutRequestID': checkout_request_id
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            data = response.json()
            
            return {
                'success': True,
                'ResultCode': data.get('ResultCode'),
                'ResultDesc': data.get('ResultDesc'),
                'MerchantRequestID': data.get('MerchantRequestID'),
                'CheckoutRequestID': data.get('CheckoutRequestID')
            }
        
        except Exception as e:
            return {
                'success': False,
                'errorMessage': f"Status query failed: {str(e)}"
            }
