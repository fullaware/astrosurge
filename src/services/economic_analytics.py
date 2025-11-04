"""
Economic Analytics Service for AstroSurge

Provides comprehensive economic analytics including:
- Historical mission performance
- Profit/loss trends
- Commodity price history
- ROI analysis
"""
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.commodity_pricing_standalone import CommodityPricingService

logger = logging.getLogger(__name__)


class EconomicAnalyticsService:
    """
    Economic analytics service for comprehensive financial analysis.
    
    Features:
    - Historical mission performance tracking
    - Profit/loss trend analysis
    - Commodity price history
    - ROI analysis and metrics
    - Time-series data for charts
    """
    
    def __init__(self, mongodb_uri: str = None):
        """Initialize the economic analytics service"""
        # MongoDB connection
        self.mongodb_uri = mongodb_uri or os.getenv("MONGODB_URI")
        if not self.mongodb_uri:
            raise ValueError("MONGODB_URI environment variable not set")
        
        self.client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
        self.db = self.client.asteroids
        
        # Test connection
        try:
            self.client.admin.command('ping')
            logger.info("✅ MongoDB connection successful for Economic Analytics")
        except ConnectionFailure:
            logger.error("❌ MongoDB connection failed for Economic Analytics")
            raise
        
        # Collections
        self.missions = self.db.missions
        self.users = self.db.users
        self.market_prices = self.db.market_prices
        
        # Initialize pricing service
        self.pricing_service = CommodityPricingService()
    
    async def get_historical_mission_performance(self, user_id: Optional[str] = None, 
                                                 limit: int = 50) -> Dict[str, Any]:
        """
        Get historical mission performance data.
        
        Args:
            user_id: Optional user ID to filter missions
            limit: Maximum number of missions to analyze
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            # Build query
            query = {"status": "completed"}
            if user_id:
                query["user_id"] = user_id
            
            # Get completed missions sorted by completion date
            missions = list(self.missions.find(query)
                          .sort("updated_at", -1)
                          .limit(limit))
            
            if not missions:
                return {
                    "total_missions": 0,
                    "successful_missions": 0,
                    "failed_missions": 0,
                    "total_revenue": 0,
                    "total_costs": 0,
                    "total_profit": 0,
                    "average_profit_per_mission": 0,
                    "average_roi": 0,
                    "mission_timeline": []
                }
            
            successful = 0
            failed = 0
            total_revenue = 0
            total_costs = 0
            total_profit = 0
            total_roi = 0
            mission_timeline = []
            
            for mission in missions:
                final_results = mission.get('final_results', {})
                
                if final_results.get('mission_complete', False):
                    successful += 1
                    revenue = final_results.get('cargo_value', 0)
                    costs = final_results.get('total_costs', 0)
                    profit = final_results.get('net_profit', 0)
                    roi = final_results.get('roi_percentage', 0)
                    
                    total_revenue += revenue
                    total_costs += costs
                    total_profit += profit
                    total_roi += roi
                    
                    mission_timeline.append({
                        "mission_id": str(mission['_id']),
                        "mission_name": mission.get('name', 'Unknown'),
                        "completion_date": mission.get('updated_at', datetime.now(timezone.utc)),
                        "revenue": revenue,
                        "costs": costs,
                        "profit": profit,
                        "roi_percentage": roi,
                        "duration_days": mission.get('total_days', 0)
                    })
                else:
                    failed += 1
            
            avg_profit = total_profit / successful if successful > 0 else 0
            avg_roi = total_roi / successful if successful > 0 else 0
            
            return {
                "total_missions": len(missions),
                "successful_missions": successful,
                "failed_missions": failed,
                "success_rate": successful / len(missions) if missions else 0,
                "total_revenue": total_revenue,
                "total_costs": total_costs,
                "total_profit": total_profit,
                "average_profit_per_mission": avg_profit,
                "average_roi": avg_roi,
                "mission_timeline": mission_timeline[:30]  # Last 30 missions
            }
            
        except Exception as e:
            logger.error(f"Error getting historical mission performance: {e}")
            raise
    
    async def get_profit_loss_trends(self, user_id: Optional[str] = None,
                                     days: int = 90) -> Dict[str, Any]:
        """
        Get profit/loss trends over time.
        
        Args:
            user_id: Optional user ID to filter
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend data for charts
        """
        try:
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            query = {
                "status": "completed",
                "updated_at": {"$gte": start_date, "$lte": end_date}
            }
            if user_id:
                query["user_id"] = user_id
            
            missions = list(self.missions.find(query).sort("updated_at", 1))
            
            # Group by time period (weekly)
            weekly_data = {}
            monthly_data = {}
            
            for mission in missions:
                final_results = mission.get('final_results', {})
                if not final_results.get('mission_complete', False):
                    continue
                
                completion_date = mission.get('updated_at', datetime.now(timezone.utc))
                
                # Weekly grouping
                week_key = completion_date.strftime("%Y-W%W")
                if week_key not in weekly_data:
                    weekly_data[week_key] = {
                        "revenue": 0,
                        "costs": 0,
                        "profit": 0,
                        "missions": 0
                    }
                
                weekly_data[week_key]["revenue"] += final_results.get('cargo_value', 0)
                weekly_data[week_key]["costs"] += final_results.get('total_costs', 0)
                weekly_data[week_key]["profit"] += final_results.get('net_profit', 0)
                weekly_data[week_key]["missions"] += 1
                
                # Monthly grouping
                month_key = completion_date.strftime("%Y-%m")
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        "revenue": 0,
                        "costs": 0,
                        "profit": 0,
                        "missions": 0
                    }
                
                monthly_data[month_key]["revenue"] += final_results.get('cargo_value', 0)
                monthly_data[month_key]["costs"] += final_results.get('total_costs', 0)
                monthly_data[month_key]["profit"] += final_results.get('net_profit', 0)
                monthly_data[month_key]["missions"] += 1
            
            # Convert to lists for chart rendering
            weekly_trend = [
                {
                    "period": key,
                    "revenue": data["revenue"],
                    "costs": data["costs"],
                    "profit": data["profit"],
                    "missions": data["missions"]
                }
                for key, data in sorted(weekly_data.items())
            ]
            
            monthly_trend = [
                {
                    "period": key,
                    "revenue": data["revenue"],
                    "costs": data["costs"],
                    "profit": data["profit"],
                    "missions": data["missions"]
                }
                for key, data in sorted(monthly_data.items())
            ]
            
            return {
                "weekly_trend": weekly_trend,
                "monthly_trend": monthly_trend,
                "total_days_analyzed": days,
                "total_missions": len(missions)
            }
            
        except Exception as e:
            logger.error(f"Error getting profit/loss trends: {e}")
            raise
    
    async def get_commodity_price_history(self, days: int = 90) -> Dict[str, Any]:
        """
        Get commodity price history from market_prices collection and current prices.
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            Dictionary with price history data
        """
        try:
            # Get historical prices from database
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # Query market prices collection
            price_history = list(
                self.market_prices.find({
                    "last_updated": {"$gte": start_date, "$lte": end_date}
                }).sort("last_updated", 1)
            )
            
            # Get current prices
            current_prices = self.pricing_service.get_commodity_prices_per_kg()
            
            # Organize by commodity
            commodities = ['Gold', 'Platinum', 'Silver', 'Copper', 'Palladium']
            price_data = {}
            
            for commodity in commodities:
                price_data[commodity] = {
                    "current_price": current_prices.get(commodity, 0),
                    "history": []
                }
                
                # Extract historical prices for this commodity
                for price_record in price_history:
                    if price_record.get('element') == commodity:
                        price_data[commodity]["history"].append({
                            "date": price_record.get('last_updated'),
                            "price": price_record.get('price_per_kg', 0)
                        })
            
            # Calculate price changes
            price_changes = {}
            for commodity in commodities:
                history = price_data[commodity]["history"]
                if len(history) >= 2:
                    old_price = history[0]["price"]
                    new_price = history[-1]["price"]
                    if old_price > 0:
                        change_percent = ((new_price - old_price) / old_price) * 100
                        price_changes[commodity] = {
                            "change_percent": change_percent,
                            "old_price": old_price,
                            "new_price": new_price
                        }
                else:
                    price_changes[commodity] = {
                        "change_percent": 0,
                        "old_price": current_prices.get(commodity, 0),
                        "new_price": current_prices.get(commodity, 0)
                    }
            
            return {
                "commodities": price_data,
                "price_changes": price_changes,
                "last_updated": datetime.now(timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"Error getting commodity price history: {e}")
            # Fallback to current prices only
            current_prices = self.pricing_service.get_commodity_prices_per_kg()
            return {
                "commodities": {
                    commodity: {
                        "current_price": current_prices.get(commodity, 0),
                        "history": []
                    }
                    for commodity in ['Gold', 'Platinum', 'Silver', 'Copper', 'Palladium']
                },
                "price_changes": {},
                "last_updated": datetime.now(timezone.utc)
            }
    
    async def get_roi_analysis(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive ROI analysis.
        
        Args:
            user_id: Optional user ID to filter
            
        Returns:
            Dictionary with ROI metrics
        """
        try:
            query = {"status": "completed"}
            if user_id:
                query["user_id"] = user_id
            
            missions = list(self.missions.find(query))
            
            if not missions:
                return {
                    "total_missions": 0,
                    "average_roi": 0,
                    "median_roi": 0,
                    "best_roi": 0,
                    "worst_roi": 0,
                    "roi_distribution": [],
                    "roi_by_mission_type": {}
                }
            
            rois = []
            mission_rois = []
            
            for mission in missions:
                final_results = mission.get('final_results', {})
                if final_results.get('mission_complete', False):
                    roi = final_results.get('roi_percentage', 0)
                    rois.append(roi)
                    
                    mission_rois.append({
                        "mission_id": str(mission['_id']),
                        "mission_name": mission.get('name', 'Unknown'),
                        "roi": roi,
                        "profit": final_results.get('net_profit', 0),
                        "costs": final_results.get('total_costs', 0),
                        "revenue": final_results.get('cargo_value', 0)
                    })
            
            if not rois:
                return {
                    "total_missions": 0,
                    "average_roi": 0,
                    "median_roi": 0,
                    "best_roi": 0,
                    "worst_roi": 0,
                    "roi_distribution": [],
                    "roi_by_mission_type": {}
                }
            
            rois_sorted = sorted(rois)
            
            avg_roi = sum(rois) / len(rois)
            median_roi = rois_sorted[len(rois_sorted) // 2] if rois_sorted else 0
            best_roi = max(rois) if rois else 0
            worst_roi = min(rois) if rois else 0
            
            # ROI distribution (buckets)
            roi_buckets = {
                "negative": sum(1 for r in rois if r < 0),
                "0-50": sum(1 for r in rois if 0 <= r < 50),
                "50-100": sum(1 for r in rois if 50 <= r < 100),
                "100-200": sum(1 for r in rois if 100 <= r < 200),
                "200+": sum(1 for r in rois if r >= 200)
            }
            
            return {
                "total_missions": len(mission_rois),
                "average_roi": avg_roi,
                "median_roi": median_roi,
                "best_roi": best_roi,
                "worst_roi": worst_roi,
                "roi_distribution": roi_buckets,
                "top_missions": sorted(mission_rois, key=lambda x: x['roi'], reverse=True)[:10],
                "mission_rois": mission_rois[:50]  # Limit for performance
            }
            
        except Exception as e:
            logger.error(f"Error getting ROI analysis: {e}")
            raise
    
    async def get_economic_dashboard_data(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all economic analytics data for dashboard.
        
        Args:
            user_id: Optional user ID to filter
            
        Returns:
            Comprehensive economic analytics dictionary
        """
        try:
            historical_performance = await self.get_historical_mission_performance(user_id)
            profit_loss_trends = await self.get_profit_loss_trends(user_id)
            price_history = await self.get_commodity_price_history()
            roi_analysis = await self.get_roi_analysis(user_id)
            
            return {
                "historical_performance": historical_performance,
                "profit_loss_trends": profit_loss_trends,
                "commodity_price_history": price_history,
                "roi_analysis": roi_analysis,
                "generated_at": datetime.now(timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"Error getting economic dashboard data: {e}")
            raise

