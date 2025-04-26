import holidays
from datetime import datetime, timedelta

def __next_day(date):
    return date + timedelta(days=1)

def __is_holiday(date, code):
    if "Festa della Liberazione" == holidays.country_holidays(code).get(date):
        return date
    elif date in holidays.country_holidays(code):
        #print("date in holidays: "+str(date))
        return __is_holiday(__next_day(date), code)
    elif date.weekday() in [5, 6]:
        #print("date.weekday() in weekend_days: "+str(date))
        return __is_holiday(__next_day(date), code)
    else:
        #print("else: "+str(date))
        return date

def next_number_business_day(date, code, number, algorithm):
    if algorithm == "next_business_day":
        next_date = date
        i = 0
        while i < number:
            next_date = __next_day(next_date)
            next_date = __is_holiday(next_date, code)
            #print("next_date: "+str(next_date))

            i += 1
        return next_date
    elif algorithm == "simple":
        return date + timedelta(days=number)

def next_business_day(date, code, format):
    date = datetime.strptime(date, format)
    next_date = __next_day(date)
    next_date = __is_holiday(next_date, code)
    next_date = next_date.strftime(format)
    return next_date

#print(next_business_day('23/04/2024', 'IT', '%d/%m/%Y'))

#print(next_two_business_day('28/12/2023', 'IT', '%d/%m/%Y'))
#print(holidays.financial_holidays('IT').get('2024-04-25'))
#print(next_number_business_day('23/04/2024', 'IT', 3, '%d/%m/%Y'))