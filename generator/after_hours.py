"""
After-hours operational events: replenishment, stocktake, VM resets.
Low volume (50-100 events per night), narratively meaningful.
"""

import numpy as np
from datetime import datetime, timedelta

from .timestamps import SIM_START, SIM_DAYS, TRADING_CLOSE_HOUR, TRADING_OPEN_HOUR

# Nights where replenishment for size-28 Women_Western Jeans is suppressed
# (planted story #6: replenishment SLA failure)
REPLENISH_FAILURE_NIGHTS = {2, 9}  # night indices (0-based) within simulation


def generate_after_hours_events(
    tag_inventory_df,
    store_layout: dict,
    rng: np.random.Generator,
) -> list[dict]:
    """
    Generate operational events for all nights in the simulation window.
    Returns list of event dicts ready to merge with main event stream.
    """
    import pandas as pd

    fixtures = [z for z in store_layout["zones"] if z["type"] == "fixture"]
    fixture_ids = [f["id"] for f in fixtures]
    fixture_categories = {f["id"]: f.get("category", "") for f in fixtures}

    all_ops_events = []

    for night_idx in range(SIM_DAYS):
        day = SIM_START + timedelta(days=night_idx)
        night_start = day.replace(hour=TRADING_CLOSE_HOUR, minute=0, second=0)
        next_morning = (day + timedelta(days=1)).replace(
            hour=TRADING_OPEN_HOUR, minute=0, second=0
        )

        # ── Replenishment (03:00 - 09:00) ────────────────────────────
        # For each fixture category, replenish some backroom stock
        replenish_start = day.replace(hour=3, minute=0) + timedelta(days=1)
        replenish_end = next_morning

        for fixture in fixtures:
            cat = fixture.get("category", "")
            fixture_id = fixture["id"]

            # Get backroom tags for this category
            backroom_tags = tag_inventory_df[
                (tag_inventory_df["category"] == cat)
                & (tag_inventory_df["initial_zone"] == "BACKROOM")
            ]

            if len(backroom_tags) == 0:
                continue

            # Replenish 3-8 items per fixture per night
            n_replenish = rng.integers(3, 9)
            sample_tags = backroom_tags.sample(
                n=min(n_replenish, len(backroom_tags)),
                random_state=int(rng.integers(0, 100000)),
            )

            for _, tag in sample_tags.iterrows():
                # ── Story #6: suppress size-28 Women_Western replenishment on failure nights ──
                if (
                    night_idx in REPLENISH_FAILURE_NIGHTS
                    and cat == "Women_Western"
                    and tag["size"] == "28"
                ):
                    continue

                ts = _random_time_between(replenish_start, replenish_end, rng)
                all_ops_events.append({
                    "tag_id": tag["tag_id"],
                    "sku_id": tag["sku_id"],
                    "event_type": "OPS_REPLENISHED",
                    "zone_from": "BACKROOM",
                    "zone_to": fixture_id,
                    "timestamp": ts,
                    "event_metadata": {},
                })

        # ── Stocktake scans (23:00 - 02:00) ──────────────────────────
        # 2-3 fixtures per night get cycle-counted
        stocktake_fixtures = rng.choice(fixtures, size=rng.integers(2, 4), replace=False)
        stocktake_start = night_start.replace(hour=23, minute=0)
        stocktake_end = (day + timedelta(days=1)).replace(hour=2, minute=0)

        for fixture in stocktake_fixtures:
            fixture_id = fixture["id"]
            cat = fixture.get("category", "")

            # Scan 5-15 tags on this fixture
            floor_tags = tag_inventory_df[
                (tag_inventory_df["initial_zone"] == fixture_id)
            ]
            if len(floor_tags) == 0:
                continue

            n_scan = min(rng.integers(5, 16), len(floor_tags))
            scan_tags = floor_tags.sample(
                n=n_scan,
                random_state=int(rng.integers(0, 100000)),
            )

            for _, tag in scan_tags.iterrows():
                ts = _random_time_between(stocktake_start, stocktake_end, rng)
                all_ops_events.append({
                    "tag_id": tag["tag_id"],
                    "sku_id": tag["sku_id"],
                    "event_type": "OPS_STOCKTAKE_SCAN",
                    "zone_from": fixture_id,
                    "zone_to": fixture_id,
                    "timestamp": ts,
                    "event_metadata": {},
                })

        # ── VM Resets (06:00 - 09:00) ─────────────────────────────────
        # 1-2 events per night, moving tags between fixtures of same category
        n_vm = rng.integers(1, 3)
        vm_start = (day + timedelta(days=1)).replace(hour=6, minute=0)
        vm_end = next_morning

        for _ in range(n_vm):
            src_fixture = rng.choice(fixtures)
            src_cat = src_fixture.get("category", "")
            same_cat_fixtures = [
                f for f in fixtures
                if f.get("category") == src_cat and f["id"] != src_fixture["id"]
            ]
            if not same_cat_fixtures:
                continue

            dst_fixture = rng.choice(same_cat_fixtures)

            # Pick a tag from source fixture
            src_tags = tag_inventory_df[
                tag_inventory_df["initial_zone"] == src_fixture["id"]
            ]
            if len(src_tags) == 0:
                continue

            tag = src_tags.sample(n=1, random_state=int(rng.integers(0, 100000))).iloc[0]
            ts = _random_time_between(vm_start, vm_end, rng)

            all_ops_events.append({
                "tag_id": tag["tag_id"],
                "sku_id": tag["sku_id"],
                "event_type": "OPS_VM_RESET",
                "zone_from": src_fixture["id"],
                "zone_to": dst_fixture["id"],
                "timestamp": ts,
                "event_metadata": {},
            })

    print(f"After-hours events generated: {len(all_ops_events)}")

    # Count by type
    from collections import Counter
    type_counts = Counter(e["event_type"] for e in all_ops_events)
    print(f"  By type: {dict(type_counts)}")
    print(f"  Avg per night: {len(all_ops_events) / SIM_DAYS:.0f}")

    return all_ops_events


def _random_time_between(
    start: datetime, end: datetime, rng: np.random.Generator
) -> datetime:
    """Random timestamp between start and end."""
    delta = (end - start).total_seconds()
    if delta <= 0:
        return start
    offset = rng.uniform(0, delta)
    return start + timedelta(seconds=offset)
