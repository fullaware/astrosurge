import random
import logging
from bson import ObjectId, Int64
from models.models import EventModel, MissionModel, MissionDay
from config import MongoDBConfig

class EventProcessor:
    @staticmethod
    def load_events() -> list[EventModel]:
        db = MongoDBConfig.get_database()
        events = db.events.find()
        return [EventModel(**event) for event in events]

    @staticmethod
    def apply_daily_events(mission: MissionModel, day_summary: MissionDay, elements_mined: dict, api_event: dict = None) -> MissionDay:
        db = MongoDBConfig.get_database()
        events = list(db.events.find())
        applied_events = day_summary.events
        phase = "travel" if day_summary.total_kg == 0 else "mining"

        if api_event:
            event = {"name": api_event["name"], "effect": api_event["effect"], "probability": 1.0, "target": "mission", "phase": phase}
            events.append(event)

        # Calculate the day's yield multiplier based on events for this day only
        day_yield_multiplier = 1.0

        for event in events:
            if event.get("phase") == phase and random.random() < event["probability"]:
                effect = event.get("effect", {})
                applied_events.append({"type": event["name"], "effect": effect})
                if event["target"] == "mission":
                    if "yield_multiplier" in effect and phase == "mining":
                        day_yield_multiplier *= effect["yield_multiplier"]
                        day_summary.note = f"{event['name']}: Yield {effect['yield_multiplier']*100}%"
                    if "revenue_multiplier" in effect:
                        mission.revenue_multiplier *= effect["revenue_multiplier"]
                        day_summary.note = f"{event['name']}: Revenue {effect['revenue_multiplier']*100}%"
                    if "repair_cost" in effect:
                        mission.ship_repair_cost += Int64(effect["repair_cost"])
                        day_summary.note = f"{event['name']}: Repair +${effect['repair_cost']}"
                    if "delay_days" in effect:
                        mission.travel_delays += Int64(effect["delay_days"])
                        day_summary.note = f"{event['name']}: Delay +{effect['delay_days']} days"
                    if "reduce_days" in effect:
                        mission.travel_delays = Int64(max(0, mission.travel_delays - effect["reduce_days"]))
                        day_summary.note = f"{event['name']}: Recovery -{effect['reduce_days']} days"
                    if "cost_reduction" in effect:
                        mission.cost = Int64(int(mission.cost * effect["cost_reduction"]))
                        day_summary.note = f"{event['name']}: Cost -{int((1 - effect['cost_reduction']) * 100)}%"

        # Apply the day's yield multiplier to this day's yield only
        if phase == "mining":
            day_summary.total_kg = Int64(int(day_summary.total_kg * day_yield_multiplier))
            for name in elements_mined:
                elements_mined[name] = Int64(int(elements_mined[name] * day_yield_multiplier))

        day_summary.events = applied_events
        logging.info(f"Day {day_summary.day}: Applied {len(applied_events)} events")
        return day_summary