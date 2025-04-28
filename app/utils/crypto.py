import requests
import json
from datetime import datetime
import logging

# Настройка логгера
logger = logging.getLogger(__name__)

class BybitAPI:
    """
    Класс для взаимодействия с API биржи Bybit
    """
    # Базовый URL для API
    BASE_URL = "https://api.bybit.com"
    
    @staticmethod
    def get_btc_price():
        """
        Получает текущую цену BTC/USDT с Bybit
        
        :return: float - текущая цена BTC в USD или None в случае ошибки
        """
        try:
            # Endpoint для получения тикера
            endpoint = "/v5/market/tickers"
            
            # Параметры запроса
            params = {
                "category": "spot",
                "symbol": "BTCUSDT"
            }
            
            # Отправка запроса
            response = requests.get(
                f"{BybitAPI.BASE_URL}{endpoint}", 
                params=params
            )
            
            # Проверка успешности запроса
            if response.status_code == 200:
                data = response.json()
                
                # Проверка структуры ответа
                if data["retCode"] == 0 and "result" in data and "list" in data["result"]:
                    tickers = data["result"]["list"]
                    if tickers and len(tickers) > 0:
                        # Берем последнюю цену
                        return float(tickers[0]["lastPrice"])
            
            logger.error(f"Failed to get BTC price. Response: {response.text}")
            return None
            
        except Exception as e:
            logger.exception(f"Error getting BTC price: {str(e)}")
            return None
    
    @staticmethod
    def convert_usd_to_btc(usd_amount):
        """
        Конвертирует сумму USD в BTC по текущему курсу
        
        :param usd_amount: float - сумма в USD
        :return: float - эквивалент в BTC или None в случае ошибки
        """
        btc_price = BybitAPI.get_btc_price()
        if btc_price and btc_price > 0:
            return usd_amount / btc_price
        return None
    
    @staticmethod
    def convert_btc_to_usd(btc_amount):
        """
        Конвертирует сумму BTC в USD по текущему курсу
        
        :param btc_amount: float - сумма в BTC
        :return: float - эквивалент в USD или None в случае ошибки
        """
        btc_price = BybitAPI.get_btc_price()
        if btc_price:
            return btc_amount * btc_price
        return None
    
    @staticmethod
    def format_btc(btc_amount):
        """
        Форматирует сумму BTC с 8 знаками после запятой
        
        :param btc_amount: float - сумма в BTC
        :return: str - форматированная сумма
        """
        return f"{btc_amount:.8f}"
    
    @staticmethod
    def format_usd(usd_amount):
        """
        Форматирует сумму USD с 2 знаками после запятой и разделителями тысяч
        
        :param usd_amount: float - сумма в USD
        :return: str - форматированная сумма
        """
        return f"{usd_amount:,.2f}" 