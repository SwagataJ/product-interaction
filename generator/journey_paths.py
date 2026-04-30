"""
Journey path sampler.
Samples a sequence of (event_type, zone_to) for each tag based on
baseline probabilities + planted-story modifiers.
"""

import numpy as np
from typing import Optional


# ─── Baseline path probabilities ─────────────────────────────────────────────
# From design doc section 2.4
BASELINE_PROBS = {
    "stays_on_fixture":       0.55,
    "picked_returned":        0.20,
    "picked_tried_rejected":  0.14,
    "picked_tried_purchased": 0.07,
    "picked_purchased_no_trial": 0.02,  # mostly accessories
    "misplaced":              0.01,
    "shrinkage":              0.01,
}

# Placement multipliers for pickup probability
PLACEMENT_PICKUP_MULT = {
    "front":     1.6,
    "mid":       1.0,
    "side":      0.8,
    "back":      0.35,  # Back fixtures get much less pickup (story #4: 4x gap)
    "near_exit": 1.2,
}


def sample_path(
    tag_record: dict,
    fixture_placement: str,
    all_fixtures: list[dict],
    rng: np.random.Generator,
) -> list[tuple[str, Optional[str]]]:
    """
    Sample a journey path for a single tag.

    Returns list of (event_type, zone_to) tuples.
    zone_to is the destination zone for the event.
    """
    sku_id = tag_record["sku_id"]
    size = tag_record["size"]
    category = tag_record["category"]
    initial_zone = tag_record["initial_zone"]

    # Start from initial zone
    current_zone = initial_zone
    events = []

    # If tag starts in backroom, first event is receiving
    if current_zone == "BACKROOM":
        events.append(("RECEIVED_BACKROOM", "BACKROOM"))
        # Move to floor
        fixture = _pick_fixture_for_category(category, all_fixtures, rng)
        events.append(("MOVED_TO_FLOOR", fixture["id"]))
        current_zone = fixture["id"]
    else:
        # Already on floor — record initial placement
        events.append(("MOVED_TO_FLOOR", current_zone))

    # ── Compute modified probabilities ────────────────────────────────
    probs = dict(BASELINE_PROBS)

    # Placement modifier: directly set stays_on_fixture based on placement
    # This creates the dramatic front/back gap needed for story #4
    placement_stay = {
        "front":     0.25,  # 75% get picked up — high engagement
        "mid":       0.55,  # baseline
        "side":      0.60,
        "back":      0.88,  # only 12% get picked up — back wall (story #4: 4x gap)
        "near_exit": 0.50,
    }
    base_stay = placement_stay.get(fixture_placement, 0.55)
    # Scale other probabilities proportionally
    old_pickup = 1.0 - probs["stays_on_fixture"]
    new_pickup = 1.0 - base_stay
    if old_pickup > 0:
        scale = new_pickup / old_pickup
        for k in probs:
            if k != "stays_on_fixture":
                probs[k] *= scale
    probs["stays_on_fixture"] = base_stay

    # ── Planted story modifiers ───────────────────────────────────────

    # Story #1: SKU-4471 size M has 71% trial rejection
    if sku_id == "SKU-4471" and size == "M":
        probs["stays_on_fixture"] = 0.10
        probs["picked_returned"] = 0.05
        probs["picked_tried_rejected"] = 0.71
        probs["picked_tried_purchased"] = 0.10
        probs["picked_purchased_no_trial"] = 0.02
        probs["misplaced"] = 0.01
        probs["shrinkage"] = 0.01

    # Story #4: Front fixtures get 4x pickup vs back
    # (already handled via PLACEMENT_PICKUP_MULT above — front=1.8, back=0.5)

    # Story #5: Accessories near exit get heavy shrinkage
    if category == "Accessories" and fixture_placement == "near_exit":
        probs["shrinkage"] = 0.15
        probs["stays_on_fixture"] = max(0.05, probs["stays_on_fixture"] - 0.14)

    # Story #2: Women_Western Jeans size 28 — handled at inventory level
    # (lots of backroom stock, floor stock sells through fast)
    # Make these units sell faster to create the stockout
    if category == "Women_Western" and size == "28":
        probs["stays_on_fixture"] = 0.30
        probs["picked_tried_purchased"] = 0.20
        probs["picked_purchased_no_trial"] = 0.08
        probs["picked_tried_rejected"] = 0.15
        probs["picked_returned"] = 0.20
        probs["misplaced"] = 0.05
        probs["shrinkage"] = 0.02

    # Accessories: more "purchase without trial"
    if category == "Accessories":
        probs["picked_purchased_no_trial"] = 0.15
        probs["picked_tried_purchased"] = 0.02
        probs["picked_tried_rejected"] = 0.03
        trial_reduction = 0.15 - BASELINE_PROBS["picked_purchased_no_trial"]
        probs["stays_on_fixture"] = max(0.1, probs["stays_on_fixture"] - trial_reduction)

    # Normalize
    total = sum(probs.values())
    probs = {k: v / total for k, v in probs.items()}

    # ── Sample path type ──────────────────────────────────────────────
    path_types = list(probs.keys())
    path_probs = [probs[k] for k in path_types]
    path_type = rng.choice(path_types, p=path_probs)

    fixture_zone = current_zone  # where the item is on the floor

    if path_type == "stays_on_fixture":
        # No further events — item stays on fixture all period
        pass

    elif path_type == "picked_returned":
        events.append(("PICKED_UP", fixture_zone))
        events.append(("BASKET_DWELL", fixture_zone))
        events.append(("RETURNED_TO_FIXTURE", fixture_zone))

    elif path_type == "picked_tried_rejected":
        events.append(("PICKED_UP", fixture_zone))
        events.append(("BASKET_DWELL", fixture_zone))
        events.append(("ENTERED_TRIAL", "TRIAL"))
        events.append(("EXITED_TRIAL_REJECTED", "TRIAL"))
        # Return to same or different fixture
        if rng.random() < 0.3:
            # Misplaced after rejection (put on wrong fixture)
            wrong_fixture = _pick_different_fixture(fixture_zone, all_fixtures, rng)
            events.append(("RETURNED_TO_FIXTURE", wrong_fixture))
        else:
            events.append(("RETURNED_TO_FIXTURE", fixture_zone))

    elif path_type == "picked_tried_purchased":
        events.append(("PICKED_UP", fixture_zone))
        events.append(("BASKET_DWELL", fixture_zone))
        events.append(("ENTERED_TRIAL", "TRIAL"))
        events.append(("EXITED_TRIAL_PURCHASED", "TRIAL"))
        till = rng.choice(["TILL_1", "TILL_2"])
        events.append(("SOLD_AT_TILL", till))
        events.append(("EXITED_STORE", "EXIT"))

    elif path_type == "picked_purchased_no_trial":
        events.append(("PICKED_UP", fixture_zone))
        events.append(("BASKET_DWELL", fixture_zone))
        till = rng.choice(["TILL_1", "TILL_2"])
        events.append(("SOLD_AT_TILL", till))
        events.append(("EXITED_STORE", "EXIT"))

    elif path_type == "misplaced":
        events.append(("PICKED_UP", fixture_zone))
        wrong_fixture = _pick_different_fixture(fixture_zone, all_fixtures, rng)
        events.append(("MISPLACED", wrong_fixture))

    elif path_type == "shrinkage":
        events.append(("PICKED_UP", fixture_zone))
        events.append(("EXITED_WITHOUT_SALE", "EXIT"))

    return events


def _pick_fixture_for_category(
    category: str, fixtures: list[dict], rng: np.random.Generator
) -> dict:
    """Pick a fixture zone matching the category."""
    matching = [f for f in fixtures if f.get("category") == category]
    if not matching:
        matching = [f for f in fixtures if f["type"] == "fixture"]
    return rng.choice(matching)


def _pick_different_fixture(
    current_fixture: str, fixtures: list[dict], rng: np.random.Generator
) -> str:
    """Pick a random fixture that isn't the current one."""
    candidates = [f["id"] for f in fixtures if f["type"] == "fixture" and f["id"] != current_fixture]
    if not candidates:
        return current_fixture
    return rng.choice(candidates)
