import holidays
from datetime import datetime, timedelta

def __next_day(date):
    """Get the next day from the given date.
    
    Args:
        date (datetime): Input date.
        
    Returns:
        datetime: Date one day after the input date.
    """
    return date + timedelta(days=1)

def __is_holiday(date, code):
    """Check if date is a holiday or weekend, and return next business day if so.
    
    Args:
        date (datetime): Date to check.
        code (str): Country code for holiday calculation (e.g., 'IT').
        
    Returns:
        datetime: Next business day if input is holiday/weekend, otherwise input date.
    """
    if "Festa della Liberazione" == holidays.country_holidays(code).get(date):
        return date
    elif date in holidays.country_holidays(code):
        return __is_holiday(__next_day(date), code)
    elif date.weekday() in [5, 6]:
        return __is_holiday(__next_day(date), code)
    else:
        return date

def next_number_business_day(date, code, number):
    """Calculate the date that is N business days from the given date.
    
    Args:
        date (datetime): Starting date.
        code (str): Country code for holiday calculation (e.g., 'IT').
        number (int): Number of business days to add (negative values return
                     date in the past without holiday checking).
        
    Returns:
        datetime: Date that is N business days from the input date.
    """
    if number >= 0:
        next_date = date
        i = 0
        while i < number:
            next_date = __next_day(next_date)
            next_date = __is_holiday(next_date, code)

            i += 1
        return next_date
    else:
        return date - timedelta(days=abs(number))

def next_business_day(date, code, format):
    """Calculate the next business day from a date string.
    
    Args:
        date (str): Date string to parse.
        code (str): Country code for holiday calculation (e.g., 'IT').
        format (str): Date format string for parsing (e.g., '%d/%m/%Y').
        
    Returns:
        str: Next business day formatted as a string in the same format.
    """
    date = datetime.strptime(date, format)
    next_date = __next_day(date)
    next_date = __is_holiday(next_date, code)
    next_date = next_date.strftime(format)
    return next_date

#print(next_business_day('23/04/2024', 'IT', '%d/%m/%Y'))

#print(next_two_business_day('28/12/2023', 'IT', '%d/%m/%Y'))
#print(holidays.financial_holidays('IT').get('2024-04-25'))
#print(next_number_business_day('23/04/2024', 'IT', 3, '%d/%m/%Y'))