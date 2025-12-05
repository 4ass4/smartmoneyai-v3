# modules/utils/merge_data.py

import pandas as pd


def merge_ohlcv_data(dataframes):
    """
    Объединяет несколько OHLCV DataFrame
    
    Args:
        dataframes: список DataFrame
        
    Returns:
        Объединенный DataFrame
    """
    if not dataframes:
        return pd.DataFrame()
    
    result = dataframes[0]
    for df in dataframes[1:]:
        result = pd.concat([result, df], ignore_index=True)
    
    return result.sort_values(by='timestamp').reset_index(drop=True)


def align_dataframes(df1, df2, on='timestamp'):
    """
    Выравнивает два DataFrame по общему ключу
    
    Args:
        df1: первый DataFrame
        df2: второй DataFrame
        on: ключ для выравнивания
        
    Returns:
        Кортеж выровненных DataFrame
    """
    merged = pd.merge(df1, df2, on=on, how='inner')
    return merged, merged

