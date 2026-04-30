"""
Build tag inventory: ~7000 RFID-tagged units mapped to SKUs.
70% start on their assigned fixture, 30% in BACKROOM.
Plants: Women_Western Jeans size 28 gets 60+ backroom tags for stockout-while-stocked story.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(43)

DATA_DIR = Path(__file__).parent.parent / "data"
LAYOUT_PATH = Path(__file__).parent / "store_layout.json"

# Target ~7000 tags total
UNITS_PER_SKU_BASE = 18  # will vary by category


def _get_fixture_for_category(category: str, zones: list[dict]) -> list[str]:
    """Get fixture zone IDs for a given category."""
    return [z["id"] for z in zones if z.get("category") == category]


def build_inventory() -> pd.DataFrame:
    catalog = pd.read_parquet(DATA_DIR / "product_catalog.parquet")
    with open(LAYOUT_PATH) as f:
        layout = json.load(f)
    zones = layout["zones"]

    rows = []
    tag_counter = 0

    # Group catalog by unique SKU+size combos
    sku_groups = catalog.groupby(["sku_id", "size"])

    for (sku_id, size), group in sku_groups:
        row = group.iloc[0]
        category = row["category"]
        fixtures = _get_fixture_for_category(category, zones)

        if not fixtures:
            continue

        # Vary units per SKU-size combo
        if category == "Accessories":
            n_units = np.random.randint(8, 15)
        elif category == "Kids":
            n_units = np.random.randint(10, 18)
        else:
            n_units = np.random.randint(14, 25)

        # ── Planted story: Women_Western Jeans size 28 gets extra backroom stock ──
        is_stockout_sku = (
            category == "Women_Western"
            and row["sub_category"] == "Jeans"
            and size == "28"
        )
        if is_stockout_sku:
            n_units = 80  # lots of units, mostly backroom

        for _ in range(n_units):
            tag_counter += 1
            tag_id = f"TAG-{tag_counter:06d}"

            # Decide initial zone: 70% on fixture, 30% backroom
            # Exception: stockout SKU gets 75% backroom
            if is_stockout_sku:
                on_floor = np.random.random() < 0.25
            else:
                on_floor = np.random.random() < 0.70

            if on_floor:
                initial_zone = np.random.choice(fixtures)
            else:
                initial_zone = "BACKROOM"

            rows.append({
                "tag_id": tag_id,
                "sku_id": sku_id,
                "size": size,
                "category": category,
                "initial_zone": initial_zone,
                "status": "active",
            })

    df = pd.DataFrame(rows)

    # Validate
    print(f"Tag inventory built: {len(df)} tags")
    print(f"By category: {df['category'].value_counts().to_dict()}")
    print(f"Floor vs backroom: {df['initial_zone'].apply(lambda z: 'floor' if z != 'BACKROOM' else 'backroom').value_counts().to_dict()}")

    # Check planted story
    stockout_tags = df[
        (df["category"] == "Women_Western")
        & (df["size"] == "28")
        & (df["sku_id"].isin(
            catalog[
                (catalog["category"] == "Women_Western")
                & (catalog["sub_category"] == "Jeans")
            ]["sku_id"]
        ))
    ]
    br_count = (stockout_tags["initial_zone"] == "BACKROOM").sum()
    print(f"Women_Western Jeans size-28 backroom tags: {br_count}")

    # Check SKU-4471 tags
    sku4471 = df[df["sku_id"] == "SKU-4471"]
    print(f"SKU-4471 tags: {len(sku4471)}, sizes: {sku4471['size'].value_counts().to_dict()}")

    df.to_parquet(DATA_DIR / "tag_inventory.parquet", index=False)
    print(f"Written to {DATA_DIR / 'tag_inventory.parquet'}")
    return df


if __name__ == "__main__":
    build_inventory()
