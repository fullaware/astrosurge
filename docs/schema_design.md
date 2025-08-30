# AstroSurge Database Schema Design

## Overview
This document outlines the new clean database schema for AstroSurge, designed to be simple, efficient, and focused on the core simulation requirements.

## Collections to Keep (Read-Only)
- **asteroids**: 958,524 records with asteroid data
- **elements**: 119 chemical elements

## Collections to Replace (New Clean Schema)

### 1. Users Collection
```javascript
{
  "_id": "ObjectId",
  "username": "string",           // Unique username
  "company_name": "string",        // Company name
  "bank_balance": "number",        // Current balance in dollars
  "created_at": "datetime",       // Account creation date
  "last_login": "datetime"        // Last login timestamp
}
```

### 2. Ships Collection
```javascript
{
  "_id": "ObjectId",
  "name": "string",               // Ship name
  "user_id": "ObjectId",          // Reference to user
  "capacity": "number",           // Cargo capacity in kg
  "mining_power": "number",       // Mining efficiency (1-100)
  "shield": "number",             // Shield strength (1-100)
  "hull": "number",               // Hull integrity (1-100)
  "location": "number",           // 0.0=Earth, 1.0=Asteroid
  "status": "string",             // "available", "en_route", "mining", "returning", "repairing"
  "created_at": "datetime",       // Ship creation date
  "active": "boolean"             // Whether ship is operational
}
```

### 3. Missions Collection
```javascript
{
  "_id": "ObjectId",
  "name": "string",               // Mission name
  "user_id": "ObjectId",          // Reference to user
  "ship_id": "ObjectId",          // Reference to ship
  "asteroid_name": "string",      // Target asteroid name
  "status": "string",             // "planned", "in_progress", "completed", "failed"
  "travel_days": "number",        // Days to reach asteroid
  "mining_days": "number",        // Days allocated for mining
  "days_elapsed": "number",       // Current day in mission
  "ship_location": "number",      // Current ship location (0.0-1.0)
  "cargo": [                      // Current cargo
    {
      "element": "string",        // Element name
      "mass_kg": "number"         // Mass in kg
    }
  ],
  "total_yield_kg": "number",     // Total extracted mass
  "budget": "number",             // Mission budget in dollars
  "cost": "number",               // Current mission cost
  "revenue": "number",            // Expected revenue
  "profit": "number",             // Expected profit
  "created_at": "datetime",       // Mission creation date
  "started_at": "datetime",       // Mission start date
  "completed_at": "datetime"      // Mission completion date
}
```

### 4. Simulation State Collection
```javascript
{
  "_id": "ObjectId",
  "user_id": "ObjectId",          // Reference to user
  "current_day": "number",        // Current simulation day
  "is_running": "boolean",        // Whether simulation is active
  "active_missions": ["ObjectId"], // Array of active mission IDs
  "last_updated": "datetime"      // Last simulation update
}
```

### 5. Market Prices Collection
```javascript
{
  "_id": "ObjectId",
  "element": "string",            // Element name
  "price_per_kg": "number",       // Price per kg in dollars
  "last_updated": "datetime"      // Last price update
}
```

## Key Design Principles

### 1. Simplicity
- Only essential fields included
- No complex nested structures
- Clear, readable field names

### 2. Performance
- Index on frequently queried fields
- Minimal document size
- Efficient query patterns

### 3. Maintainability
- Consistent naming conventions
- Clear relationships between collections
- Easy to extend and modify

### 4. Simulation Focus
- Fields directly support simulation logic
- Real-time updates supported
- Turn-based progression enabled

## Indexes

### Users Collection
- `username` (unique)
- `company_name`

### Ships Collection
- `user_id`
- `status`
- `active`

### Missions Collection
- `user_id`
- `ship_id`
- `status`
- `created_at`

### Simulation State Collection
- `user_id` (unique per user)

### Market Prices Collection
- `element` (unique per element)

## Data Migration Plan

### Phase 1: Backup
- Export existing data from old collections
- Verify data integrity

### Phase 2: Cleanup
- Drop old collections (ships, missions, users, etc.)
- Keep asteroids and elements collections

### Phase 3: Implementation
- Create new collections with clean schema
- Implement data validation
- Test basic CRUD operations

### Phase 4: Validation
- Verify new schema works correctly
- Test simulation integration
- Validate performance

## Benefits of New Schema

1. **Cleaner Code**: Simpler models, easier to maintain
2. **Better Performance**: Optimized indexes, smaller documents
3. **Easier Testing**: Clear structure, predictable behavior
4. **Future-Proof**: Easy to extend and modify
5. **Simulation Ready**: Direct support for turn-based progression
