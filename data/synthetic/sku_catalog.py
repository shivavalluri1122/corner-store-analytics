"""Static product catalog for the synthetic Corner Store dataset.

Defines ~150 SKUs across 10 categories with realistic names and prices.
This module is deterministic: calling build_sku_catalog() twice returns
the exact same DataFrame, which keeps generated datasets reproducible.
"""

import random

import pandas as pd

# category -> (sku prefix, (min_price, max_price), list of item names)
CATEGORY_ITEMS: dict[str, tuple[str, tuple[float, float], list[str]]] = {
    "Beverages": (
        "BEV",
        (1.25, 4.50),
        [
            "Coca-Cola 20oz Bottle",
            "Diet Coke 20oz Bottle",
            "Sprite 20oz Bottle",
            "Pepsi 20oz Bottle",
            "Mountain Dew 20oz Bottle",
            "Gatorade Lemon-Lime 28oz",
            "Gatorade Fruit Punch 28oz",
            "Bottled Water 16.9oz",
            "Sparkling Water Lime 12oz",
            "Iced Tea Lemon 18.5oz",
            "Energy Drink Original 16oz",
            "Energy Drink Sugar-Free 16oz",
            "Orange Juice 12oz",
            "Chocolate Milk 14oz",
            "Iced Latte Bottle 13oz",
        ],
    ),
    "Snacks": (
        "SNK",
        (1.25, 4.00),
        [
            "Lay's Classic Chips 1oz",
            "Doritos Nacho Cheese 1oz",
            "Cheetos Crunchy 1oz",
            "Pretzels Snack Bag 1.5oz",
            "Popcorn Butter Bag 3oz",
            "Trail Mix Pouch 2oz",
            "Beef Jerky Original 2.85oz",
            "Pork Rinds 2.5oz",
            "Cheese Crackers Pack",
            "Peanut Butter Crackers Pack",
            "Tortilla Chips Family Size",
            "Veggie Straws 1oz",
            "Rice Cakes Snack Pack",
            "Mixed Nuts 1.5oz",
            "Pita Chips Sea Salt 1.5oz",
        ],
    ),
    "Candy": (
        "CDY",
        (0.99, 2.99),
        [
            "Snickers Bar",
            "M&M's Peanut Bag",
            "M&M's Plain Bag",
            "Reese's Peanut Butter Cups",
            "Skittles Original Bag",
            "Starburst Original Bag",
            "Kit Kat Bar",
            "Twix Bar",
            "Hershey's Milk Chocolate Bar",
            "Sour Patch Kids Bag",
            "Gummy Bears Bag",
            "Milky Way Bar",
            "3 Musketeers Bar",
            "Tic Tac Mints",
            "Life Savers Roll",
        ],
    ),
    "Dairy": (
        "DAI",
        (1.50, 7.50),
        [
            "Whole Milk 1 Gallon",
            "2% Milk 1 Gallon",
            "Whole Milk Half Gallon",
            "Large Eggs Dozen",
            "Butter Stick 4oz",
            "Shredded Cheddar Cheese 8oz",
            "String Cheese Pack",
            "Greek Yogurt Cup",
            "Vanilla Yogurt Cup",
            "Sour Cream 8oz",
            "Cream Cheese 8oz",
            "Half and Half Pint",
            "Cottage Cheese 16oz",
            "American Cheese Slices",
            "Heavy Whipping Cream Pint",
        ],
    ),
    "Bakery": (
        "BAK",
        (1.50, 6.00),
        [
            "White Sandwich Bread",
            "Wheat Sandwich Bread",
            "Bagels Plain 6-Pack",
            "Blueberry Muffin",
            "Chocolate Chip Muffin",
            "Glazed Donut",
            "Chocolate Donut",
            "Butter Croissant",
            "Dinner Rolls 8-Pack",
            "Cinnamon Roll",
            "Banana Bread Slice",
            "Pound Cake Slice",
            "Hamburger Buns 8-Pack",
            "Hot Dog Buns 8-Pack",
            "Flour Tortillas 10-Pack",
        ],
    ),
    "Frozen Foods": (
        "FRZ",
        (2.50, 9.00),
        [
            "Frozen Pepperoni Pizza",
            "Frozen Cheese Pizza",
            "Frozen Burritos 4-Pack",
            "Frozen French Fries Bag",
            "Frozen Chicken Nuggets Bag",
            "Frozen Mixed Vegetables Bag",
            "Frozen Waffles 8-Pack",
            "Frozen Breakfast Sandwich",
            "Frozen Ice Cream Sandwiches 6-Pack",
            "Frozen Vanilla Ice Cream Pint",
            "Frozen Chocolate Ice Cream Pint",
            "Frozen Corn Dogs 4-Pack",
            "Frozen Mozzarella Sticks Bag",
            "Frozen Pot Pie",
            "Frozen Popsicles 6-Pack",
        ],
    ),
    "Household & Cleaning": (
        "HHC",
        (1.50, 12.00),
        [
            "Paper Towels 2-Pack",
            "Toilet Paper 4-Pack",
            "Dish Soap 12oz",
            "Laundry Detergent Small",
            "All-Purpose Cleaner Spray",
            "Trash Bags 13-Gallon 10-Pack",
            "Sponges 3-Pack",
            "Aluminum Foil Roll",
            "Plastic Wrap Roll",
            "Sandwich Bags Box",
            "Air Freshener Spray",
            "Batteries AA 4-Pack",
            "LED Light Bulbs 2-Pack",
            "Matches Box",
            "Lighter Fluid",
        ],
    ),
    "Personal Care": (
        "PCR",
        (1.50, 9.00),
        [
            "Toothpaste Tube",
            "Toothbrush Single",
            "Mouthwash 8oz",
            "Bar Soap 2-Pack",
            "Travel Size Shampoo",
            "Deodorant Stick",
            "Hand Sanitizer 2oz",
            "Facial Tissues Box",
            "Disposable Razors 2-Pack",
            "Cotton Swabs Box",
            "Band-Aids Box",
            "Lip Balm",
            "Hair Gel Small",
            "Travel Size Body Wash",
            "Travel Wet Wipes Pack",
        ],
    ),
    "Grocery & Pantry": (
        "GRO",
        (0.99, 6.50),
        [
            "White Rice 2lb Bag",
            "Spaghetti Pasta Box",
            "Pasta Sauce Jar",
            "Canned Black Beans",
            "Canned Corn",
            "Canned Tuna",
            "Peanut Butter Jar",
            "Grape Jelly Jar",
            "Cereal Small Box",
            "Instant Oatmeal Packets",
            "Instant Ramen Noodles",
            "Cooking Oil Small Bottle",
            "Ketchup Bottle",
            "Hot Sauce Bottle",
            "Sugar 2lb Bag",
        ],
    ),
    "Health & OTC": (
        "HOT",
        (2.50, 14.00),
        [
            "Ibuprofen Tablets Small Bottle",
            "Acetaminophen Tablets Small Bottle",
            "Allergy Relief Tablets",
            "Cough Drops Bag",
            "Antacid Tablets Roll",
            "Vitamin C Tablets Bottle",
            "Small Multivitamin Bottle",
            "Electrolyte Powder Packet",
            "First Aid Spray",
            "Reading Glasses +2.0",
            "Face Masks 5-Pack",
            "Digital Thermometer",
            "Nasal Spray",
            "Eye Drops Bottle",
            "Antibacterial Ointment Tube",
        ],
    ),
}

CATALOG_SEED = 42


def _priced(rng: random.Random, lo: float, hi: float) -> float:
    """Random price in [lo, hi], rounded to end in .49 or .99 like real shelf prices."""
    raw = rng.uniform(lo, hi)
    dollars = int(raw)
    cents = rng.choice([0.49, 0.99])
    price = dollars + cents
    return round(max(lo, min(hi, price)), 2)


def build_sku_catalog(seed: int = CATALOG_SEED) -> pd.DataFrame:
    """Build the ~150 SKU catalog as a DataFrame with columns:
    sku, item, category, unit_price.
    """
    rng = random.Random(seed)
    rows = []
    for category, (prefix, price_range, items) in CATEGORY_ITEMS.items():
        for i, item_name in enumerate(items, start=1):
            sku = f"{prefix}-{i:03d}"
            rows.append(
                {
                    "sku": sku,
                    "item": item_name,
                    "category": category,
                    "unit_price": _priced(rng, *price_range),
                }
            )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    catalog = build_sku_catalog()
    print(f"Built {len(catalog)} SKUs across {catalog['category'].nunique()} categories")
    print(catalog.head(20))
