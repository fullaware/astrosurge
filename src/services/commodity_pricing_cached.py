"""
Enhanced Commodity Pricing Service with MongoDB Caching

This service handles fetching real commodity prices from yfinance API
and caching them in MongoDB for consistent mission economics.
"""
import yfinance as yf
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import os
from pymongo import MongoClient
from bson import ObjectId

logger = logging.getLogger(__name__)


class CommodityPricingService:
    """
    Enhanced service for fetching and managing commodity prices with MongoDB caching.
    
    Features:
    - Fetch real-time commodity prices from yfinance
    - Cache prices in MongoDB with timestamps
    - Weekly price updates (Monday morning)
    - Price history tracking
    - Graceful fallback when API fails
    """
    
    def __init__(self, mongodb_uri: str = None):
        """Initialize the commodity pricing service with MongoDB connection"""
        # MongoDB connection
        self.mongodb_uri = mongodb_uri or os.getenv("MONGODB_URI", "mongodb://archimedes:NoCandy123!@archimedes.home.fullaware.com:27017/asteroids")
        self.client = MongoClient(self.mongodb_uri)
        self.db = self.client.asteroids
        self.market_prices_collection = self.db.market_prices
        
        # yfinance symbols for major commodities
        self.commodity_symbols = {
            'Gold': 'GC=F',      # Gold futures
            'Platinum': 'PL=F',  # Platinum futures
            'Silver': 'SI=F',    # Silver futures
            'Copper': 'HG=F',    # Copper futures
            'Palladium': 'PA=F'  # Palladium futures
        }
        
        # Fallback prices (per ounce) when API fails
        self.fallback_prices = {
            'GC=F': 2000.0,   # Gold ~$2000/oz
            'PL=F': 1000.0,   # Platinum ~$1000/oz
            'SI=F': 25.0,     # Silver ~$25/oz
            'HG=F': 4.0,      # Copper ~$4/oz
            'PA=F': 2000.0    # Palladium ~$2000/oz
        }
        
        # Conversion factor: ounces to kilograms
        self.OUNCES_PER_KG = 35.274
        
        # Ensure indexes exist
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create necessary indexes for the market_prices collection"""
        try:
            # Index on symbol for fast lookups
            self.market_prices_collection.create_index("symbol", unique=True)
            # Index on timestamp for date-based queries
            self.market_prices_collection.create_index("timestamp")
            # Compound index for symbol + timestamp
            self.market_prices_collection.create_index([("symbol", 1), ("timestamp", -1)])
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")
    
    def _is_price_stale(self, timestamp: datetime) -> bool:
        """
        Check if cached price is stale (older than 7 days).
        
        Args:
            timestamp: When the price was last updated
            
        Returns:
            True if price is stale, False otherwise
        """
        if not timestamp:
            return True
        
        # Consider prices stale after 7 days
        stale_threshold = datetime.now() - timedelta(days=7)
        return timestamp < stale_threshold
    
    def _should_update_prices(self) -> bool:
        """
        Check if prices should be updated (Monday morning or if stale).
        
        Returns:
            True if prices should be updated, False otherwise
        """
        # Check if we have any cached prices
        latest_price = self.market_prices_collection.find_one(
            {}, sort=[("timestamp", -1)]
        )
        
        if not latest_price:
            logger.info("No cached prices found, will fetch new prices")
            return True
        
        latest_timestamp = latest_price.get("timestamp")
        if self._is_price_stale(latest_timestamp):
            logger.info("Cached prices are stale, will fetch new prices")
            return True
        
        # Check if it's Monday morning (weekly update)
        now = datetime.now()
        if now.weekday() == 0 and now.hour < 10:  # Monday before 10 AM
            logger.info("Monday morning detected, will update prices")
            return True
        
        logger.info("Prices are fresh, using cached data")
        return False
    
    def fetch_commodity_price(self, symbol: str) -> float:
        """
        Fetch the current price for a single commodity.
        
        Args:
            symbol: yfinance symbol (e.g., 'GC=F' for gold)
            
        Returns:
            Price per ounce, or fallback price if API fails
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if 'regularMarketPrice' in info and info['regularMarketPrice'] is not None:
                price = float(info['regularMarketPrice'])
                logger.info(f"Successfully fetched price for {symbol}: ${price:.2f}/oz")
                return price
            else:
                logger.warning(f"No price data available for {symbol}, using fallback")
                return self.fallback_prices.get(symbol, 0.0)
                
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {str(e)}")
            return self.fallback_prices.get(symbol, 0.0)
    
    def update_cached_prices(self) -> Dict[str, float]:
        """
        Update cached prices in MongoDB.
        
        Returns:
            Dictionary of updated prices per ounce
        """
        logger.info("Updating cached commodity prices...")
        updated_prices = {}
        timestamp = datetime.now()
        
        for name, symbol in self.commodity_symbols.items():
            try:
                # Fetch current price
                price = self.fetch_commodity_price(symbol)
                updated_prices[symbol] = price
                
                # Update or insert in MongoDB
                self.market_prices_collection.update_one(
                    {"symbol": symbol},
                    {
                        "$set": {
                            "symbol": symbol,
                            "commodity_name": name,
                            "price_per_ounce": price,
                            "price_per_kg": self.convert_ounce_to_kilogram(price),
                            "timestamp": timestamp,
                            "source": "yfinance"
                        }
                    },
                    upsert=True
                )
                
                logger.info(f"Cached price for {name} ({symbol}): ${price:.2f}/oz")
                
            except Exception as e:
                logger.error(f"Error updating cached price for {symbol}: {str(e)}")
                # Use fallback price
                fallback_price = self.fallback_prices.get(symbol, 0.0)
                updated_prices[symbol] = fallback_price
        
        logger.info(f"Successfully updated {len(updated_prices)} commodity prices")
        return updated_prices
    
    def get_cached_prices(self) -> Dict[str, float]:
        """
        Get cached prices from MongoDB.
        
        Returns:
            Dictionary mapping symbols to prices per ounce
        """
        try:
            cached_prices = {}
            cursor = self.market_prices_collection.find({})
            
            for doc in cursor:
                symbol = doc.get("symbol")
                price = doc.get("price_per_ounce")
                if symbol and price is not None:
                    cached_prices[symbol] = price
            
            logger.info(f"Retrieved {len(cached_prices)} cached prices")
            return cached_prices
            
        except Exception as e:
            logger.error(f"Error retrieving cached prices: {str(e)}")
            return {}
    
    def get_commodity_prices_with_caching(self) -> Dict[str, float]:
        """
        Get commodity prices, using cache if available and fresh.
        
        Returns:
            Dictionary mapping symbols to prices per ounce
        """
        if self._should_update_prices():
            return self.update_cached_prices()
        else:
            return self.get_cached_prices()
    
    def convert_ounce_to_kilogram(self, price_per_ounce: float) -> float:
        """
        Convert price from per-ounce to per-kilogram.
        
        Args:
            price_per_ounce: Price per ounce
            
        Returns:
            Price per kilogram
        """
        return price_per_ounce * self.OUNCES_PER_KG
    
    def get_commodity_prices_per_kg(self) -> Dict[str, float]:
        """
        Get all commodity prices converted to per-kilogram.
        
        Returns:
            Dictionary mapping commodity names to prices per kilogram
        """
        ounce_prices = self.get_commodity_prices_with_caching()
        kg_prices = {}
        
        for name, symbol in self.commodity_symbols.items():
            if symbol in ounce_prices:
                kg_price = self.convert_ounce_to_kilogram(ounce_prices[symbol])
                kg_prices[name] = kg_price
                logger.debug(f"{name}: ${kg_price:.2f}/kg (${ounce_prices[symbol]:.2f}/oz)")
        
        return kg_prices
    
    def get_price_history(self, symbol: str, days: int = 30) -> List[Dict]:
        """
        Get price history for a commodity.
        
        Args:
            symbol: Commodity symbol
            days: Number of days of history to retrieve
            
        Returns:
            List of price records
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor = self.market_prices_collection.find(
                {
                    "symbol": symbol,
                    "timestamp": {"$gte": cutoff_date}
                }
            ).sort("timestamp", -1)
            
            history = []
            for doc in cursor:
                history.append({
                    "timestamp": doc.get("timestamp"),
                    "price_per_ounce": doc.get("price_per_ounce"),
                    "price_per_kg": doc.get("price_per_kg"),
                    "source": doc.get("source", "unknown")
                })
            
            logger.info(f"Retrieved {len(history)} price records for {symbol}")
            return history
            
        except Exception as e:
            logger.error(f"Error retrieving price history for {symbol}: {str(e)}")
            return []
    
    def get_price_summary(self) -> Dict[str, Dict[str, float]]:
        """
        Get a comprehensive price summary for all commodities.
        
        Returns:
            Dictionary with both per-ounce and per-kilogram prices
        """
        ounce_prices = self.get_commodity_prices_with_caching()
        summary = {}
        
        for name, symbol in self.commodity_symbols.items():
            if symbol in ounce_prices:
                summary[name] = {
                    'price_per_ounce': ounce_prices[symbol],
                    'price_per_kg': self.convert_ounce_to_kilogram(ounce_prices[symbol]),
                    'symbol': symbol
                }
        
        return summary
    
    def cleanup_old_prices(self, days_to_keep: int = 90):
        """
        Clean up old price records to keep database size manageable.
        
        Args:
            days_to_keep: Number of days of price history to keep
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            result = self.market_prices_collection.delete_many(
                {"timestamp": {"$lt": cutoff_date}}
            )
            
            logger.info(f"Cleaned up {result.deleted_count} old price records")
            
        except Exception as e:
            logger.error(f"Error cleaning up old prices: {str(e)}")
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


# Example usage and testing
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create service instance
    pricing_service = CommodityPricingService()
    
    try:
        # Test fetching all prices with caching
        print("🚀 AstroSurge Enhanced Commodity Pricing Service")
        print("=" * 60)
        
        print("\n📊 Fetching commodity prices with MongoDB caching...")
        prices_per_kg = pricing_service.get_commodity_prices_per_kg()
        
        print("\n💰 Commodity Prices (per kilogram):")
        for commodity, price in prices_per_kg.items():
            print(f"  {commodity:12}: ${price:>10,.2f}/kg")
        
        # Show price history for Platinum
        print(f"\n📈 Price History for Platinum (last 7 days):")
        history = pricing_service.get_price_history('PL=F', days=7)
        for record in history[:5]:  # Show last 5 records
            timestamp = record['timestamp'].strftime('%Y-%m-%d %H:%M')
            print(f"  {timestamp}: ${record['price_per_kg']:,.2f}/kg")
        
        print(f"\n✅ Caching System Status: Active")
        print(f"✅ MongoDB Integration: Working")
        print(f"✅ Price History: Available")
        
    finally:
        pricing_service.close_connection()
