"""
Timestamp sampler for journey events.
Generates realistic timestamps with intra-day patterns (lunch/evening peaks, weekend surges).
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Optional

# Simulation window
SIM_START = datetime(2026, 4, 13)  # Monday
SIM_DAYS = 14
SIM_END = SIM_START + timedelta(days=SIM_DAYS)

TRADING_OPEN_HOUR = 10
TRADING_CLOSE_HOUR = 22


def _intraday_weight(hour: float) -> float:
    """
    Weight for customer activity by hour-of-day.
    Peaks at lunch (12-14) and evening (18-21).
    """
    if hour < TRADING_OPEN_HOUR or hour >= TRADING_CLOSE_HOUR:
        return 0.0
    if 12 <= hour < 14:
        return 1.5  # lunch micro-peak
    if 18 <= hour < 21:
        return 3.0  # evening peak
    if 14 <= hour < 18:
        return 1.0  # afternoon baseline
    if 10 <= hour < 12:
        return 0.6  # morning warm-up
    if 21 <= hour < 22:
        return 1.8  # late evening
    return 0.5


def _is_weekend(dt: datetime) -> bool:
    return dt.weekday() in (5, 6)  # Saturday, Sunday


def sample_journey_day(rng: np.random.Generator) -> datetime:
    """Sample a random day within the simulation window, biased toward weekends."""
    days = []
    weights = []
    for d in range(SIM_DAYS):
        dt = SIM_START + timedelta(days=d)
        days.append(dt)
        weights.append(1.5 if _is_weekend(dt) else 1.0)

    weights = np.array(weights) / sum(weights)
    return rng.choice(days, p=weights)


def sample_pickup_time(day: datetime, rng: np.random.Generator) -> datetime:
    """
    Sample a realistic pickup timestamp during trading hours.
    Biased toward evening peak.
    """
    # Build hour-level weights
    hours = np.arange(TRADING_OPEN_HOUR, TRADING_CLOSE_HOUR, 0.25)
    weights = np.array([_intraday_weight(h) for h in hours])

    # Weekend surge
    if _is_weekend(day):
        weights *= 1.4

    weights /= weights.sum()
    hour = rng.choice(hours, p=weights)

    # Add minute-level jitter
    minute = rng.integers(0, 60)
    second = rng.integers(0, 60)

    return day.replace(
        hour=int(hour),
        minute=minute,
        second=second,
        microsecond=0,
    )


def sample_backroom_dwell(rng: np.random.Generator) -> timedelta:
    """Gamma(shape=2, scale=12) hours, clipped [4, 96]."""
    hours = rng.gamma(2, 12)
    hours = np.clip(hours, 4, 96)
    return timedelta(hours=float(hours))


def sample_floor_dwell(rng: np.random.Generator) -> timedelta:
    """Exponential(scale=8) hours, clipped [0.1, 168]."""
    hours = rng.exponential(8)
    hours = np.clip(hours, 0.1, 168)
    return timedelta(hours=float(hours))


def sample_basket_dwell(rng: np.random.Generator) -> timedelta:
    """Normal(mean=4, std=2) minutes, clipped [0.5, 20]."""
    minutes = rng.normal(4, 2)
    minutes = np.clip(minutes, 0.5, 20)
    return timedelta(minutes=float(minutes))


def sample_trial_dwell(rng: np.random.Generator) -> timedelta:
    """Normal(mean=5, std=2) minutes, clipped [1, 15]."""
    minutes = rng.normal(5, 2)
    minutes = np.clip(minutes, 1, 15)
    return timedelta(minutes=float(minutes))


def sample_till_to_exit(rng: np.random.Generator) -> timedelta:
    """Normal(mean=60, std=20) seconds, clipped [10, 300]."""
    seconds = rng.normal(60, 20)
    seconds = np.clip(seconds, 10, 300)
    return timedelta(seconds=float(seconds))


def assign_timestamps(
    events: list[tuple[str, Optional[str]]],
    day: datetime,
    rng: np.random.Generator,
    is_planted_saturday_drop: bool = False,
) -> list[dict]:
    """
    Assign timestamps to a journey event sequence.
    Returns list of dicts with event_type, zone_to, timestamp.
    """
    timestamped = []
    current_time = None

    for i, (event_type, zone_to) in enumerate(events):
        if event_type == "RECEIVED_BACKROOM":
            # Backroom receipt happens before the journey day
            dwell = sample_backroom_dwell(rng)
            pickup_time = sample_pickup_time(day, rng)
            current_time = pickup_time - dwell
            # Clamp to sim window
            if current_time < SIM_START:
                current_time = SIM_START + timedelta(hours=rng.uniform(1, 24))

        elif event_type == "MOVED_TO_FLOOR":
            if current_time is None:
                # Item was already on floor — timestamp is start of day
                current_time = day.replace(
                    hour=TRADING_OPEN_HOUR,
                    minute=rng.integers(0, 30),
                    second=rng.integers(0, 60),
                )
            else:
                # Moved from backroom — add a small delay
                current_time += timedelta(minutes=rng.uniform(5, 30))

        elif event_type == "PICKED_UP":
            if current_time.hour < TRADING_OPEN_HOUR:
                current_time = sample_pickup_time(day, rng)
            else:
                # Add floor dwell time but keep within trading hours
                dwell = sample_floor_dwell(rng)
                candidate = current_time + dwell
                # If it goes past close, re-sample within trading hours
                close_time = day.replace(hour=TRADING_CLOSE_HOUR, minute=0)
                if candidate >= close_time:
                    current_time = sample_pickup_time(day, rng)
                    # Ensure it's after the previous event
                    if timestamped and current_time <= timestamped[-1]["timestamp"]:
                        current_time = timestamped[-1]["timestamp"] + timedelta(minutes=rng.uniform(5, 60))
                else:
                    current_time = candidate

            # Story #3: Saturday trial drop — suppress most activity
            # during 12:00-18:00 on the planted Saturday (simulates trial room
            # maintenance closure + reduced staff)
            if is_planted_saturday_drop and 12 <= current_time.hour < 18:
                # 85% chance of skipping this pickup entirely
                if rng.random() < 0.85:
                    return timestamped  # truncate journey here

        elif event_type == "BASKET_DWELL":
            current_time += sample_basket_dwell(rng)

        elif event_type == "ENTERED_TRIAL":
            current_time += timedelta(minutes=rng.uniform(0.5, 2))

        elif event_type in ("EXITED_TRIAL_REJECTED", "EXITED_TRIAL_PURCHASED"):
            current_time += sample_trial_dwell(rng)

        elif event_type == "RETURNED_TO_FIXTURE":
            current_time += timedelta(minutes=rng.uniform(1, 5))

        elif event_type == "SOLD_AT_TILL":
            current_time += timedelta(minutes=rng.uniform(2, 8))

        elif event_type == "EXITED_STORE":
            current_time += sample_till_to_exit(rng)

        elif event_type == "EXITED_WITHOUT_SALE":
            current_time += timedelta(minutes=rng.uniform(1, 10))

        elif event_type == "MISPLACED":
            current_time += timedelta(minutes=rng.uniform(5, 60))

        else:
            current_time += timedelta(minutes=rng.uniform(1, 5))

        timestamped.append({
            "event_type": event_type,
            "zone_to": zone_to,
            "timestamp": current_time,
        })

    return timestamped
