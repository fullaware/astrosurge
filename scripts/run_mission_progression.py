#!/usr/bin/env python3
"""Run the full AstroSurge mission progression (Tiers 1-4)."""

import json
import sys
import urllib.request

API = "http://localhost:8001/api/simulate"


def simulate(spkid, ship_cost=50_000_000, reusable=True, refinery=False,
             mining_days=139, previous_mission_profit=0.0, seed=42):
    """Run a simulation via the API and return parsed result."""
    payload = {
        "spkid": spkid,
        "ship_cost": ship_cost,
        "reusable": reusable,
        "refinery": refinery,
        "mining_days": mining_days,
        "previous_mission_profit": previous_mission_profit,
        "seed": seed,
    }
    req = urllib.request.Request(
        API,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def report(tier, label, r):
    """Print a mission result."""
    fin = r.get("financials", {})
    mining = r.get("mining", {})
    transit = r.get("transit", {})
    status_icon = "✅" if r["status"] == "completed" else "❌"
    print(f"\n{'='*60}")
    print(f"{status_icon} TIER {tier}: {label}")
    print(f"{'='*60}")
    print(f"  Status:           {r['status']}")
    print(f"  Target:           {r['asteroid_name']} (spkid {r['spkid']})")
    print(f"  Duration:         {transit.get('round_trip_days', 0)} days")
    print(f"  Mined:            {mining.get('total_mined_kg', 0):,.0f} kg")
    print(f"  Ore extracted:    {mining.get('total_ore_kg', 0):,.1f} kg")
    print(f"  Total Revenue:    ${fin.get('total_revenue_usd', 0):,.2f}")
    print(f"  Total Cost:       ${fin.get('total_cost_usd', 0):,.2f}")
    print(f"  Net Profit:       ${fin.get('net_profit_usd', 0):,.2f}")
    print(f"  ROI:              {fin.get('roi', 0)*100:.1f}%")
    print(f"  Debt Repaid:      ${fin.get('debt_repaid', 0):,.2f}")
    print(f"  Retained Profit:  ${fin.get('retained_profit', 0):,.2f}")
    if r.get("error"):
        print(f"  Error:            {r['error']}")
    return fin.get("retained_profit", 0)


def main():
    seed = 42

    # ═══════════════════════════════════════════════════════════════════
    # TIER 1: Fast ROI (PGM Strike)
    # Target: Heracles (spkid=2005143) — M-class, MOID 0.0584
    # Ship: Base mining ship, reusable launch, no refinery
    # ═══════════════════════════════════════════════════════════════════
    retained = simulate(spkid=2005143, ship_cost=50_000_000,
                        reusable=True, refinery=False, seed=seed)
    retained = report(1, "Fast ROI — Heracles (M-class, MOID 0.0584)", retained)

    if retained.get("status") != "completed":
        print("\n❌ Tier 1 failed. Cannot proceed.")
        return

    tier1_profit = retained.get("financials", {}).get("retained_profit", 0)
    print(f"\n  >>> Tier 1 retained profit: ${tier1_profit:,.2f}")

    # Check if we can afford the Tier 2 upgrade
    upgrade_cost_t2 = 30_000_000  # water extraction + cryotankage
    if tier1_profit < upgrade_cost_t2:
        print(f"  ⚠️  Not enough profit for Tier 2 upgrade (${upgrade_cost_t2:,.2f} needed)")
        print(f"  ...running another Tier 1 mission on Zeus to build capital...")
        r2 = simulate(spkid=2005732, ship_cost=50_000_000,
                      reusable=True, refinery=False,
                      previous_mission_profit=tier1_profit, seed=seed+1)
        r2 = report(1, "Fast ROI — Zeus (M-class, MOID 0.0707)", r2)
        tier1_profit += r2.get("financials", {}).get("retained_profit", 0)
        print(f"\n  >>> Combined retained: ${tier1_profit:,.2f}")

    # ═══════════════════════════════════════════════════════════════════
    # TIER 2: Ice Farming
    # Target: Cuyo (spkid=2003753) — C-class, MOID 0.0727
    # Upgrade: water_extraction + cryotankage ($30M assumed)
    # Ship: reusable launch, no refinery for ice
    # ═══════════════════════════════════════════════════════════════════
    budget_after_t2_upgrade = tier1_profit - upgrade_cost_t2
    print(f"\n  >>> Budget for Tier 2 mission after upgrade: ${budget_after_t2_upgrade:,.2f}")

    r3 = simulate(spkid=2003753, ship_cost=50_000_000,
                  reusable=True, refinery=False,
                  previous_mission_profit=budget_after_t2_upgrade,
                  mining_days=180, seed=seed+2)
    r3 = report(2, "Ice Farming — Cuyo (C-class, MOID 0.0727)", r3)

    tier2_profit = r3.get("financials", {}).get("retained_profit", 0)

    # ═══════════════════════════════════════════════════════════════════
    # TIER 3: Hazard Hunter
    # Target: Toutatis (spkid=2004179) — C-class PHA, MOID 0.0066
    # Upgrade: propulsion_manufacturing ($50M assumed)
    # ═══════════════════════════════════════════════════════════════════
    upgrade_cost_t3 = 50_000_000
    budget_after_t3_upgrade = tier2_profit - upgrade_cost_t3
    print(f"\n  >>> Budget for Tier 3 mission after upgrade: ${budget_after_t3_upgrade:,.2f}")

    r4 = simulate(spkid=2004179, ship_cost=75_000_000,
                  reusable=True, refinery=False,
                  previous_mission_profit=budget_after_t3_upgrade,
                  mining_days=200, seed=seed+3)
    r4 = report(3, "Hazard Hunter — Toutatis (C-class PHA, MOID 0.0066)", r4)

    tier3_profit = r4.get("financials", {}).get("retained_profit", 0)

    # ═══════════════════════════════════════════════════════════════════
    # TIER 4: Precision Extraction
    # Target: Heracles again (spkid=2005143) — already characterized
    # Upgrade: advanced_refinement + swarm_ai ($80M assumed)
    # Use refinery for PGM-specific separation
    # ═══════════════════════════════════════════════════════════════════
    upgrade_cost_t4 = 80_000_000
    budget_after_t4_upgrade = tier3_profit - upgrade_cost_t4
    print(f"\n  >>> Budget for Tier 4 mission after upgrade: ${budget_after_t4_upgrade:,.2f}")

    r5 = simulate(spkid=2005143, ship_cost=100_000_000,
                  reusable=True, refinery=True,
                  previous_mission_profit=budget_after_t4_upgrade,
                  mining_days=250, seed=seed+4)
    r5 = report(4, "Precision Extraction — Heracles return (M-class, refinery)", r5)

    # ═══════════════════════════════════════════════════════════════════
    # FINAL SUMMARY
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'='*60}")
    print("🏁 MISSION PROGRESSION COMPLETE")
    print(f"{'='*60}")
    print(f"  Tier 1 Profit:     ${tier1_profit:>12,.2f}")
    print(f"  Tier 2 Profit:     ${tier2_profit:>12,.2f}")
    print(f"  Tier 3 Profit:     ${tier3_profit:>12,.2f}")
    print(f"  Tier 4 Profit:     ${r5.get('financials',{}).get('retained_profit',0):>12,.2f}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
