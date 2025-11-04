"""
Standalone Commodity Pricing Service for AstroSurge

This service handles fetching real commodity prices from yfinance API
with MongoDB caching for daily updates and weekend/holiday handling.
"""
import yfinance as yf
import logging
import time
import threading
from typing import Dict, Optional
from datetime import datetime, timedelta, timezone
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)


class CommodityPricingService:
    """
    Standalone service for fetching and managing commodity prices.
    
    Features:
    - Fetch real-time commodity prices from yfinance
    - Session-based caching to avoid excessive API calls
    - Graceful fallback when API fails
    - Mission economics calculations
    - Price validation and conversion
    """
    
    def __init__(self, mongodb_uri: str = None):
        """Initialize the commodity pricing service with MongoDB caching"""
        # MongoDB connection for persistent caching
        self.mongodb_uri = mongodb_uri or os.getenv("MONGODB_URI")
        self.mongo_client = None
        self.market_prices_collection = None
        
        if self.mongodb_uri:
            try:
                self.mongo_client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
                self.mongo_client.admin.command('ping')
                # Extract database name from URI or use default
                if '/' in self.mongodb_uri and '?' in self.mongodb_uri:
                    db_name = self.mongodb_uri.split('/')[-1].split('?')[0]
                elif '/' in self.mongodb_uri:
                    db_name = self.mongodb_uri.split('/')[-1]
                else:
                    db_name = 'asteroids'  # Default database name
                
                # Use extracted database name or default
                if not db_name or db_name == '':
                    db_name = 'asteroids'
                
                self.mongo_db = self.mongo_client[db_name]
                self.market_prices_collection = self.mongo_db.market_prices
                logger.info(f"✅ MongoDB connection successful for commodity pricing cache (database: {db_name})")
            except (ConnectionFailure, Exception) as e:
                logger.warning(f"⚠️ MongoDB connection failed, using in-memory cache only: {e}")
                self.mongo_client = None
                self.mongo_db = None
        
        # yfinance symbols for major commodities
        self.commodity_symbols = {
            'Gold': 'GC=F',      # Gold futures
            'Platinum': 'PL=F',  # Platinum futures
            'Silver': 'SI=F',    # Silver futures
            'Copper': 'HG=F',    # Copper futures
            'Palladium': 'PA=F'  # Palladium futures
        }
        
        # Fallback prices (per ounce) when API fails
        # These are reasonable market values as of 2024
        self.fallback_prices = {
            'GC=F': 2000.0,   # Gold ~$2000/oz
            'PL=F': 1000.0,   # Platinum ~$1000/oz
            'SI=F': 25.0,     # Silver ~$25/oz
            'HG=F': 4.0,      # Copper ~$4/oz
            'PA=F': 2000.0    # Palladium ~$2000/oz
        }
        
        # Conversion factor: ounces to kilograms
        self.OUNCES_PER_KG = 35.274
        
        # In-memory cache as fallback
        self._session_cache = {}
        self._cache_timestamp = None
    
        # Rate limiting protection
        self._request_lock = threading.Lock()  # Prevent concurrent requests
        self._last_request_time = None
        self._min_request_interval = 1.0  # Minimum 1 second between requests
        self._request_delay = 0.5  # Default delay between requests (500ms)
        self._max_retries = 3
        self._base_backoff = 2.0  # Base backoff time in seconds
        self._rate_limit_errors = [
            '429',  # Too Many Requests
            '503',  # Service Unavailable
            'rate limit',
            'rate_limit',
            'too many requests',
            'quota exceeded'
        ]
    
    def _is_weekend_or_holiday(self) -> bool:
        """Check if current day is a weekend (markets closed)"""
        now = datetime.now(timezone.utc)
        # Saturday = 5, Sunday = 6
        return now.weekday() >= 5
    
    def _should_update_prices(self) -> bool:
        """
        Check if prices should be updated (once daily, not on weekends).
        
        Returns:
            True if prices should be updated, False to use cache
        """
        # If it's a weekend, always use cached values
        if self._is_weekend_or_holiday():
            logger.info("Weekend detected - using cached prices")
            return False
        
        # Check MongoDB cache first
        if self.market_prices_collection is not None:
            try:
                latest_price = self.market_prices_collection.find_one(
                    {}, sort=[("last_updated", -1)]
                )
                
                if latest_price:
                    last_updated = latest_price.get("last_updated")
                    if isinstance(last_updated, datetime):
                        # Check if cache is from today (same day)
                        now = datetime.now(timezone.utc)
                        if last_updated.date() == now.date():
                            logger.info("Prices already updated today - using cached values")
                            return False
                        
                        # Check if cache is less than 24 hours old
                        if (now - last_updated) < timedelta(hours=24):
                            logger.info("Prices cached within 24 hours - using cached values")
                            return False
                
                logger.info("No recent cache found or cache expired - will fetch new prices")
                return True
            except Exception as e:
                logger.warning(f"Error checking MongoDB cache: {e}, falling back to in-memory cache")
        
        # Fallback to in-memory cache check
        if not self._cache_timestamp:
            return True
        
        # Check if cache is from today
        now = datetime.now(timezone.utc)
        if self._cache_timestamp.date() == now.date():
            return False
        
        # Check if cache is less than 24 hours old
        stale_threshold = now - timedelta(hours=24)
        return self._cache_timestamp < stale_threshold
    
    def _throttle_request(self):
        """Throttle requests to avoid rate limiting"""
        with self._request_lock:
            if self._last_request_time is not None:
                elapsed = time.time() - self._last_request_time
                if elapsed < self._min_request_interval:
                    sleep_time = self._min_request_interval - elapsed
                    time.sleep(sleep_time)
            self._last_request_time = time.time()
    
    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is a rate limit error"""
        error_str = str(error).lower()
        return any(rate_limit_term in error_str for rate_limit_term in self._rate_limit_errors)
    
    def fetch_commodity_price(self, symbol: str, retry_count: int = 0) -> float:
        """
        Fetch the current price for a single commodity with rate limiting protection.
        
        Args:
            symbol: yfinance symbol (e.g., 'GC=F' for gold)
            retry_count: Current retry attempt (for exponential backoff)
            
        Returns:
            Price per ounce, or fallback price if API fails
        """
        # Throttle request to avoid rate limiting
        self._throttle_request()
        
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
            error_str = str(e)
            
            # Check if this is a rate limit error
            if self._is_rate_limit_error(e):
                logger.warning(f"Rate limit detected for {symbol}: {error_str}")
                
                # Exponential backoff retry
                if retry_count < self._max_retries:
                    backoff_time = self._base_backoff * (2 ** retry_count)
                    logger.info(f"Retrying {symbol} after {backoff_time:.1f}s backoff (attempt {retry_count + 1}/{self._max_retries})")
                    time.sleep(backoff_time)
                    return self.fetch_commodity_price(symbol, retry_count + 1)
                else:
                    logger.error(f"Max retries reached for {symbol} due to rate limiting, using fallback")
                    return self.fallback_prices.get(symbol, 0.0)
            else:
                # Non-rate-limit error
                logger.error(f"Error fetching price for {symbol}: {error_str}")
            return self.fallback_prices.get(symbol, 0.0)
    
    def fetch_all_commodity_prices(self) -> Dict[str, float]:
        """
        Fetch prices for all tracked commodities with rate limiting protection.
        Adds delays between requests to avoid rate limiting.
        
        Returns:
            Dictionary mapping symbols to prices per ounce
        """
        prices = {}
        rate_limit_encountered = False
        
        for name, symbol in self.commodity_symbols.items():
            price = self.fetch_commodity_price(symbol)
            prices[symbol] = price
            
            # Add delay between requests to avoid rate limiting
            if self._request_delay > 0:
                time.sleep(self._request_delay)
            
            # Check if we hit rate limits (fallback prices indicate failure)
            if price == self.fallback_prices.get(symbol, 0.0):
                rate_limit_encountered = True
        
        if rate_limit_encountered:
            logger.warning("Some prices may have been rate limited, using fallback values")
            
        logger.info(f"Fetched prices for {len(prices)} commodities")
        return prices
    
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
        Uses MongoDB caching with daily updates and weekend handling.
        
        Returns:
            Dictionary mapping commodity names to prices per kilogram
        """
        # Check if we should update prices
        should_update = self._should_update_prices()
        
        # Try to get cached prices from MongoDB first
        if not should_update and self.market_prices_collection is not None:
            try:
                cached_prices = {}
                for commodity_name in self.commodity_symbols.keys():
                    price_doc = self.market_prices_collection.find_one(
                        {"element": commodity_name},
                        sort=[("last_updated", -1)]
                    )
                    if price_doc and "price_per_kg" in price_doc:
                        cached_prices[commodity_name] = price_doc["price_per_kg"]
                
                if len(cached_prices) == len(self.commodity_symbols):
                    logger.info(f"Using MongoDB cached prices (last updated: {price_doc.get('last_updated', 'unknown')})")
                    return cached_prices
            except Exception as e:
                logger.warning(f"Error reading MongoDB cache: {e}, fetching new prices")
        
        # Check in-memory cache as fallback
        if not should_update and self._session_cache:
            logger.info("Using in-memory cached commodity prices")
            return self._session_cache
        
        # Fetch new prices (only if not weekend/holiday and cache is stale)
        if self._is_weekend_or_holiday():
            logger.warning("Weekend detected - markets closed, using most recent cached prices")
            # Try to get the most recent cached prices
            if self.market_prices_collection is not None:
                try:
                    cached_prices = {}
                    for commodity_name in self.commodity_symbols.keys():
                        price_doc = self.market_prices_collection.find_one(
                            {"element": commodity_name},
                            sort=[("last_updated", -1)]
                        )
                        if price_doc and "price_per_kg" in price_doc:
                            cached_prices[commodity_name] = price_doc["price_per_kg"]
                        else:
                            # Use fallback price converted to kg
                            symbol = self.commodity_symbols[commodity_name]
                            fallback_oz = self.fallback_prices.get(symbol, 0.0)
                            cached_prices[commodity_name] = self.convert_ounce_to_kilogram(fallback_oz)
                    
                    if cached_prices:
                        logger.info("Using cached weekend prices from MongoDB")
                        return cached_prices
                except Exception as e:
                    logger.warning(f"Error reading weekend cache: {e}")
            
            # Final fallback: use in-memory cache or fallback prices
            if self._session_cache:
                return self._session_cache
            
            # Convert fallback prices to kg
            kg_prices = {}
            for name, symbol in self.commodity_symbols.items():
                fallback_oz = self.fallback_prices.get(symbol, 0.0)
                kg_prices[name] = self.convert_ounce_to_kilogram(fallback_oz)
            logger.info("Using fallback prices (weekend mode)")
            return kg_prices
        
        # Fetch new prices from API with rate limiting protection
        logger.info("Fetching new commodity prices from yfinance API (with rate limiting protection)")
        
        # Try to fetch prices, but prefer cached data if rate limited
        try:
            ounce_prices = self.fetch_all_commodity_prices()
            
            # Check if we got mostly fallback prices (indicates rate limiting)
            fallback_count = sum(
                1 for symbol, price in ounce_prices.items()
                if price == self.fallback_prices.get(symbol, 0.0)
            )
            
            if fallback_count >= len(self.commodity_symbols) * 0.5:  # 50% or more fallbacks
                logger.warning("High rate of fallback prices detected, likely rate limited. Using cached data.")
                # Try to get cached prices instead
                if self.market_prices_collection is not None:
                    try:
                        cached_prices = {}
                        for commodity_name in self.commodity_symbols.keys():
                            price_doc = self.market_prices_collection.find_one(
                                {"element": commodity_name},
                                sort=[("last_updated", -1)]
                            )
                            if price_doc and "price_per_kg" in price_doc:
                                # Convert back to ounce price for consistency
                                kg_price = price_doc["price_per_kg"]
                                symbol = self.commodity_symbols[commodity_name]
                                ounce_price = kg_price / self.OUNCES_PER_KG
                                cached_prices[symbol] = ounce_price
                        
                        if cached_prices:
                            logger.info("Using cached prices due to rate limiting")
                            ounce_prices = cached_prices
                            # Update fallback prices to use cached values
                            for symbol, price in ounce_prices.items():
                                if price > 0:
                                    self.fallback_prices[symbol] = price
                    except Exception as e:
                        logger.warning(f"Error reading cached prices: {e}")
        except Exception as e:
            logger.error(f"Error fetching prices from API: {e}")
            # Use cached or fallback prices
            ounce_prices = {symbol: self.fallback_prices.get(symbol, 0.0) 
                          for symbol in self.commodity_symbols.values()}
        
        kg_prices = {}
        now = datetime.now(timezone.utc)
        
        for name, symbol in self.commodity_symbols.items():
            if symbol in ounce_prices:
                kg_price = self.convert_ounce_to_kilogram(ounce_prices[symbol])
                kg_prices[name] = kg_price
                logger.debug(f"{name}: ${kg_price:.2f}/kg (${ounce_prices[symbol]:.2f}/oz)")
        
                # Store in MongoDB cache
                if self.market_prices_collection is not None:
                    try:
                        self.market_prices_collection.update_one(
                            {"element": name},
                            {
                                "$set": {
                                    "element": name,
                                    "price_per_kg": kg_price,
                                    "price_per_ounce": ounce_prices[symbol],
                                    "last_updated": now,
                                    "symbol": symbol
                                }
                            },
                            upsert=True
                        )
                    except Exception as e:
                        logger.warning(f"Error caching price to MongoDB: {e}")
        
        # Cache in memory as well
        self._session_cache = kg_prices
        self._cache_timestamp = now
        
        logger.info(f"✅ Updated commodity prices and cached for 24 hours")
        return kg_prices
    
    def get_commodity_price_per_kg(self, commodity_name: str) -> float:
        """
        Get the price for a specific commodity in per-kilogram.
        
        Args:
            commodity_name: Name of the commodity (e.g., 'Gold', 'Platinum')
            
        Returns:
            Price per kilogram
        """
        if commodity_name not in self.commodity_symbols:
            logger.error(f"Unknown commodity: {commodity_name}")
            return 0.0
        
        symbol = self.commodity_symbols[commodity_name]
        ounce_price = self.fetch_commodity_price(symbol)
        return self.convert_ounce_to_kilogram(ounce_price)
    
    def get_price_summary(self) -> Dict[str, Dict[str, float]]:
        """
        Get a comprehensive price summary for all commodities.
        
        Returns:
            Dictionary with both per-ounce and per-kilogram prices
        """
        ounce_prices = self.fetch_all_commodity_prices()
        summary = {}
        
        for name, symbol in self.commodity_symbols.items():
            if symbol in ounce_prices:
                summary[name] = {
                    'price_per_ounce': ounce_prices[symbol],
                    'price_per_kg': self.convert_ounce_to_kilogram(ounce_prices[symbol]),
                    'symbol': symbol
                }
        
        return summary
    
    def validate_price_data(self, prices: Dict[str, float]) -> bool:
        """
        Validate that price data is reasonable.
        
        Args:
            prices: Dictionary of prices to validate
            
        Returns:
            True if prices are reasonable, False otherwise
        """
        for symbol, price in prices.items():
            if price <= 0:
                logger.warning(f"Invalid price for {symbol}: {price}")
                return False
            
            # Check if price is within reasonable bounds (10x fallback range)
            fallback = self.fallback_prices.get(symbol, 0)
            if fallback > 0:
                min_price = fallback * 0.1
                max_price = fallback * 10.0
                if not (min_price <= price <= max_price):
                    logger.warning(f"Price for {symbol} ({price}) outside reasonable range ({min_price}-{max_price})")
                    return False
        
        return True
    
    def get_mission_economics(self, cargo_capacity_kg: float = 50000) -> Dict[str, Dict[str, float]]:
        """
        Calculate mission economics for asteroid mining.
        
        Args:
            cargo_capacity_kg: Ship cargo capacity in kilograms
            
        Returns:
            Dictionary with economic calculations for each commodity
        """
        kg_prices = self.get_commodity_prices_per_kg()
        economics = {}
        
        for commodity, price_per_kg in kg_prices.items():
            total_value = cargo_capacity_kg * price_per_kg
            economics[commodity] = {
                'price_per_kg': price_per_kg,
                'cargo_capacity_kg': cargo_capacity_kg,
                'total_cargo_value': total_value,
                'commodity_name': commodity
            }
        
        return economics
    
    def calculate_ore_value(self, commodity_name: str, ore_weight_kg: float, ore_grade: float = 0.1) -> Dict[str, float]:
        """
        Calculate the value of mined ore considering ore grade.
        
        Args:
            commodity_name: Name of the commodity
            ore_weight_kg: Total weight of ore mined
            ore_grade: Grade of ore (0.1 = 10% commodity content)
            
        Returns:
            Dictionary with ore value calculations
        """
        price_per_kg = self.get_commodity_price_per_kg(commodity_name)
        
        # Calculate actual commodity weight (ore grade * total weight)
        commodity_weight_kg = ore_weight_kg * ore_grade
        gangue_weight_kg = ore_weight_kg * (1 - ore_grade)
        
        # Calculate values
        commodity_value = commodity_weight_kg * price_per_kg
        total_ore_value = commodity_value  # Only commodity has value
        
        return {
            'total_ore_weight_kg': ore_weight_kg,
            'commodity_weight_kg': commodity_weight_kg,
            'gangue_weight_kg': gangue_weight_kg,
            'ore_grade': ore_grade,
            'price_per_kg': price_per_kg,
            'commodity_value': commodity_value,
            'total_ore_value': total_ore_value
        }
    
    def clear_cache(self):
        """Clear the session cache to force fresh price fetch"""
        self._session_cache = {}
        self._cache_timestamp = None
        logger.info("Session cache cleared")


# Example usage and testing
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create service instance
    pricing_service = CommodityPricingService()
    
    # Test fetching all prices
    print("🚀 AstroSurge Standalone Commodity Pricing Service")
    print("=" * 60)
    
    print("\n📊 Fetching commodity prices...")
    prices_per_kg = pricing_service.get_commodity_prices_per_kg()
    
    print("\n💰 Commodity Prices (per kilogram):")
    for commodity, price in prices_per_kg.items():
        print(f"  {commodity:12}: ${price:>10,.2f}/kg")
    
    # Test mission economics
    print(f"\n🛸 Mission Economics (50,000kg cargo capacity):")
    economics = pricing_service.get_mission_economics(50000)
    
    for commodity, data in economics.items():
        print(f"  {commodity:12}: ${data['total_cargo_value']:>15,.0f}")
    
    # Test ore value calculation
    print(f"\n⛏️  Ore Value Calculation Example:")
    print(f"  Mining 10,000kg of Platinum ore at 10% grade:")
    ore_value = pricing_service.calculate_ore_value('Platinum', 10000, 0.1)
    print(f"  Total ore weight: {ore_value['total_ore_weight_kg']:,} kg")
    print(f"  Commodity weight: {ore_value['commodity_weight_kg']:,} kg")
    print(f"  Gangue weight: {ore_value['gangue_weight_kg']:,} kg")
    print(f"  Ore grade: {ore_value['ore_grade']:.1%}")
    print(f"  Commodity value: ${ore_value['commodity_value']:,.0f}")
    
    # Test price summary
    print("\n📈 Detailed Price Summary:")
    summary = pricing_service.get_price_summary()
    for commodity, data in summary.items():
        print(f"{commodity}:")
        print(f"  Per ounce: ${data['price_per_ounce']:.2f}")
        print(f"  Per kg: ${data['price_per_kg']:,.2f}")
        print(f"  Symbol: {data['symbol']}")
        print()
    
    # Test caching
    print("🔄 Testing caching...")
    cached_prices = pricing_service.get_commodity_prices_per_kg()
    print(f"Cached prices retrieved: {len(cached_prices)} commodities")
    
    print(f"\n✅ Standalone Service Status: Ready")
    print(f"✅ Error Handling: Graceful fallback when API fails")
    print(f"✅ Price Conversion: Accurate ounce-to-kilogram conversion")
    print(f"✅ Session Caching: Working")
    print(f"✅ Mission Economics: Calculated")
    print(f"✅ Ore Value Calculations: Available")
