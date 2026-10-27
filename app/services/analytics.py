"""Aggregate numbers shown in the UI and the Excel Summary sheet."""
from __future__ import annotations

import statistics
from typing import Any, Optional

from ..models import Offer, ReferencePackage


def _round(x: Optional[float]) -> Optional[float]:
    return None if x is None else round(x, 2)


def compute_analytics(ref: ReferencePackage, offers: list[Offer], ref_price_usd: Optional[float]) -> dict[str, Any]:
    page_offers = [o for o in offers if o.verification == "page"]
    leads = [o for o in offers if o.verification == "snippet"]
    stat_prices = sorted(o.price_usd_from for o in offers if o.in_stats and o.price_usd_from is not None)
    wide = sorted(o.price_usd_from for o in offers if o.in_wide and o.price_usd_from is not None)
    out: dict[str, Any] = {
        "wide_count": len(wide),
        "wide_min": _round(wide[0]) if wide else None,
        "wide_max": _round(wide[-1]) if wide else None,
        "wide_median": _round(statistics.median(wide)) if wide else None,
        "reference_price_usd": _round(ref_price_usd),
        "total_found": len(offers),
        "verified_pages": len(page_offers),
        "same": sum(1 for o in offers if o.match_level == "same"),
        "leads_to_check": len(leads),
        "priced": sum(1 for o in page_offers if o.price_usd_from is not None),
        "in_stats": len(stat_prices),
        "flights_included": sum(1 for o in page_offers if o.flights_included is True),
        "by_level": {lv: sum(1 for o in page_offers if o.match_level == lv) for lv in ("same", "near", "partial", "rejected")},
        "by_seller_type": {},
        "by_domain": {},
    }
    for o in page_offers:
        out["by_seller_type"][o.seller_type] = out["by_seller_type"].get(o.seller_type, 0) + 1
        out["by_domain"][o.listed_on] = out["by_domain"].get(o.listed_on, 0) + 1

    if stat_prices:
        median = statistics.median(stat_prices)
        out.update(
            min=_round(stat_prices[0]), max=_round(stat_prices[-1]), median=_round(median),
            mean=_round(statistics.fmean(stat_prices)),
            p25=_round(statistics.quantiles(stat_prices, n=4)[0]) if len(stat_prices) >= 2 else _round(stat_prices[0]),
            p75=_round(statistics.quantiles(stat_prices, n=4)[2]) if len(stat_prices) >= 2 else _round(stat_prices[0]),
        )
        if ref_price_usd:
            out["vs_median_usd"] = _round(ref_price_usd - median)
            out["vs_median_pct"] = round((ref_price_usd - median) / median * 100, 1) if median else None
            cheaper = sum(1 for p in stat_prices if p < ref_price_usd)
            out["rank"] = cheaper + 1
            out["rank_of"] = len(stat_prices) + 1
            out["position"] = (
                "below market" if ref_price_usd < out["p25"] else
                "above market" if ref_price_usd > out["p75"] else "within the market's middle range"
            )
    return out
