import requests
import json
from config import config

class TronManager:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "TRON-PRO-API-KEY": config.TRONGRID_API_KEY
        }
    
    def send_usdt(self, to_address: str, amount: float):
        """إرسال USDT عبر TronGrid API مباشرة"""
        url = f"{config.TRONGRID_API_URL}/wallet/triggersmartcontract"
        
        payload = {
            "contract_address": config.TRON_USDT_CONTRACT,
            "function_selector": "transfer(address,uint256)",
            "parameter": self._encode_parameters(to_address, amount),
            "owner_address": config.ADMIN_WALLET,
            "fee_limit": 10_000_000
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def _encode_parameters(self, to_address: str, amount: float) -> str:
        """تشفير معاملات العقد الذكي"""
        # إزالة 'T' من العنوان إذا موجودة
        clean_address = to_address[1:] if to_address.startswith('T') else to_address
        hex_amount = hex(int(amount * 10**6))[2:].zfill(64)
        return f"000000000000000000000000{clean_address}{hex_amount}"
