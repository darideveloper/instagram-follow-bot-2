from datetime import datetime


def get_today_iso () -> str:
    """ get string of current date in iso format

    Returns:
        str: _description_
    """
    today = datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_iso = today.isoformat()
    return today_iso

def get_date_from_iso (date_iso:str):
    """ Convert iso date to datetime object

    Args:
        date_iso (str): date in iso format
    """
    
    date = datetime.fromisoformat(date_iso)
    return date
