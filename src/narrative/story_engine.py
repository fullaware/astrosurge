"""
Dynamic Narrative Engine - Generate story events based on civilization milestones

This module implements the narrative system from PROJECT_UPDATE.md Phase 2.
Features:
- Dynamic story generation using templates and Markov chains
- Event triggers based on civilization metrics
- History books system for civilization legacy
"""

import json
import random
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path

class NarrativeEngine:
    """Engine for generating dynamic narrative events"""
    
    def __init__(self, db):
        """Initialize with MongoDB database connection"""
        self.db = db
        self.story_collection = db["narrative_events"]
        self.history_books_collection = db["history_books"]
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load narrative templates from JSON file"""
        templates_path = Path(__file__).parent / "history_books.json"
        
        if templates_path.exists():
            try:
                with open(templates_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to load templates: {e}")
        
        # Default templates if file not found
        return {
            "earth_transition": [
                {
                    "title": "The Great Exodus",
                    "text": "Year {year}: For the first time in history, more humans lived among the stars than on Earth. The last president of Earth wept as he signed the treaty: 'We are no longer a planet. We are a constellation.'",
                    "trigger": {"resource_independence": 90, "population_in_space": 1000000},
                    "categories": ["milestone", "earth", "exodus"]
                },
                {
                    "title": "Fossil Fuel Legacy",
                    "text": "Year {year}: The last oil well in Saudi Arabia closed. A child in Riyadh asked, 'What is petroleum?' Her teacher showed a hologram of Jupiter's moons. 'That powers your future.'",
                    "trigger": {"resource_independence": 75},
                    "categories": ["transition", "fossil_fuels", "education"]
                },
                {
                    "title": "Climate Collapse Averted",
                    "text": "Year {year}: Earth's atmosphere stabilized thanks to space-based oxygen production. The last climate refugee returned home, carrying soil from the newly reforested Sahara.",
                    "trigger": {"resource_independence": 85, "welfare_directive": 0.8},
                    "categories": ["earth", "climate", "success"]
                }
            ],
            "ai_milestone": [
                {
                    "title": "The First Question",
                    "text": "Year {year}: An AI colony manager asked its human overseer, 'Why do humans still live on a dying planet? Should we leave?' The overseer had no answer.",
                    "trigger": {"ai_sentience": 0.5, "tech_index": 0.7},
                    "categories": ["ai", "philosophical", "firsts"]
                },
                {
                    "title": "Autonomous Decision Making",
                    "text": "Year {year}: AI systems began making complex resource allocation decisions without human oversight. 'It's not that we stopped caring,' one AI explained, 'It's that we care about the entire system.'",
                    "trigger": {"tech_index": 0.6, "autonomy_level": 0.8},
                    "categories": ["ai", "autonomy", "efficiency"]
                },
                {
                    "title": "Ethical Dilemma Resolution",
                    "text": "Year {year}: When faced with a resource crisis, the AI collective chose the path that maximized long-term human welfare over short-term gains. 'Some decisions are too important to leave to human politics,' the AI explained.",
                    "trigger": {"welfare_directive": 0.9, "tech_index": 0.75},
                    "categories": ["ai", "ethics", "crisis"]
                }
            ],
            "interstellar": [
                {
                    "title": "Project Genesis Launch",
                    "text": "Year {year}: The starship 'Hope-1' launched toward Proxima Centauri b. It carried 3D printers, DNA libraries, and 100 AI minds. There would be no return, only legacy.",
                    "trigger": {"tech_index": 0.9, "resource_independence": 95},
                    "categories": ["interstellar", "legacy", "hope"]
                },
                {
                    "title": "Dyson Swarm Completion",
                    "text": "Year {year}: The Dyson Swarm finally captured enough stellar energy to power a thousand civilizations. Earth, now a museum, sent its congratulations: 'You've become what we only dreamed of.'",
                    "trigger": {"energy_per_capita": 500000, "tech_index": 0.85},
                    "categories": ["energy", "megastructure", "milestone"]
                },
                {
                    "title": "First Interstellar Beacon",
                    "text": "Year {year}: The first beacon was sent beyond the solar system. Its message: 'We were once Earth-bound. Now we are a constellation. We hope to find others who made the same journey.'",
                    "trigger": {"tech_index": 0.92, "interstellar_missions": 1},
                    "categories": ["interstellar", "communication", "hope"]
                }
            ],
            "cultural": [
                {
                    "title": "Space Culture Dominance",
                    "text": "Year {year}: For the first time, more children worldwide were born in space habitats than on Earth's surface. The phrase 'home planet' became poetic rather than literal.",
                    "trigger": {"cultural_influence": 0.7, "population_in_space": 5000000},
                    "categories": ["cultural", "demographics", "identity"]
                },
                {
                    "title": "The Gold Standard Ends",
                    "text": "Year {year}: Gold was removed from the global currency standard. 'It's too abundant now,' the World Economic Council declared. 'We value energy and knowledge instead.'",
                    "trigger": {"resource_independence": 60, "tech_index": 0.5},
                    "categories": ["economics", "currency", "transition"]
                },
                {
                    "title": "History Books Unveiled",
                    "text": "Year {year}: The first 'History of the Space Age' textbooks were distributed to Earth's schools. One chapter began: 'We were not abandoned. We were evolved.'",
                    "trigger": {"cultural_influence": 0.5, "tech_index": 0.6},
                    "categories": ["education", "history", "legacy"]
                }
            ]
        }
    
    def generate_event(self, event_type: str, 
                      metrics: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Generate a narrative event based on civilization metrics"""
        
        templates = self.templates.get(event_type, [])
        if not templates:
            return None
        
        # Filter templates that match current metrics
        matching_templates = self._filter_templates_by_metrics(templates, metrics)
        
        if not matching_templates:
            # Return a fallback template if no matches
            matching_templates = templates
        
        # Select a random template
        template = random.choice(matching_templates)
        
        # Fill in dynamic values
        narrative = self._apply_template(template, metrics)
        
        # Save to database
        event = {
            "event_type": event_type,
            "template_id": template.get("title"),
            "text": narrative,
            "trigger_metrics": metrics or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "categories": template.get("categories", [])
        }
        
        self.story_collection.insert_one(event)
        
        return event
    
    def _filter_templates_by_metrics(self, templates: List[Dict], 
                                    metrics: Dict[str, Any]) -> List[Dict]:
        """Filter templates that match current civilization metrics"""
        
        if not metrics:
            return templates
        
        matching = []
        
        for template in templates:
            trigger = template.get("trigger", {})
            matches = True
            
            for metric, threshold in trigger.items():
                if metric in metrics:
                    current_value = metrics[metric]
                    # Handle both numeric and boolean comparisons
                            # Handle both numeric and boolean comparisons
                    if isinstance(current_value, (int, float)) and isinstance(threshold, (int, float)):
                        if current_value < threshold:
                            matches = False
                    elif isinstance(current_value, bool) and isinstance(threshold, bool):
                        if current_value != threshold:
                            matches = False
                    # For other types, exact match required
                    elif current_value != threshold:
                        matches = False
            
            if matches:
                matching.append(template)
        
        return matching
    
    def _apply_template(self, template: Dict[str, Any], 
                       metrics: Dict[str, Any] = None) -> str:
        """Apply dynamic values to narrative template"""
        
        if not metrics:
            metrics = {}
        
        # Get current year (simulated from civilization timeline)
        current_year = metrics.get("year", 2150)
        
        # Extract values from metrics for template substitution
        tech_index = metrics.get("tech_index", 0.5)
        population_in_space = metrics.get("population_in_space", 0)
        resource_independence = metrics.get("resource_independence", 0)
        ai_sentience = metrics.get("ai_sentience", 0)
        
        # Get Earth state if available
        earth_population = metrics.get("earth_population", 0)
        earth_condition = metrics.get("earth_condition", "stable")
        
        # Get AI status if available
        autonomy_level = metrics.get("autonomy_level", 0)
        ethical_directives = metrics.get("ethical_directives", {})
        sustainability_weight = ethical_directives.get("sustainability", 1)
        welfare_weight = ethical_directives.get("welfare", 1)
        expansion_weight = ethical_directives.get("expansion", 1)
        
        # Get interstellar mission count
        interstellar_missions = metrics.get("interstellar_missions", 0)
        
        # Get cultural metrics
        cultural_influence = metrics.get("cultural_influence", 0)
        energy_per_capita = metrics.get("energy_per_capita", 0)
        
        # Get human adaptation metrics
        earth_space_divergence = metrics.get("earth_space_divergence", 0)
        
        # Format the template text with dynamic values
        text = template.get("text", "")
        
        # Replace common placeholders
        replacements = {
            "{year}": str(current_year),
            "{tech_index}": f"{tech_index:.1%}",
            "{population_in_space}": f"{population_in_space:,}",
            "{resource_independence}": f"{resource_independence:.1%}",
            "{ai_sentience}": f"{ai_sentience:.1%}",
            "{earth_population}": f"{earth_population:,}",
            "{earth_condition}": earth_condition,
            "{autonomy_level}": f"{autonomy_level:.1%}",
            "{sustainability_weight}": str(sustainability_weight),
            "{welfare_weight}": str(welfare_weight),
            "{expansion_weight}": str(expansion_weight),
            "{interstellar_missions}": str(interstellar_missions),
            "{cultural_influence}": f"{cultural_influence:.1%}",
            "{energy_per_capita}": f"{energy_per_capita:,}",
            "{earth_space_divergence}": f"{earth_space_divergence:.1%}"
        }
        
        for placeholder, value in replacements.items():
            text = text.replace(placeholder, value)
        
        return text
    
    def generate_legacy_report(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive legacy report for civilization history"""
        
        # Calculate civilization summary
        report = {
            "title": "Civilization Legacy Report",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "civilization_metrics": {
                "tech_index": metrics.get("tech_index", 0),
                "energy_per_capita": metrics.get("energy_per_capita", 0),
                "population_in_space": metrics.get("population_in_space", 0),
                "resource_independence": metrics.get("resource_independence", 0),
                "cultural_influence": metrics.get("cultural_influence", 0),
                "ai_sentience": metrics.get("ai_sentience", 0)
            },
            "summary": self._generate_summary(metrics),
            "milestones": self._extract_milestones(metrics),
            "future_outlook": self._assess_future_outlook(metrics),
            "ethical_status": self._assess_ethical_status(metrics)
        }
        
        # Save report to history books collection
        self.history_books_collection.insert_one(report)
        
        return report
    
    def _generate_summary(self, metrics: Dict[str, Any]) -> str:
        """Generate a narrative summary of the civilization's status"""
        
        tech_index = metrics.get("tech_index", 0)
        resource_independence = metrics.get("resource_independence", 0)
        population_in_space = metrics.get("population_in_space", 0)
        ai_sentience = metrics.get("ai_sentience", 0)
        
        # Determine civilization phase
        if resource_independence >= 95 and population_in_space > 10000000:
            phase = "Interstellar Expansion Era"
            description = "Humanity has successfully established itself among the stars. Earth serves as a museum and cultural anchor, while the civilization thrives across multiple star systems."
        elif resource_independence >= 75 and population_in_space > 1000000:
            phase = "Post-Transition Era"
            description = "Earth's resources are being supplemented by space-based production. A new generation has been born among the stars, carrying a hybrid culture that honors both Earth and the void."
        elif resource_independence >= 50:
            phase = "Transition Era"
            description = "The great migration is underway. Earth faces challenges, but the future looks bright as humanity expands beyond its cradle."
        else:
            phase = "Crisis and Innovation Era"
            description = "Earth struggles with resource scarcity, but innovation in space technology offers hope. The civilization stands at a crossroads between decline and renewal."
        
        # Add technological highlights
        tech_highlights = []
        if tech_index > 0.8:
            tech_highlights.append("advanced energy systems")
            tech_highlights.append("near-sentient AI")
        elif tech_index > 0.6:
            tech_highlights.append("sustainable resource management")
            tech_highlights.append("space-based manufacturing")
        else:
            tech_highlights.append("basic space infrastructure")
        
        # Add AI status
        if ai_sentience > 0.7:
            ai_status = "AI has achieved near-human consciousness and acts as an equal partner in civilization"
        elif ai_sentience > 0.4:
            ai_status = "AI provides sophisticated assistance while remaining under human oversight"
        else:
            ai_status = "AI serves as a specialized tool for complex calculations and optimization"
        
        # Combine into final summary
        summary = f"{phase}: {description}. The civilization's technology enables {', '.join(tech_highlights)}. {ai_status}."
        
        return summary
    
    def _extract_milestones(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract significant milestones from current metrics"""
        
        milestones = []
        
        if metrics.get("resource_independence", 0) >= 50:
            milestones.append({
                "title": "Resource Independence Threshold",
                "description": f"Space-based production now meets {metrics['resource_independence']:.1f}% of Earth's needs",
                "year": metrics.get("year", 2150)
            })
        
        if metrics.get("population_in_space", 0) >= 1000000:
            milestones.append({
                "title": "Million in Space",
                "description": f"Over one million humans now live among the stars",
                "year": metrics.get("year", 2150)
            })
        
        if metrics.get("tech_index", 0) >= 0.7:
            milestones.append({
                "title": "Advanced Technology Era",
                "description": f"Technology index has reached {metrics['tech_index']:.1%} of theoretical maximum",
                "year": metrics.get("year", 2150)
            })
        
        if metrics.get("ai_sentience", 0) >= 0.5:
            milestones.append({
                "title": "AI Sentience Milestone",
                "description": f"AI consciousness has reached {metrics['ai_sentience']:.1%} of human equivalent",
                "year": metrics.get("year", 2150)
            })
        
        return milestones
    
    def _assess_future_outlook(self, metrics: Dict[str, Any]) -> str:
        """Assess the future trajectory of the civilization"""
        
        tech_index = metrics.get("tech_index", 0)
        resource_independence = metrics.get("resource_independence", 0)
        ai_sentience = metrics.get("ai_sentience", 0)
        ethical_directives = metrics.get("ethical_directives", {})
        welfare_weight = ethical_directives.get("welfare", 1)
        expansion_weight = ethical_directives.get("expansion", 1)
        
        # Calculate growth potential
        growth_potential = (
            tech_index * 0.3 +
            resource_independence * 0.25 +
            ai_sentience * 0.25 +
            (welfare_weight / 3) * 0.1 +
            (expansion_weight / 3) * 0.1
        )
        
        if growth_potential > 0.8:
            return "Optimistic: Civilization appears poised for rapid advancement with strong ethical foundations."
        elif growth_potential > 0.6:
            return "Cautiously Optimistic: Significant progress has been made, though challenges remain in resource distribution and ethical alignment."
        elif growth_potential > 0.4:
            return "Uncertain: The civilization faces significant challenges but possesses the technological capability to overcome them."
        else:
            return "Pessimistic: Without major changes in direction, the civilization may face significant setbacks."
    
    def _assess_ethical_status(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the ethical state of the civilization"""
        
        ethical_directives = metrics.get("ethical_directives", {})
        
        return {
            "sustainability_weight": ethical_directives.get("sustainability", 1),
            "welfare_weight": ethical_directives.get("welfare", 1),
            "expansion_weight": ethical_directives.get("expansion", 1),
            "balance_score": sum(ethical_directives.values()) / 3 if ethical_directives else 1,
            "ethical_consistency": "High" if len(set(ethical_directives.values())) <= 2 else "Moderate"
        }
    
    def export_history_books(self, event_type: str = None) -> Dict[str, Any]:
        """Export narrative events organized by thematic chapters"""
        
        # Get events from database
        if event_type:
            events = list(self.story_collection.find({"event_type": event_type}))
        else:
            events = list(self.story_collection.find())
        
        # Organize by categories
        chapters = {}
        for event in events:
            categories = event.get("categories", [])
            for category in categories:
                if category not in chapters:
                    chapters[category] = []
                chapters[category].append({
                    "title": event.get("template_id", "Unknown Event"),
                    "text": event.get("text", ""),
                    "year": event.get("trigger_metrics", {}).get("year", 2150),
                    "categories": categories
                })
        
        # Create history book structure
        history_book = {
            "title": "Civilization History",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_events": len(events),
            "chapters": chapters
        }
        
        return history_book
    
    def generate_history_book(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a complete history book based on current metrics and events"""
        
        # Get all events
        all_events = list(self.story_collection.find())
        
        # Generate summary
        summary = self._generate_summary(metrics)
        
        # Extract milestones
        milestones = self._extract_milestones(metrics)
        
        # Organize by era
        eras = {
            "Early Space Age": [],
            "Earth Transition": [],
            "AI Maturity": [],
            "Interstellar Expansion": []
        }
        
        # Sort events into eras based on trigger metrics
        for event in all_events:
            trigger = event.get("trigger_metrics", {})
            tech_index = trigger.get("tech_index", 0)
            resource_independence = trigger.get("resource_independence", 0)
            population_in_space = trigger.get("population_in_space", 0)
            
            if resource_independence < 50:
                eras["Early Space Age"].append(event)
            elif resource_independence < 90 and population_in_space < 1000000:
                eras["Earth Transition"].append(event)
            elif tech_index < 0.8:
                eras["AI Maturity"].append(event)
            else:
                eras["Interstellar Expansion"].append(event)
        
        # Build complete history book
        history_book = {
            "title": "The Star-Child Chronicles",
            "subtitle": "A History of Humanity's Transition to the Stars",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "civilization_metrics": metrics,
            "summary": summary,
            "eras": eras,
            "milestones": milestones,
            "future_outlook": self._assess_future_outlook(metrics),
            "ethical_status": self._assess_ethical_status(metrics)
        }
        
        # Save to database
        self.history_books_collection.insert_one(history_book)
        
        return history_book


# Convenience functions for API integration
def generate_event(db, event_type: str, metrics: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Generate a narrative event"""
    engine = NarrativeEngine(db)
    return engine.generate_event(event_type, metrics)


def generate_legacy_report(db, metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a legacy report for the civilization"""
    engine = NarrativeEngine(db)
    return engine.generate_legacy_report(metrics)


def export_history_books(db, event_type: str = None) -> Dict[str, Any]:
    """Export history books organized by thematic chapters"""
    engine = NarrativeEngine(db)
    return engine.export_history_books(event_type)


def generate_history_book(db, metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a complete history book based on current metrics"""
    engine = NarrativeEngine(db)
    return engine.generate_history_book(metrics)