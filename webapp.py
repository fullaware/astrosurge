"""
Flask API endpoints for AstroSurge Visualization Dashboard
"""
from flask import Flask, jsonify, render_template, request
import logging
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.visualization import AstroSurgeVisualizationService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Initialize visualization service
viz_service = AstroSurgeVisualizationService()

def get_api_base_url():
    """Get API base URL from environment variables.
    Prefers API_BASE_URL if set, otherwise constructs from API_PORT.
    In Docker, uses service name 'api', otherwise 'localhost'."""
    api_base_url = os.getenv("API_BASE_URL")
    if api_base_url:
        return api_base_url
    
    # Construct from port number
    api_port = os.getenv("API_PORT", "8000")
    # In Docker Compose, use service name; otherwise use localhost
    api_host = os.getenv("API_HOST", "localhost")
    return f"http://{api_host}:{api_port}/api"

@app.route('/')
def index():
    """Serve the main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/dashboard')
def get_dashboard():
    """Get comprehensive dashboard data"""
    try:
        user_id = request.args.get('user_id')
        dashboard_data = viz_service.get_dashboard_data(user_id)
        return jsonify(dashboard_data)
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({'error': 'Failed to get dashboard data'}), 500

@app.route('/api/missions', methods=['GET'])
def get_missions():
    """Get mission data - proxy to FastAPI backend"""
    try:
        import requests
        api_base_url = get_api_base_url()
        user_id = request.args.get('user_id')
        params = {'user_id': user_id} if user_id else {}
        response = requests.get(f"{api_base_url}/missions", params=params, timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            logger.error(f"FastAPI missions GET endpoint returned {response.status_code}")
            # Fallback to visualization service
            try:
                mission_data = viz_service._get_mission_data(user_id)
                if isinstance(mission_data, dict) and 'missions' in mission_data:
                    return jsonify(mission_data['missions'])
                elif isinstance(mission_data, list):
                    return jsonify(mission_data)
            except:
                pass
            return jsonify([])
    except Exception as e:
        logger.error(f"Error getting missions: {str(e)}")
        return jsonify([])

@app.route('/api/missions', methods=['POST'])
def create_mission():
    """Create a new mission - proxy to FastAPI backend"""
    try:
        import requests
        api_base_url = get_api_base_url()
        mission_data = request.get_json()
        response = requests.post(f"{api_base_url}/missions", json=mission_data, timeout=10)
        if response.status_code == 200 or response.status_code == 201:
            return jsonify(response.json()), response.status_code
        else:
            logger.error(f"FastAPI missions POST endpoint returned {response.status_code}")
            error_detail = response.json().get('detail', 'Failed to create mission') if response.content else 'Failed to create mission'
            return jsonify({'error': error_detail}), response.status_code
    except Exception as e:
        logger.error(f"Error creating mission: {str(e)}")
        return jsonify({'error': 'Failed to create mission'}), 500

@app.route('/api/ships', methods=['GET'])
def get_ships():
    """Get ships data - proxy to FastAPI backend"""
    try:
        import requests
        api_base_url = get_api_base_url()
        user_id = request.args.get('user_id')
        params = {'user_id': user_id} if user_id else {}
        response = requests.get(f"{api_base_url}/ships", params=params, timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            logger.error(f"FastAPI ships endpoint returned {response.status_code}")
            return jsonify([])
    except Exception as e:
        logger.error(f"Error getting ships: {str(e)}")
        return jsonify([])

@app.route('/api/ships/purchase', methods=['POST'])
def purchase_ship():
    """Purchase a new ship - proxy to FastAPI backend"""
    try:
        import requests
        api_base_url = get_api_base_url()
        ship_data = request.get_json()
        response = requests.post(f"{api_base_url}/ships/purchase", json=ship_data, timeout=10)
        if response.status_code == 200 or response.status_code == 201:
            return jsonify(response.json()), response.status_code
        else:
            logger.error(f"FastAPI ships/purchase endpoint returned {response.status_code}")
            error_detail = response.json().get('detail', 'Failed to purchase ship') if response.content else 'Failed to purchase ship'
            return jsonify({'error': error_detail}), response.status_code
    except Exception as e:
        logger.error(f"Error purchasing ship: {str(e)}")
        return jsonify({'error': 'Failed to purchase ship'}), 500

@app.route('/api/financing/calculate')
def calculate_financing():
    """Calculate financing needs - proxy to FastAPI backend"""
    try:
        import requests
        api_base_url = get_api_base_url()
        # Pass through all query parameters
        params = dict(request.args)
        response = requests.get(f"{api_base_url}/financing/calculate", params=params, timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            logger.error(f"FastAPI financing/calculate endpoint returned {response.status_code}")
            return jsonify({'error': 'Failed to calculate financing'}), response.status_code
    except Exception as e:
        logger.error(f"Error calculating financing: {str(e)}")
        return jsonify({'error': 'Failed to calculate financing'}), 500

@app.route('/api/financing/options')
def get_financing_options():
    """Get financing options - proxy to FastAPI backend"""
    try:
        import requests
        api_base_url = get_api_base_url()
        response = requests.get(f"{api_base_url}/financing/options", timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'default_apr': 8.0})
    except Exception as e:
        logger.error(f"Error getting financing options: {str(e)}")
        return jsonify({'default_apr': 8.0})

@app.route('/api/financing/loans', methods=['POST'])
def create_loan():
    """Create a new loan - proxy to FastAPI backend"""
    try:
        import requests
        api_base_url = get_api_base_url()
        loan_data = request.get_json()
        response = requests.post(f"{api_base_url}/financing/loans", json=loan_data, timeout=10)
        if response.status_code == 200 or response.status_code == 201:
            return jsonify(response.json()), response.status_code
        else:
            logger.error(f"FastAPI financing/loans endpoint returned {response.status_code}")
            error_detail = response.json().get('detail', 'Failed to create loan') if response.content else 'Failed to create loan'
            return jsonify({'error': error_detail}), response.status_code
    except Exception as e:
        logger.error(f"Error creating loan: {str(e)}")
        return jsonify({'error': 'Failed to create loan'}), 500

@app.route('/api/missions/budget-estimate')
def get_budget_estimate():
    """Get budget estimate - proxy to FastAPI backend"""
    try:
        import requests
        api_base_url = get_api_base_url()
        # Pass through all query parameters
        params = dict(request.args)
        response = requests.get(f"{api_base_url}/missions/budget-estimate", params=params, timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            logger.error(f"FastAPI budget-estimate endpoint returned {response.status_code}")
            return jsonify({'error': 'Failed to calculate budget estimate'}), response.status_code
    except Exception as e:
        logger.error(f"Error calculating budget estimate: {str(e)}")
        return jsonify({'error': 'Failed to calculate budget estimate'}), 500

@app.route('/api/missions/readiness')
def check_mission_readiness():
    """Check mission readiness - proxy to FastAPI backend"""
    try:
        import requests
        api_base_url = get_api_base_url()
        # Pass through all query parameters
        params = dict(request.args)
        response = requests.get(f"{api_base_url}/missions/readiness", params=params, timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            logger.error(f"FastAPI readiness endpoint returned {response.status_code}")
            return jsonify({'error': 'Failed to check readiness'}), response.status_code
    except Exception as e:
        logger.error(f"Error checking readiness: {str(e)}")
        return jsonify({'error': 'Failed to check readiness'}), 500

@app.route('/api/missions/<mission_id>/results')
def get_mission_results(mission_id):
    """Get detailed mission results - proxy to FastAPI backend"""
    try:
        import requests
        api_base_url = get_api_base_url()
        url = f"{api_base_url}/missions/{mission_id}/results"
        logger.info(f"Proxying mission results request to: {url}")
        response = requests.get(url, timeout=10)
        logger.info(f"FastAPI response status: {response.status_code}")
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            logger.error(f"FastAPI mission results endpoint returned {response.status_code}: {response.text}")
            try:
                error_detail = response.json().get('detail', 'Failed to get mission results')
            except:
                error_detail = response.text or 'Failed to get mission results'
            return jsonify({'error': error_detail}), response.status_code
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error to FastAPI: {str(e)}")
        return jsonify({'error': 'Failed to connect to API service'}), 503
    except Exception as e:
        logger.error(f"Error getting mission results: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to get mission results: {str(e)}'}), 500

@app.route('/api/missions/<mission_id>')
def get_mission_details(mission_id):
    """Get detailed mission information"""
    try:
        mission_details = viz_service.get_mission_details(mission_id)
        return jsonify(mission_details)
    except Exception as e:
        logger.error(f"Error getting mission details: {str(e)}")
        return jsonify({'error': 'Failed to get mission details'}), 500

@app.route('/api/asteroids')
def get_asteroids():
    """Get asteroid data - proxy to FastAPI backend"""
    try:
        import requests
        api_base_url = get_api_base_url()
        limit = int(request.args.get('limit', 20))
        params = {'limit': limit, 'skip': 0}
        response = requests.get(f"{api_base_url}/asteroids", params=params, timeout=5)
        if response.status_code == 200:
            asteroids = response.json()
            # FastAPI returns a list directly, but handle object format too
            if isinstance(asteroids, list):
                return jsonify(asteroids)
            elif isinstance(asteroids, dict) and 'asteroids' in asteroids:
                return jsonify(asteroids['asteroids'])
            else:
                return jsonify([])
        else:
            logger.error(f"FastAPI asteroids endpoint returned {response.status_code}")
            return jsonify([])
    except Exception as e:
        logger.error(f"Error getting asteroids: {str(e)}")
        # Fallback to visualization service
        try:
            limit = int(request.args.get('limit', 20))
            asteroid_data = viz_service._get_asteroid_data()
            if isinstance(asteroid_data, dict) and 'asteroids' in asteroid_data:
                asteroids = asteroid_data['asteroids'][:limit]
                return jsonify(asteroids)
            elif isinstance(asteroid_data, list):
                return jsonify(asteroid_data[:limit])
        except:
            pass
        return jsonify([])

@app.route('/api/asteroids/<asteroid_id>/details')
def get_asteroid_details(asteroid_id):
    """Get comprehensive asteroid details - proxy to FastAPI backend"""
    try:
        import requests
        api_base_url = get_api_base_url()
        response = requests.get(f"{api_base_url}/asteroids/{asteroid_id}/details", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            logger.error(f"FastAPI asteroid details endpoint returned {response.status_code}")
            return jsonify({'error': 'Failed to get asteroid details'}), response.status_code
    except Exception as e:
        logger.error(f"Error getting asteroid details: {str(e)}")
        return jsonify({'error': 'Failed to get asteroid details'}), 500

@app.route('/api/asteroids/<asteroid_id>/mining-analysis')
def get_asteroid_mining_analysis(asteroid_id):
    """Get asteroid mining analysis - proxy to FastAPI backend"""
    try:
        import requests
        api_base_url = get_api_base_url()
        response = requests.get(f"{api_base_url}/asteroids/{asteroid_id}/mining-analysis", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            logger.error(f"FastAPI mining analysis endpoint returned {response.status_code}")
            return jsonify({'error': 'Failed to get mining analysis'}), response.status_code
    except Exception as e:
        logger.error(f"Error getting mining analysis: {str(e)}")
        return jsonify({'error': 'Failed to get mining analysis'}), 500

@app.route('/api/asteroids/<asteroid_name>')
def get_asteroid_analysis(asteroid_name):
    """Get detailed asteroid analysis"""
    try:
        asteroid_analysis = viz_service.get_asteroid_analysis(asteroid_name)
        return jsonify(asteroid_analysis)
    except Exception as e:
        logger.error(f"Error getting asteroid analysis: {str(e)}")
        return jsonify({'error': 'Failed to get asteroid analysis'}), 500

@app.route('/api/fleet')
def get_fleet():
    """Get fleet data"""
    try:
        user_id = request.args.get('user_id')
        fleet_data = viz_service._get_fleet_data(user_id)
        return jsonify(fleet_data)
    except Exception as e:
        logger.error(f"Error getting fleet data: {str(e)}")
        return jsonify({'error': 'Failed to get fleet data'}), 500

@app.route('/api/economics')
def get_economics():
    """Get economic data"""
    try:
        user_id = request.args.get('user_id')
        economic_data = viz_service._get_economic_data(user_id)
        return jsonify(economic_data)
    except Exception as e:
        logger.error(f"Error getting economic data: {str(e)}")
        return jsonify({'error': 'Failed to get economic data'}), 500

@app.route('/api/economics/analytics')
def get_economics_analytics():
    """Get comprehensive economic analytics"""
    try:
        user_id = request.args.get('user_id')
        if viz_service.analytics_service:
            import asyncio
            analytics_data = asyncio.run(viz_service.analytics_service.get_economic_dashboard_data(user_id))
            return jsonify(analytics_data)
        else:
            return jsonify({'error': 'Analytics service not available'}), 503
    except Exception as e:
        logger.error(f"Error getting economic analytics: {str(e)}")
        return jsonify({'error': 'Failed to get economic analytics'}), 500

@app.route('/api/orbital')
def get_orbital():
    """Get orbital mechanics data"""
    try:
        orbital_data = viz_service._get_orbital_data()
        return jsonify(orbital_data)
    except Exception as e:
        logger.error(f"Error getting orbital data: {str(e)}")
        return jsonify({'error': 'Failed to get orbital data'}), 500

@app.route('/api/risk')
def get_risk():
    """Get risk assessment data"""
    try:
        risk_data = viz_service._get_risk_data()
        return jsonify(risk_data)
    except Exception as e:
        logger.error(f"Error getting risk data: {str(e)}")
        return jsonify({'error': 'Failed to get risk data'}), 500

@app.route('/api/market')
def get_market():
    """Get market data"""
    try:
        market_data = viz_service._get_market_data()
        return jsonify(market_data)
    except Exception as e:
        logger.error(f"Error getting market data: {str(e)}")
        return jsonify({'error': 'Failed to get market data'}), 500

@app.route('/api/commodity-prices')
def get_commodity_prices():
    """Get current commodity prices"""
    try:
        if viz_service.pricing_service:
            prices_per_kg = viz_service.pricing_service.get_commodity_prices_per_kg()
            return jsonify({
                'prices_per_kg': prices_per_kg,
                'last_updated': viz_service._get_timestamp()
            })
        else:
            # Fallback prices
            return jsonify({
                'prices_per_kg': {
                    'Gold': 70548.0,
                    'Platinum': 35274.0,
                    'Silver': 881.85,
                    'Copper': 9.0,
                    'Palladium': 35274.0
                },
                'last_updated': viz_service._get_timestamp()
            })
    except Exception as e:
        logger.error(f"Error getting commodity prices: {str(e)}")
        return jsonify({
            'prices_per_kg': {
                'Gold': 70548.0,
                'Platinum': 35274.0,
                'Silver': 881.85,
                'Copper': 9.0,
                'Palladium': 35274.0
            },
            'last_updated': viz_service._get_timestamp()
        }), 200

@app.route('/api/orbital/travel-time')
def get_travel_time():
    """Calculate travel time for orbital mechanics"""
    try:
        moid_au = float(request.args.get('moid_au', 1.0))
        mission_type = request.args.get('mission_type', 'round_trip')
        
        if viz_service.orbital_service:
            import asyncio
            result = asyncio.run(viz_service.orbital_service.calculate_travel_time(
                moid_au=moid_au,
                mission_type=mission_type
            ))
            return jsonify(result)
        else:
            # Fallback calculation
            distance_km = moid_au * 149597870.7  # AU to km
            speed_kmh = 72537  # km/h
            one_way_hours = distance_km / speed_kmh
            one_way_days = one_way_hours / 24
            
            if mission_type == 'round_trip':
                total_days = one_way_days * 2
            elif mission_type == 'mining_mission':
                total_days = one_way_days * 2 + 30  # Add 30 days for mining
            else:
                total_days = one_way_days
            
            return jsonify({
                'one_way_time_days': one_way_days,
                'total_time_days': total_days,
                'distance_km': distance_km,
                'moid_au': moid_au
            })
    except Exception as e:
        logger.error(f"Error calculating travel time: {str(e)}")
        return jsonify({'error': 'Failed to calculate travel time'}), 500

@app.route('/api/mining/operations')
def get_mining_operations():
    """Get active mining operations data from MongoDB"""
    try:
        user_id = request.args.get('user_id')
        mining_data = viz_service._get_mining_data(user_id)
        return jsonify(mining_data)
    except Exception as e:
        logger.error(f"Error getting mining operations: {str(e)}")
        return jsonify({
            'active_mining_missions': [],
            'total_active': 0,
            'total_cargo': 0,
            'error': str(e)
        }), 500

@app.route('/api/mining/mission/<mission_id>')
def get_mission_mining_details(mission_id):
    """Get detailed mining data for a specific mission"""
    try:
        if not viz_service.mongo_db:
            return jsonify({'error': 'MongoDB not available'}), 500
        
        missions_collection = viz_service.mongo_db.missions
        asteroids_collection = viz_service.mongo_db.asteroids
        
        from bson import ObjectId
        mission = missions_collection.find_one({"_id": ObjectId(mission_id)})
        
        if not mission:
            return jsonify({'error': 'Mission not found'}), 404
        
        if mission.get('current_phase') != 'mining':
            return jsonify({'error': 'Mission is not in mining phase'}), 400
        
        # Get cargo data
        cargo = mission.get('cargo', {})
        if isinstance(cargo, list):
            cargo_dict = {}
            for item in cargo:
                if isinstance(item, dict):
                    element = item.get('element') or item.get('name')
                    mass = item.get('mass_kg') or item.get('weight', 0)
                    if element:
                        cargo_dict[element] = mass
            cargo = cargo_dict
        
        current_cargo_kg = sum(cargo.values()) if cargo else 0
        ship_capacity_kg = mission.get('ship_capacity', 50000)
        progress_percentage = (current_cargo_kg / ship_capacity_kg * 100) if ship_capacity_kg > 0 else 0
        
        # Get asteroid class
        asteroid_class = None
        asteroid_id = mission.get('asteroid_id')
        asteroid_name = mission.get('asteroid_name')
        
        if asteroid_id:
            try:
                if isinstance(asteroid_id, str) and len(asteroid_id) == 24:
                    asteroid_obj = asteroids_collection.find_one({"_id": ObjectId(asteroid_id)})
                else:
                    asteroid_obj = asteroids_collection.find_one({"name": asteroid_name})
                
                if asteroid_obj:
                    asteroid_class = asteroid_obj.get('class', 'C')
            except Exception as e:
                logger.warning(f"Error getting asteroid class: {e}")
        
        if not asteroid_class:
            asteroid_class = 'C'
        
        # Format cargo breakdown
        cargo_breakdown = {}
        for element, weight in cargo.items():
            if weight > 0:
                cargo_breakdown[element] = round(weight, 2)
        
        return jsonify({
            'mission_id': mission_id,
            'name': mission.get('name', 'Unnamed Mission'),
            'asteroid_name': asteroid_name,
            'asteroid_class': asteroid_class,
            'current_cargo_kg': round(current_cargo_kg, 2),
            'ship_capacity_kg': ship_capacity_kg,
            'progress_percentage': round(progress_percentage, 2),
            'mining_days': mission.get('current_day', 0),
            'cargo_breakdown': cargo_breakdown,
            'daily_yield': round(current_cargo_kg / max(mission.get('current_day', 1), 1), 2)
        })
        
    except Exception as e:
        logger.error(f"Error getting mission mining details: {str(e)}")
        return jsonify({'error': f'Failed to get mission mining details: {str(e)}'}), 500

@app.route('/api/alerts')
def get_alerts():
    """Get alert data"""
    try:
        user_id = request.args.get('user_id')
        alert_data = viz_service._get_alert_data(user_id)
        return jsonify(alert_data)
    except Exception as e:
        logger.error(f"Error getting alert data: {str(e)}")
        return jsonify({'error': 'Failed to get alert data'}), 500

@app.route('/api/charts')
def get_charts():
    """Get chart data"""
    try:
        chart_data = viz_service._get_chart_data()
        return jsonify(chart_data)
    except Exception as e:
        logger.error(f"Error getting chart data: {str(e)}")
        return jsonify({'error': 'Failed to get chart data'}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'AstroSurge Visualization API',
        'version': '1.0.0',
        'timestamp': viz_service._get_timestamp()
    })

def _get_timestamp():
    """Get current timestamp"""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

# Add the timestamp method to the viz_service
viz_service._get_timestamp = _get_timestamp

if __name__ == '__main__':
    # Get port from environment or default to 5000
    port = int(os.getenv('FLASK_PORT', '5000'))
    # Debug mode should be disabled in production
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    print("🚀 Starting AstroSurge Visualization Dashboard API...")
    print(f"📊 Dashboard available at: http://localhost:{port}")
    print(f"🔗 API endpoints available at: http://localhost:{port}/api/")
    print("=" * 60)
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)



