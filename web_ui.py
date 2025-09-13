#!/usr/bin/env python3
"""
AstroSurge Web UI - Flask-based interface
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import requests
from datetime import datetime
import json
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'astrosurge-secret-key-2024')

# Backend API configuration
API_BASE_URL = os.environ.get('BACKEND_API_URL', "http://localhost:8000/api")

@app.route('/')
def index():
    """Main page - redirect to login if not authenticated"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            session['user_id'] = str(uuid.uuid4())
            session['username'] = username
            return redirect(url_for('company_setup'))
        return render_template('login.html', error="Please enter a username")
    
    return render_template('login.html')

@app.route('/company_setup', methods=['GET', 'POST'])
def company_setup():
    """Company setup page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if 'company_name' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        company_name = request.form.get('company_name')
        if company_name:
            session['company_name'] = company_name
            return redirect(url_for('dashboard'))
        return render_template('company_setup.html', error="Please enter a company name")
    
    return render_template('company_setup.html')

@app.route('/dashboard')
def dashboard():
    """Main dashboard"""
    if 'user_id' not in session or 'company_name' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', 
                         username=session['username'], 
                         company_name=session['company_name'])

@app.route('/api/company/stats')
def company_stats():
    """Get company statistics from backend"""
    try:
        response = requests.get(f"{API_BASE_URL}/company/stats", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                'totalMissions': 0,
                'activeMissions': 0,
                'completedMissions': 0,
                'totalShips': 0,
                'totalRevenue': 0,
                'totalCosts': 0,
                'netProfit': 0
            }), 200
    except Exception as e:
        print(f"Error fetching company stats: {e}")
        return jsonify({
            'totalMissions': 0,
            'activeMissions': 0,
            'completedMissions': 0,
            'totalShips': 0,
            'totalRevenue': 0,
            'totalCosts': 0,
            'netProfit': 0
        }), 200

@app.route('/api/missions')
def get_missions():
    """Get missions from backend"""
    try:
        response = requests.get(f"{API_BASE_URL}/missions", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify([]), 200
    except Exception as e:
        print(f"Error fetching missions: {e}")
        return jsonify([]), 200

@app.route('/api/asteroids')
def get_asteroids():
    """Get asteroids from backend"""
    try:
        response = requests.get(f"{API_BASE_URL}/asteroids", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify([]), 200
    except Exception as e:
        print(f"Error fetching asteroids: {e}")
        return jsonify([]), 200

@app.route('/api/ships')
def get_ships():
    """Get ships from backend"""
    try:
        response = requests.get(f"{API_BASE_URL}/ships", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify([]), 200
    except Exception as e:
        print(f"Error fetching ships: {e}")
        return jsonify([]), 200

@app.route('/api/missions', methods=['POST'])
def create_mission():
    """Create a new mission"""
    try:
        data = request.json
        response = requests.post(f"{API_BASE_URL}/missions", 
                               json=data, 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        return jsonify({'success': response.status_code == 200}), response.status_code
    except Exception as e:
        print(f"Error creating mission: {e}")
        return jsonify({'error': 'Failed to create mission'}), 500

@app.route('/api/ships', methods=['POST'])
def create_ship():
    """Create a new ship"""
    try:
        data = request.json
        response = requests.post(f"{API_BASE_URL}/ships", 
                               json=data, 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        return jsonify({'success': response.status_code == 200}), response.status_code
    except Exception as e:
        print(f"Error creating ship: {e}")
        return jsonify({'error': 'Failed to create ship'}), 500

@app.route('/api/ships/<ship_id>/veteran', methods=['PUT'])
def update_ship_veteran(ship_id):
    """Update ship veteran status"""
    try:
        data = request.json
        response = requests.put(f"{API_BASE_URL}/ships/{ship_id}/veteran", 
                              json=data, 
                              headers={'Content-Type': 'application/json'},
                              timeout=10)
        return jsonify({'success': response.status_code == 200}), response.status_code
    except Exception as e:
        print(f"Error updating ship veteran status: {e}")
        return jsonify({'error': 'Failed to update ship status'}), 500

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
