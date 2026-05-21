import numpy as np
import pandas as pd
from pathlib import Path

OUTPUT_FILE = Path(__file__).resolve().parent / "marketing_data.xlsx"


def generate_marketing_data(num_rows: int = 500, export_excel: bool = True) -> pd.DataFrame:
    """Generate a realistic marketing dataset and optionally export it to Excel."""
    platforms = ["Meta", "Google", "LinkedIn"]
    audience_segments = [
        "Tech Bros 25-34",
        "Soccer Moms",
        "Growth Founders",
        "E-commerce Shoppers",
        "Beauty Enthusiasts",
        "Fitness Fanatics",
        "Finance Professionals",
        "Urban Explorers",
        "Home Decor Lovers",
        "B2B Decision Makers",
    ]
    creatives = [
        "Spring Launch",
        "Holiday Special",
        "Limited Offer",
        "Customer Success",
        "New Arrival",
        "Conversion Booster",
        "Brand Awareness",
        "Seasonal Deal",
        "Storytelling Video",
        "Lead Magnet",
    ]

    rng = np.random.default_rng(42)

    data = []
    for i in range(num_rows):
        campaign_id = f"CMP-{1000 + i}"
        platform = rng.choice(platforms, p=[0.45, 0.40, 0.15])
        audience = rng.choice(audience_segments)
        creative = rng.choice(creatives)

        spend = float(np.round(rng.uniform(150, 4500), 2))
        impressions = int(rng.integers(5000, 180000))

        base_ctr = 0.008 if platform == "LinkedIn" else 0.015
        ctr_noise = rng.normal(0, 0.002)
        ctr = max(0.0005, base_ctr + ctr_noise)

        clicks = max(1, int(impressions * ctr))
        conversion_rate = 0.04 if platform == "Google" else 0.025
        conversions = max(1, int(clicks * conversion_rate * rng.uniform(0.6, 1.3)))

        cpa = spend / conversions
        roas = rng.uniform(1.6, 5.2)

        data.append(
            {
                "Campaign ID": campaign_id,
                "Platform": platform,
                "Audience Segment": audience,
                "Ad Creative Name": creative,
                "Spend ($)": spend,
                "Impressions": impressions,
                "Clicks": clicks,
                "Conversions": conversions,
                "CTR": clicks / impressions,
                "CPA": cpa,
                "ROAS": roas,
            }
        )

    df = pd.DataFrame(data)

    # Add deliberate poor performers for a few segments
    poor_segments = ["Tech Bros 25-34", "Soccer Moms", "Home Decor Lovers"]
    mask = df["Audience Segment"].isin(poor_segments)

    df.loc[mask, "CTR"] = df.loc[mask, "CTR"] * 0.35
    df.loc[mask, "CPA"] = df.loc[mask, "CPA"] * 2.5
    df.loc[mask, "ROAS"] = df.loc[mask, "ROAS"] * 0.75
    df.loc[mask, "Clicks"] = (df.loc[mask, "CTR"] * df.loc[mask, "Impressions"]).astype(int).clip(lower=1)
    df.loc[mask, "Conversions"] = (df.loc[mask, "Clicks"] * 0.02).astype(int).clip(lower=1)
    df.loc[mask, "CPA"] = df.loc[mask, "Spend ($)"].div(df.loc[mask, "Conversions"])

    df = df.round({"CTR": 5, "CPA": 2, "ROAS": 2})

    if export_excel:
        df.to_excel(OUTPUT_FILE, index=False)

    return df


if __name__ == "__main__":
    df = generate_marketing_data(500, export_excel=True)
    print(f"Generated {len(df)} rows and exported to {OUTPUT_FILE}")
