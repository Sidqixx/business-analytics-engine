from __future__ import annotations
import pandas as pd

def get_product_catalog()->pd.DataFrame:
    """

    Return the product used by the synthetic F&B Business.

    Returns
    -----
    pd.Dataframe
        Columns:
        - product
        - category
        - base_price
        - base_cost
        - demand_weight
    """

    products =[
        {
            "product": "Nasi Goreng",
            "category": "Food",
            "base_price": 25_000,
            "base_cost": 13_000,
            "demand_weight": 10,
        },
        {
            "product": "Mie Goreng",
            "category": "Food",
            "base_price": 23_000,
            "base_cost": 12_000,
            "demand_weight": 8,
        },
        {
            "product": "Ayam Geprek",
            "category": "Food",
            "base_price": 22_000,
            "base_cost": 12_000,
            "demand_weight": 12,
        },
        {
            "product": "Ayam Bakar",
            "category": "Food",
            "base_price": 27_000,
            "base_cost": 15_000,
            "demand_weight": 7,
        },
        {
            "product": "Nasi Ayam",
            "category": "Food",
            "base_price": 24_000,
            "base_cost": 13_000,
            "demand_weight": 9,
        },
        {
            "product": "Mie Ayam",
            "category": "Food",
            "base_price": 20_000,
            "base_cost": 10_000,
            "demand_weight": 8,
        },
        {
            "product": "Es Teh",
            "category": "Beverage",
            "base_price": 6_000,
            "base_cost": 2_000,
            "demand_weight": 15,
        },
        {
            "product": "Es Jeruk",
            "category": "Beverage",
            "base_price": 8_000,
            "base_cost": 3_000,
            "demand_weight": 9,
        },
        {
            "product": "Kopi Susu",
            "category": "Beverage",
            "base_price": 15_000,
            "base_cost": 7_000,
            "demand_weight": 8,
        },
        {
            "product": "Kopi Hitam",
            "category": "Beverage",
            "base_price": 10_000,
            "base_cost": 4_000,
            "demand_weight": 4,
        },
        {
            "product": "Air Mineral",
            "category": "Beverage",
            "base_price": 5_000,
            "base_cost": 3_000,
            "demand_weight": 7,
        },
        {
            "product": "Kentang Goreng",
            "category": "Snack",
            "base_price": 15_000,
            "base_cost": 7_000,
            "demand_weight": 4,
        },
        {
            "product": "Tahu Crispy",
            "category": "Snack",
            "base_price": 12_000,
            "base_cost": 5_500,
            "demand_weight": 5,
        },
        {
            "product": "Pisang Goreng",
            "category": "Snack",
            "base_price": 12_000,
            "base_cost": 5_000,
            "demand_weight": 6,
        },
        {
            "product": "Puding Coklat",
            "category": "Dessert",
            "base_price": 10_000,
            "base_cost": 5_000,
            "demand_weight": 3,
        },

    ]

    catalog= pd.DataFrame(products)

    #Basic Validation to catch accidental catalog errors early.
    required_columns={
        "product",
        "category",
        "base_price",
        "base_cost",
        "demand_weight",
    }

    missing_columns = required_columns - set(catalog.columns)
    if missing_columns:
        raise ValueError(
            f"Missing required catalog columns: {sorted(missing_columns)}"
        )

    if catalog["product"].duplicated().any():
       duplicated=catalog.loc[
          catalog["product"].duplicated(), "product"
       ].tolist()
       raise ValueError(f"Duplicate products found:{duplicated}")

    if (catalog["base_price"] <= 0).any():
        raise ValueError("All base prices must be greater than 0.")

    if (catalog["base_cost"] < 0).any():
        raise ValueError("Base cost cannot be negative.")

    if (catalog["demand_weight"] <= 0).any():
        raise ValueError("Demand weights must be greater than 0.")

    return catalog

if __name__ == "__main__":
    df_catalog = get_product_catalog()

    print("Product Catalog")
    print("=" * 60)
    print(df_catalog.to_string(index=False))
    print("\nTotal products:", len(df_catalog))
    print("Total demand weight:", df_catalog["demand_weight"].sum())

    
