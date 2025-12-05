from collections import defaultdict


def bucket_trades(trades: list, bucket_seconds: int = 5):
    """
    Агрегирует сделки по временным бакетам для оценки краткосрочной динамики.

    Args:
        trades: список сделок [{price, volume, side, timestamp}, ...]
        bucket_seconds: размер окна в секундах

    Returns:
        dict:
        {
            "bucket_count": int,
            "last_bucket_delta": float,
            "last_bucket_aggr": {"buy": float, "sell": float},
            "last_bucket_velocity": float,  # trades per sec in last bucket
            "mean_velocity": float          # средняя скорость по всем buckets
        }
    """
    if not trades or not isinstance(trades, list):
        return {
            "bucket_count": 0,
            "last_bucket_delta": 0,
            "last_bucket_aggr": {"buy": 0, "sell": 0},
            "last_bucket_velocity": 0,
            "mean_velocity": 0
        }

    buckets = defaultdict(list)
    for t in trades:
        if not isinstance(t, dict):
            continue
        ts = t.get("timestamp", 0)
        if ts is None:
            continue
        # timestamp предполагается в мс
        bucket_id = int(ts // (bucket_seconds * 1000))
        buckets[bucket_id].append(t)

    if not buckets:
        return {
            "bucket_count": 0,
            "last_bucket_delta": 0,
            "last_bucket_aggr": {"buy": 0, "sell": 0},
            "last_bucket_velocity": 0,
            "mean_velocity": 0
        }

    sorted_ids = sorted(buckets.keys())
    last_id = sorted_ids[-1]

    def calc_bucket_metrics(trades_bucket):
        buy = sell = 0.0
        for t in trades_bucket:
            side = t.get("side")
            vol = float(t.get("volume", 0) or 0)
            if side == "buy":
                buy += vol
            elif side == "sell":
                sell += vol
        delta = buy - sell
        count = len(trades_bucket)
        # velocity = count per second inside bucket
        vel = count / bucket_seconds if bucket_seconds > 0 else count
        return delta, {"buy": buy, "sell": sell}, vel

    # Last bucket
    last_delta, last_aggr, last_vel = calc_bucket_metrics(buckets[last_id])

    # Mean velocity across all buckets
    velocities = []
    for bid in sorted_ids:
        _, _, vel = calc_bucket_metrics(buckets[bid])
        velocities.append(vel)
    mean_vel = sum(velocities) / len(velocities) if velocities else 0

    return {
        "bucket_count": len(sorted_ids),
        "last_bucket_delta": last_delta,
        "last_bucket_aggr": last_aggr,
        "last_bucket_velocity": last_vel,
        "mean_velocity": mean_vel
    }

