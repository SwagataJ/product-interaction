"""
Main synthetic data generator.
Produces events.parquet with all journey events + after-hours ops events.
Plants all six insight stories.
"""

import json
import uuid
import numpy as np
import pandas as pd
from datetime import timedelta
from pathlib import Path

from .journey_paths import sample_path
from .timestamps import (
    SIM_START, SIM_DAYS, assign_timestamps, sample_journey_day,
)
from .after_hours import generate_after_hours_events

DATA_DIR = Path(__file__).parent.parent / "data"
LAYOUT_PATH = Path(__file__).parent / "store_layout.json"

# ── Planted story #3: Saturday drop ──────────────────────────────────────────
# The second Saturday in the sim window has trial room utilization drop
PLANTED_SAT_DROP_DAY = SIM_START + timedelta(days=12)  # Second Saturday (Apr 25)
assert PLANTED_SAT_DROP_DAY.weekday() == 5, f"Expected Saturday, got {PLANTED_SAT_DROP_DAY.strftime('%A')}"


def run():
    rng = np.random.default_rng(seed=2026)

    # Load data
    with open(LAYOUT_PATH) as f:
        layout = json.load(f)

    catalog = pd.read_parquet(DATA_DIR / "product_catalog.parquet")
    inventory = pd.read_parquet(DATA_DIR / "tag_inventory.parquet")

    zones = layout["zones"]
    fixtures = [z for z in zones if z["type"] == "fixture"]
    fixture_placement = {z["id"]: z.get("placement", "mid") for z in fixtures}

    all_events = []

    # ── Generate customer journey events for each tag ─────────────────
    # Each tag can have MULTIPLE journeys across the 14-day window.
    # A tag that stays on fixture can be picked up on different days.
    # A tag that was sold exits the cycle. A rejected tag goes back and
    # can be picked up again on a later day.
    TERMINAL_EVENTS = {"EXITED_STORE", "EXITED_WITHOUT_SALE"}

    for idx, tag in inventory.iterrows():
        tag_dict = tag.to_dict()
        initial_zone = tag_dict["initial_zone"]

        # Get placement of the fixture this tag is on (or will go to)
        if initial_zone in fixture_placement:
            placement = fixture_placement[initial_zone]
        else:
            # Backroom tag — pick which fixture it will go to and use that placement
            cat_fixtures = [z for z in fixtures if z.get("category") == tag_dict["category"]]
            if cat_fixtures:
                dest = rng.choice(cat_fixtures)
                placement = dest.get("placement", "mid")
            else:
                placement = "mid"

        # Each tag gets journeys across multiple days until sold/lost
        # Unsold tags can have 3-8 interaction attempts over 14 days
        n_journeys = rng.integers(8, 20)
        used_days = set()
        tag_sold = False
        prev_zone = initial_zone

        for j in range(n_journeys):
            if tag_sold:
                break

            # Pick a unique journey day for this tag
            for _ in range(20):
                day = sample_journey_day(rng)
                if day.date() not in used_days:
                    break
            used_days.add(day.date())

            # For subsequent journeys, the tag might be on a different fixture
            # (e.g., returned to a different fixture after rejection)
            # Re-evaluate placement each journey
            if j > 0 and prev_zone and prev_zone in fixture_placement:
                placement = fixture_placement[prev_zone]

            # Sample journey path
            path = sample_path(tag_dict, placement, fixtures, rng)

            if not path:
                continue

            # Check if this is the planted Saturday drop day
            is_sat_drop = (day.date() == PLANTED_SAT_DROP_DAY.date())

            # Assign timestamps
            timestamped = assign_timestamps(path, day, rng, is_sat_drop)

            if not timestamped:
                continue

            # Build event records
            evt_prev_zone = None
            for evt in timestamped:
                all_events.append({
                    "event_id": str(uuid.uuid4()),
                    "tag_id": tag_dict["tag_id"],
                    "sku_id": tag_dict["sku_id"],
                    "zone_from": evt_prev_zone,
                    "zone_to": evt["zone_to"],
                    "event_type": evt["event_type"],
                    "timestamp": evt["timestamp"],
                    "event_metadata": {},
                })
                evt_prev_zone = evt["zone_to"]
                prev_zone = evt["zone_to"]  # track for placement across journeys

                # If this tag was sold or shrinkage, stop generating journeys
                if evt["event_type"] in TERMINAL_EVENTS:
                    tag_sold = True

    print(f"Customer journey events: {len(all_events)}")

    # ── Generate after-hours operational events ───────────────────────
    ops_events = generate_after_hours_events(inventory, layout, rng)

    for evt in ops_events:
        evt["event_id"] = str(uuid.uuid4())
        if "event_metadata" not in evt:
            evt["event_metadata"] = {}

    all_events.extend(ops_events)
    print(f"Total events (customer + ops): {len(all_events)}")

    # ── Build DataFrame and write ─────────────────────────────────────
    df = pd.DataFrame(all_events)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["event_metadata"] = df["event_metadata"].apply(json.dumps)
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Summary stats
    print(f"\nEvent type distribution:")
    print(df["event_type"].value_counts().to_string())
    print(f"\nDate range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Unique tags: {df['tag_id'].nunique()}")
    print(f"Unique SKUs: {df['sku_id'].nunique()}")

    df.to_parquet(DATA_DIR / "events.parquet", index=False)
    print(f"\nWritten to {DATA_DIR / 'events.parquet'}")


if __name__ == "__main__":
    run()
