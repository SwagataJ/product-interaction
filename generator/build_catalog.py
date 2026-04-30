"""
Build a realistic product catalog modeled on Westside (Trent Ltd) offerings.
Produces product_catalog.parquet with ~350 SKUs across Westside's actual brand portfolio.
"""

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ─── Westside Brand & Category Definitions ───────────────────────────────────
# Based on actual Westside brand portfolio and pricing (2025-2026)

CATALOG_SPEC = {
    "Women_Western": {
        "sub_categories": {
            "Casual_Top": {
                "brands": ["LOV", "Nuon", "Wardrobe"],
                "sizes": ["XS", "S", "M", "L", "XL"],
                "fits": ["Regular", "Relaxed", "Slim"],
                "price_range": (499, 1699),
                "cost_ratio": 0.35,
                "count": 30,
            },
            "T_Shirt": {
                "brands": ["Nuon", "Studiofit", "LOV"],
                "sizes": ["XS", "S", "M", "L", "XL"],
                "fits": ["Regular", "Relaxed", "Oversized"],
                "price_range": (499, 999),
                "cost_ratio": 0.30,
                "count": 20,
            },
            "Dress": {
                "brands": ["LOV", "Bombay Paisley", "Wardrobe"],
                "sizes": ["XS", "S", "M", "L", "XL"],
                "fits": ["Regular", "A-Line", "Bodycon"],
                "price_range": (999, 2499),
                "cost_ratio": 0.35,
                "count": 20,
            },
            "Jeans": {
                "brands": ["Nuon", "LOV"],
                "sizes": ["26", "28", "30", "32", "34"],
                "fits": ["Slim", "Relaxed", "Skinny", "Wide-Leg"],
                "price_range": (1299, 1699),
                "cost_ratio": 0.35,
                "count": 18,
            },
            "Trousers": {
                "brands": ["Wardrobe", "LOV", "Nuon"],
                "sizes": ["26", "28", "30", "32", "34"],
                "fits": ["Regular", "Slim", "Wide-Leg"],
                "price_range": (999, 1499),
                "cost_ratio": 0.35,
                "count": 12,
            },
        },
    },
    "Women_Ethnic": {
        "sub_categories": {
            "Kurta": {
                "brands": ["Utsa", "Bombay Paisley", "Vark", "Diza"],
                "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
                "fits": ["Regular", "A-Line", "Straight"],
                "price_range": (699, 2599),
                "cost_ratio": 0.35,
                "count": 35,
            },
            "Ethnic_Top": {
                "brands": ["Utsa", "Bombay Paisley"],
                "sizes": ["XS", "S", "M", "L", "XL"],
                "fits": ["Regular", "Relaxed"],
                "price_range": (599, 1499),
                "cost_ratio": 0.35,
                "count": 15,
            },
            "Ethnic_Bottom": {
                "brands": ["Utsa", "Bombay Paisley", "Vark"],
                "sizes": ["26", "28", "30", "32", "34"],
                "fits": ["Regular", "Relaxed"],
                "price_range": (599, 1299),
                "cost_ratio": 0.35,
                "count": 12,
            },
        },
    },
    "Men_Casual": {
        "sub_categories": {
            "Casual_Shirt": {
                "brands": ["ETA", "WES Casuals", "Nuon"],
                "sizes": ["S", "M", "L", "XL", "XXL"],
                "fits": ["Slim", "Regular", "Relaxed"],
                "price_range": (999, 1499),
                "cost_ratio": 0.35,
                "count": 30,
            },
            "T_Shirt": {
                "brands": ["ETA", "Nuon", "Studiofit"],
                "sizes": ["S", "M", "L", "XL", "XXL"],
                "fits": ["Regular", "Relaxed", "Oversized"],
                "price_range": (799, 1299),
                "cost_ratio": 0.30,
                "count": 25,
            },
            "Polo": {
                "brands": ["ETA", "Ascot"],
                "sizes": ["S", "M", "L", "XL", "XXL"],
                "fits": ["Regular", "Slim"],
                "price_range": (799, 1299),
                "cost_ratio": 0.35,
                "count": 12,
            },
            "Jeans": {
                "brands": ["Nuon", "Ascot", "WES Casuals"],
                "sizes": ["28", "30", "32", "34", "36"],
                "fits": ["Slim", "Relaxed", "Skinny", "Barrel"],
                "price_range": (1299, 1699),
                "cost_ratio": 0.35,
                "count": 20,
            },
            "Chinos": {
                "brands": ["ETA", "Ascot", "WES Casuals"],
                "sizes": ["28", "30", "32", "34", "36"],
                "fits": ["Slim", "Regular", "Relaxed"],
                "price_range": (1299, 1499),
                "cost_ratio": 0.35,
                "count": 12,
            },
        },
    },
    "Men_Formal": {
        "sub_categories": {
            "Formal_Shirt": {
                "brands": ["WES Formals", "Ascot"],
                "sizes": ["S", "M", "L", "XL", "XXL"],
                "fits": ["Slim", "Regular"],
                "price_range": (1299, 1999),
                "cost_ratio": 0.40,
                "count": 18,
            },
            "Formal_Trousers": {
                "brands": ["WES Formals", "Ascot"],
                "sizes": ["28", "30", "32", "34", "36"],
                "fits": ["Slim", "Regular"],
                "price_range": (1299, 1999),
                "cost_ratio": 0.40,
                "count": 12,
            },
        },
    },
    "Kids": {
        "sub_categories": {
            "Girls_Top": {
                "brands": ["HOP Kids", "Y&F Girls"],
                "sizes": ["3-4Y", "5-6Y", "7-8Y", "9-10Y", "11-12Y", "13-14Y"],
                "fits": ["Regular"],
                "price_range": (399, 799),
                "cost_ratio": 0.30,
                "count": 15,
            },
            "Girls_Dress": {
                "brands": ["HOP Kids", "Y&F Girls"],
                "sizes": ["3-4Y", "5-6Y", "7-8Y", "9-10Y", "11-12Y", "13-14Y"],
                "fits": ["Regular", "A-Line"],
                "price_range": (599, 1299),
                "cost_ratio": 0.30,
                "count": 12,
            },
            "Boys_Shirt": {
                "brands": ["HOP Kids", "Y&F Boys"],
                "sizes": ["3-4Y", "5-6Y", "7-8Y", "9-10Y", "11-12Y", "13-14Y"],
                "fits": ["Regular"],
                "price_range": (499, 999),
                "cost_ratio": 0.30,
                "count": 12,
            },
            "Boys_T_Shirt": {
                "brands": ["HOP Kids", "Y&F Boys"],
                "sizes": ["3-4Y", "5-6Y", "7-8Y", "9-10Y", "11-12Y", "13-14Y"],
                "fits": ["Regular"],
                "price_range": (399, 599),
                "cost_ratio": 0.30,
                "count": 12,
            },
        },
    },
    "Accessories": {
        "sub_categories": {
            "Hair_Accessories": {
                "brands": ["Studiowest"],
                "sizes": ["ONE_SIZE"],
                "fits": ["ONE_SIZE"],
                "price_range": (195, 399),
                "cost_ratio": 0.25,
                "count": 10,
            },
            "Bags_Pouches": {
                "brands": ["Studiowest"],
                "sizes": ["ONE_SIZE"],
                "fits": ["ONE_SIZE"],
                "price_range": (599, 1299),
                "cost_ratio": 0.30,
                "count": 8,
            },
            "Scarves_Stoles": {
                "brands": ["Bombay Paisley", "Utsa"],
                "sizes": ["ONE_SIZE"],
                "fits": ["ONE_SIZE"],
                "price_range": (499, 999),
                "cost_ratio": 0.30,
                "count": 6,
            },
            "Fashion_Jewellery": {
                "brands": ["Studiowest"],
                "sizes": ["ONE_SIZE"],
                "fits": ["ONE_SIZE"],
                "price_range": (295, 799),
                "cost_ratio": 0.20,
                "count": 8,
            },
        },
    },
}

COLORS = [
    "Black", "White", "Navy", "Charcoal", "Grey", "Beige", "Off-White",
    "Olive", "Rust", "Maroon", "Teal", "Sage", "Mustard", "Coral",
    "Light Blue", "Dark Blue", "Pink", "Red", "Cream", "Taupe",
    "Indigo", "Forest Green", "Lavender", "Peach",
]

# ─── Planted story: SKU-4471 is a Men's Casual Slim Fit Shirt (ETA) ──────────
# with a fit issue in size M — high trial rejection rate
PLANTED_SKU_4471_ID = "SKU-4471"


def _round_price(price: float) -> int:
    """Round to Westside-style price points: 99-ending."""
    base = int(price / 100) * 100
    return base - 1 if base > 100 else max(99, int(price))


def build_catalog() -> pd.DataFrame:
    rows = []
    sku_counter = 1000

    for category, cat_spec in CATALOG_SPEC.items():
        for sub_cat, spec in cat_spec["sub_categories"].items():
            for i in range(spec["count"]):
                sku_counter += 1
                sku_id = f"SKU-{sku_counter}"

                brand = np.random.choice(spec["brands"])
                color = np.random.choice(COLORS)
                size = np.random.choice(spec["sizes"])
                fit = np.random.choice(spec["fits"])

                lo, hi = spec["price_range"]
                price = _round_price(np.random.uniform(lo, hi))
                unit_cost = round(price * spec["cost_ratio"], 2)

                rows.append({
                    "sku_id": sku_id,
                    "category": category,
                    "sub_category": sub_cat,
                    "brand": brand,
                    "color": color,
                    "size": size,
                    "fit": fit,
                    "price_inr": price,
                    "unit_cost_inr": unit_cost,
                })

    df = pd.DataFrame(rows)

    # ── Plant SKU-4471: ETA Men's Slim Fit Casual Shirt ──
    # We need it across ALL sizes so we can show the fit issue in size M
    planted_rows = []
    for size in ["S", "M", "L", "XL", "XXL"]:
        planted_rows.append({
            "sku_id": PLANTED_SKU_4471_ID,
            "category": "Men_Casual",
            "sub_category": "Casual_Shirt",
            "brand": "ETA",
            "color": "Navy",
            "size": size,
            "fit": "Slim",
            "price_inr": 1299,
            "unit_cost_inr": round(1299 * 0.35, 2),
        })

    planted_df = pd.DataFrame(planted_rows)
    df = pd.concat([df, planted_df], ignore_index=True)

    print(f"Catalog built: {len(df)} rows")
    print(f"Categories: {df['category'].value_counts().to_dict()}")
    print(f"SKU-4471 sizes: {df[df['sku_id'] == PLANTED_SKU_4471_ID]['size'].tolist()}")

    df.to_parquet(DATA_DIR / "product_catalog.parquet", index=False)
    print(f"Written to {DATA_DIR / 'product_catalog.parquet'}")
    return df


if __name__ == "__main__":
    build_catalog()
