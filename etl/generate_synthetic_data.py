#!/usr/bin/env python3
"""
Synthetic data generator for the Global E‑Commerce BI project.
Creates customers.csv, marketing.csv, orders.csv, returns.csv.

Usage:
    python generate_synthetic_data.py
"""
import numpy as np
import pandas as pd
from pathlib import Path

def main(output_dir="data/raw", seed=42):
    rng = np.random.default_rng(seed)

    start_date = pd.Timestamp("2023-01-01")
    end_date   = pd.Timestamp("2025-08-31")
    dates = pd.date_range(start_date, end_date, freq="D")

    regions = {
        "EU": ["Germany", "France", "Italy", "Spain", "Netherlands", "Poland", "Sweden"],
        "NA": ["United States", "Canada", "Mexico"],
        "APAC": ["Japan", "Australia", "Singapore", "India", "South Korea"]
    }
    channels = ["Paid Search", "Social", "Email", "Affiliate", "Direct"]

    region_sla = {"EU": 5, "NA": 6, "APAC": 8}
    region_lead_mu = {"EU": 3.0, "NA": 4.0, "APAC": 6.0}
    region_lead_sigma = {"EU": 1.0, "NA": 1.5, "APAC": 2.0}

    month_mult = {1:0.9,2:0.92,3:1.0,4:1.02,5:1.05,6:1.08,7:1.0,8:0.98,9:1.05,10:1.15,11:1.35,12:1.5}
    weekday_mult = {0:1.0,1:1.02,2:1.02,3:1.03,4:1.05,5:0.95,6:0.9}
    base_daily_orders = {"EU": 220, "NA": 170, "APAC": 140}

    # Customers
    n_customers = 50000
    def sample_country():
        region_weights = np.array([0.5, 0.3, 0.2])
        reg = rng.choice(list(regions.keys()), p=region_weights)
        country = rng.choice(regions[reg])
        return reg, country

    cust_ids = np.arange(1, n_customers + 1)
    cust_signup_dates = rng.choice(dates, size=n_customers, replace=True)
    cust_region, cust_country = [], []
    for _ in range(n_customers):
        r, c = sample_country()
        cust_region.append(r); cust_country.append(c)
    segments = ["New", "Returning", "VIP"]
    segment_probs = [0.6, 0.35, 0.05]
    customers = pd.DataFrame({
        "customer_id": cust_ids,
        "signup_date": cust_signup_dates,
        "region": cust_region,
        "country": cust_country,
        "segment": rng.choice(segments, size=n_customers, p=segment_probs)
    })

    # Marketing
    rows = []
    for dt in dates:
        m_mult = month_mult[dt.month]
        for reg in regions.keys():
            for ch in channels:
                ch_base = {"Paid Search":1200,"Social":900,"Email":300,"Affiliate":400,"Direct":100}[ch]
                reg_mult = {"EU":1.0,"NA":0.85,"APAC":0.7}[reg]
                spend = rng.normal(ch_base*m_mult*reg_mult, ch_base*0.15)
                spend = max(50, spend)
                ch_eff = {"Paid Search":3.5,"Social":4.2,"Email":2.0,"Affiliate":3.0,"Direct":1.5}[ch]
                sessions = int(max(100, rng.normal(spend*ch_eff, spend*ch_eff*0.2)))
                rows.append([dt.date(), reg, ch, round(spend,2), sessions])
    marketing = pd.DataFrame(rows, columns=["date","region","channel","spend","sessions"])

    # Orders
    order_rows, order_id = [], 1
    ch_conv = {"Paid Search":0.020,"Social":0.012,"Email":0.035,"Affiliate":0.018,"Direct":0.030}

    for dt in dates:
        m_mult = month_mult[dt.month]; w_mult = weekday_mult[dt.weekday()]
        for reg in regions.keys():
            base_orders = base_daily_orders[reg] * m_mult * w_mult
            mk = marketing[(marketing["date"]==dt.date()) & (marketing["region"]==reg)]
            expected_from_mkt = sum(mk["sessions"] * mk["channel"].map(ch_conv))
            expected_orders = max(10, rng.normal(base_orders + expected_from_mkt*0.5, (base_orders+50)*0.2))
            n_orders = int(max(5, rng.poisson(lam=max(5, expected_orders))))

            reg_customers = customers[customers["region"]==reg]["customer_id"].values
            cust_choices = rng.choice(reg_customers, size=n_orders, replace=True)
            reg_countries = regions[reg]
            country_choices = rng.choice(reg_countries, size=n_orders, replace=True)
            channel_choices = rng.choice(channels, size=n_orders, replace=True, p=[0.3,0.25,0.15,0.15,0.15])

            items = rng.integers(1, 6, size=n_orders)
            price_per_item = np.exp(rng.normal(3.2, 0.45, size=n_orders))
            revenue = np.round(items * price_per_item, 2)
            cogs = np.round(revenue * rng.uniform(0.5, 0.7, size=n_orders), 2)

            ship_offset = rng.integers(0, 4, size=n_orders)
            ship_dates = pd.to_datetime(dt) + pd.to_timedelta(ship_offset, unit="D")

            mu, sigma = region_lead_mu[reg], region_lead_sigma[reg]
            lead = np.maximum(1, rng.normal(mu, sigma, size=n_orders)).astype(int)
            delivery_dates = ship_dates + pd.to_timedelta(lead, unit="D")
            promised = ship_dates + pd.to_timedelta(region_sla[reg], unit="D")
            on_time = (delivery_dates <= promised)

            base_ret = 0.06 + (lead - mu) * 0.01
            ch_penalty = np.array([0.0 if ch=="Direct" else 0.01 for ch in channel_choices])
            ret_prob = np.clip(base_ret + ch_penalty, 0.01, 0.25)
            returned = rng.binomial(1, ret_prob).astype(bool)

            for i in range(n_orders):
                order_rows.append([
                    order_id, int(cust_choices[i]), pd.to_datetime(dt).date(),
                    ship_dates[i].date(), delivery_dates[i].date(), promised[i].date(),
                    reg, country_choices[i], channel_choices[i],
                    int(items[i]), float(revenue[i]), float(cogs[i]), bool(returned[i])
                ])
                order_id += 1

    orders = pd.DataFrame(order_rows, columns=[
        "order_id","customer_id","order_date","ship_date","delivery_date","promised_delivery_date",
        "region","country","channel","items","revenue","cogs","returned_flag"
    ])

    # Returns
    reason_codes = ["Damaged","Wrong Size","Not as Described","Changed Mind","Late Delivery"]
    returned_orders = orders[orders["returned_flag"]].copy()
    n_ret = len(returned_orders)
    if n_ret > 0:
        refund_ratio = rng.choice([1.0,0.8,0.6], size=n_ret, p=[0.6,0.25,0.15])
        refund = (returned_orders["revenue"].values * refund_ratio).round(2)
        reasons = rng.choice(reason_codes, size=n_ret, p=[0.2,0.35,0.2,0.15,0.1])
        return_dates = pd.to_datetime(returned_orders["delivery_date"]) + pd.to_timedelta(rng.integers(1,21,size=n_ret),'D')
        returns = pd.DataFrame({
            "return_id": range(1, n_ret+1),
            "order_id": returned_orders["order_id"].values,
            "return_date": return_dates.dt.date,
            "reason_code": reasons,
            "refund_amount": refund
        })
    else:
        returns = pd.DataFrame(columns=["return_id","order_id","return_date","reason_code","refund_amount"])

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    customers.rename(columns={"region":"customer_region","country":"customer_country"}).to_csv(out/"customers.csv", index=False)
    marketing.to_csv(out/"marketing.csv", index=False)
    orders.to_csv(out/"orders.csv", index=False)
    returns.to_csv(out/"returns.csv", index=False)
    print("Wrote:", out)

if __name__ == "__main__":
    main()
