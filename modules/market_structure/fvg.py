def detect_fvg(df):
    """
    Fair Value Gap — свеча оставила разрыв:
    Previous high < next low (бычий FVG)
    Previous low > next high (медвежий FVG)
    """

    gaps = []

    for i in range(1, len(df)-1):
        prev_high = df['high'][i-1]
        next_low = df['low'][i+1]

        prev_low = df['low'][i-1]
        next_high = df['high'][i+1]

        # Bullish FVG
        if prev_high < next_low:
            gaps.append({
                "index": i,
                "type": "bullish",
                "low": prev_high,
                "high": next_low
            })

        # Bearish FVG
        if prev_low > next_high:
            gaps.append({
                "index": i,
                "type": "bearish",
                "low": next_high,
                "high": prev_low
            })

    return gaps

