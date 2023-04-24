from datetime import datetime

def get_date_iso (date:datetime) -> str:
    """ get string of date in iso format

    Args:
        date (datetime): date to convert

    Returns:
        str: date in iso format
    """
    date_iso = date.isoformat()
    return date_iso

def get_today () -> datetime:
    """ Get today date with hour, minute, second and microsecond set to 0

    Returns:
        datetime: datetime instance
    """
    
    today = datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    return today

def get_today_iso () -> str:
    """ get string of current date in iso format

    Returns:
        str: datetimem converted to iso format
    """
    today = get_today ()
    today_iso = get_date_iso (today)
    return today_iso

def get_date_from_iso (date_iso:str):
    """ Convert iso date to datetime object

    Args:
        date_iso (str): date in iso format
    """
    
    date = datetime.fromisoformat(date_iso)
    return date
