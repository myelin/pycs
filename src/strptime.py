# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/56036

"""a pure-Python version of strptime.

Attempts to simulate time.strptime as closely as possible, following the
specification for time.strptime as spelled out in the official Python docs.

Locale support is handled by using LocaleAssembly().  Just follow the examples 
in this file to see how to create your own locale.  English and Swedish are 
included by default.

Thanks to Andrew Markebo (flognat@fukt.hk-r.se) for his pure Python version of
strptime, which convinced me to improve locale support.  And of course to Guido
van Rossum and everyone else who has contributed to Python, the greatest
language I have ever used.

"""
import re
###Python 2.2 -- For _StrpObj.return_time(): from time import  struct_time
from exceptions import Exception
__all__=['strptime','AS_IS','CHECK','FILL_IN','LocaleAssembly','ENGLISH','SWEDISH']

# module metadata
__author__ = 'Brett Cannon'
__email__ = 'drifty@bigfoot.com'
__version__ = '2.0'
__url__ = 'http://www.drifty.org/'

# global settings and parameter constants
CENTURY = 2000
AS_IS = 'AS_IS'
CHECK = 'CHECK'
FILL_IN = 'FILL_IN'

def LocaleAssembly(DirectiveDict, MonthDict, DayDict, am_pmTuple):
    """Creates locale tuple for use by strptime.
    Takes in DirectiveDict (locale-specific regexes for extracting info from
    time string), MonthDict (locale full and abbreviated month names), DayDict
    (locale full and abbreviated weekday names), and am_pmDict (locale's valid
    representation of AM and PM).

    DirectiveDict, MonthDict, and DayDict are dictionaries, while am_pmTuple is a
    tuple.  Look at how the ENGLISH dictionary is created for an example of how
    the passed-in values should be constructed.  Also, make sure that every
    value in your language dictionary has a corresponding version to one in the
    ENGLISH dictionary; leaving any out could cause problems.

    Also note: if there are any values in the BasicDict that you would like to
    override, just put the overrides in the DirectiveDict dictionary argument.

    """
###Python 2.2 -- Remove the %Z value since it has been deprecated.
    BasicDict={'%d':r'(?P<d>[0-3]\d)', # Day of the month [01,31].
        '%H':r'(?P<H>[0-2]\d)', # Hour (24-h) [00,23].
        '%I':r'(?P<I>[01]\d)', # Hour (12-h) [01,12].
        '%j':r'(?P<j>[0-3]\d\d)', # Day of the year [001,366].
        '%m':r'(?P<m>[01]\d)', # Month [01,12].
        '%M':r'(?P<M>[0-5]\d)', # Minute [00,59].
        '%S':r'(?P<S>[0-6]\d)', # Second [00,61].
        '%U':r'(?P<U>[0-5]\d)', # Week number of the year, Sunday first [00,53]
        '%w':r'(?P<w>[0-6])', # Weekday [0(Sunday),6].
        '%W':r'(?P<W>[0-5]\d)', # Week number of the year, Monday first [00,53]
        '%y':r'(?P<y>\d\d)', # Year without century [00,99].
        '%Y':r'(?P<Y>\d\d\d\d)', # Year with century.
        '%Z':r'(?P<Z>(\D+ Time)|([\S\D]{3,3}))', # Time zone name (or empty)
        '%%':r'(?P<percent>%)' # Literal "%" (ignored, in the end)
        }
    BasicDict.update(DirectiveDict)
    return BasicDict, MonthDict, DayDict, am_pmTuple



"""Built-in locales"""
ENGLISH_Lang=(
    {'%a':r'(?P<a>[^\s\d]{3,3})', #Abbreviated weekday name.
     '%A':r'(?P<A>[^\s\d]{6,9})', #Full weekday name.
     '%b':r'(?P<b>[^\s\d]{3,3})', #Abbreviated month name.
     '%B':r'(?P<B>[^\s\d]{3,9})', #Full month name.
     '%c':r'(?P<m>\d\d)/(?P<d>\d\d)/(?P<y>\d\d) (?P<H>\d\d):(?P<M>\d\d):(?P<S>\d\d)', #Appropriate date and time representation.
     '%p':r'(?P<p>(a|A|p|P)(m|M))', #Equivalent of either AM or PM.
     '%x':r'(?P<m>\d\d)/(?P<d>\d\d)/(?P<y>\d\d)', #Appropriate date representation.
     '%X':r'(?P<H>\d\d):(?P<M>\d\d):(?P<S>\d\d)'}, #Appropriate time representation.
    {'January':1,   'Jan':1,
     'February':2,  'Feb':2,
     'March':3,     'Mar':3,
     'April':4,     'Apr':4,
     'May':5,
     'June':6,      'Jun':6,
     'July':7,      'Jul':7,
     'August':8,    'Aug':8,
     'September':9, 'Sep':9,
     'October':10,  'Oct':10,
     'November':11, 'Nov':11,
     'December':12, 'Dec':12},
    {'Monday':0,    'Mon':0,   # Adjusted for Monday-first counting.
     'Tuesday':1,   'Tue':1,
     'Wednesday':2, 'Wed':2,
     'Thursday':3,  'Thu':3,
     'Friday':4,    'Fri':4,
     'Saturday':5,  'Sat':5,
     'Sunday':6,    'Sun':6},
    (('am','AM'),('pm','PM'))
    )
ENGLISH=LocaleAssembly(ENGLISH_Lang[0],ENGLISH_Lang[1],ENGLISH_Lang[2],ENGLISH_Lang[3])

SWEDISH_Lang=(
    {'%a':r'(?P<a>[^\s\d]{3,3})',
     '%A':r'(?P<A>[^\s\d]{6,7})',
     '%b':r'(?P<b>[^\s\d]{3,3})',
     '%B':r'(?P<B>[^\s\d]{3,8})',
     '%c':r'(?P<a>[^\s\d]{3,3}) (?P<d>[0-3]\d) (?P<b>[^\s\d]{3,3}) (?P<Y>\d\d\d\d) (?P<H>[0-2]\d):(?P<M>[0-5]\d):(?P<S>[0-6]\d)',
     '%p':r'(?P<p>(a|A|p|P)(m|M))',
     '%x':r'(?P<m>\d\d)/(?P<d>\d\d)/(?P<y>\d\d)',
     '%X':r'(?P<H>\d\d):(?P<M>\d\d):(?P<S>\d\d)'},
    {'Januari':1,   'Jan':1,
     'Februari':2,  'Feb':2,
     'Mars':3,      'Mar':3,
     'April':4,     'Apr':4,
     'Maj':5,       'Maj':5,
     'Juni':6,      'Jun':6,
     'Juli':7,      'Jul':7,
     'Augusti':8,   'Aug':8,
     'September':9, 'Sep':9,
     'Oktober':10,  'Okt':10,
     'November':11, 'Nov':11,
     'December':12, 'Dec':12},
    {'MÂndag':0,    'MÂn':0,
     'Tisdag':1,    'Tis':1,
     'Onsdag':2,    'Ons':2,
     'Torsdag':3,   'Tor':3,
     'Fredag':4,    'Fre':4,
     'Lˆrdag':5,    'Lˆr':5,
     'Sˆndag':6,    'Sˆn':6},
    (('am','AM'),('pm','PM'))
    )
SWEDISH=LocaleAssembly(SWEDISH_Lang[0],SWEDISH_Lang[1],SWEDISH_Lang[2],SWEDISH_Lang[3])



class StrptimeError(Exception):
    """Exception class for the module."""
    def __init__(self,args=None): self.args=args



class _StrpObj:  ###Python 2.2 -- Subclass object.
    """An object with basic time manipulation methods.
    As of Python 2.2, the time module functions return a pseudo-sequence
    object from time.struct_time.  Unfortunately, it cannot be subclassed.
    This is why _StrpObj does not subclass struct_time and has to explicitly
    create an instance when _StrpObj.return_time() is called.

    """
    def __init__(self, year=None, month=None, day=None, hour=None, minute=None, 
        second=None, day_week=None, julian_date=None, daylight=None):
        """Sets up instances variables.  All values can be set at initialization.
        Any into left out is automatically set to None.

        """
        self.year=year
        self.month=month
        self.day=day
        self.hour=hour
        self.minute=minute
        self.second=second
        self.day_week=day_week
        self.julian_date=julian_date
        self.daylight=daylight

    def julianFirst(self):
        """Calculates the julian date for the first day of year self.year."""
        a=(14-1)/12  # for symmetry with gregToJulian's formula
        y=(self.year+4800)-a
        m=1+12*a-3
        julian_first=1+((153*m+2)/5)+365*y+y/4-y/100+y/400-32045
        return julian_first

    def gregToJulian(self):
        """Converts the Gregorian date to the Julian date.
        Uses self.year, self.month, and self.day along with julianFirst().

	"""
        a=(14-self.month)/12
        y=self.year+4800-a
        m=self.month+12*a-3
        julian_day=self.day+((153*m+2)/5)+365*y+y/4-y/100+y/400-32045

        julian_first=self.julianFirst()

        julian_date=julian_day-julian_first
        julian_date=julian_date+1 # to make result be same as what strftime would give.
        return julian_date

    def julianToGreg(self):
        """Converts the Julian date to the Gregorian date."""
        julian_first=self.julianFirst()
        julian_day=self.julian_date+julian_first
        julian_day=julian_day-1
        a=julian_day+32044
        b=(4*a+3)/146097
        c=a-((146097*b)/4)
        d=(4*c+3)/1461
        e=c-((1461*d)/4)
        m=(5*e+2)/153
        day=e-((153*m+2)/5)+1
        month=m+3-12*(m/10)
        year=100*b+d-4800+(m/10)
        return (year,month,day)

    def dayWeek(self):
        """Figures out the day of the week using self.year, self.month, and self.day.
        Monday is 0.

        """
        a=(14-self.month)/12
        y=self.year-a
        m=self.month+12*a-2
        day_week=(self.day+y+(y/4)-(y/100)+(y/400)+((31*m)/12))%7
        if day_week==0:
            day_week=6
        else:
            day_week=day_week-1
        return day_week

    def FillInInfo(self):
        """Based on the current time information, it figures out what other info can be filled in."""
        if self.julian_date==None and self.year and self.month and self.day:
            julian_date=self.gregToJulian()
            self.julian_date=julian_date
        if (self.month==None or self.day==None) and self.year and self.julian_date:
            gregorian=self.julianToGreg()
            self.month=gregorian[1] # Year tossed out since must be already ok
            self.day=gregorian[2]
        if self.day_week==None and self.year and self.month and self.day:
            self.day_week=self.dayWeek()

    def CheckIntegrity(self):
        """Checks info integrity based on the range that a number can be.
	  Any invalid info raises StrptimeError.

	"""
        if self.month!=None:
            if not (1<=self.month<=12):
                raise StrptimeError,'Month incorrect'
        if self.day!=None:
            if not 1<=self.day<=31:
                raise StrptimeError,'Day incorrect'
        if self.hour!=None:
            if not 0<=self.hour<=23:
                raise StrptimeError,'Hour incorrect'
        if self.minute!=None:
            if not 0<=self.minute<=59:
                raise StrptimeError,'Minute incorrect'
        if self.second!=None:
            if not 0<=self.second<=61: #61 covers leap seconds.
                raise StrptimeError,'Second incorrect'
        if self.day_week!=None:
            if not 0<=self.day_week<=6:
                raise StrptimeError,'Day of the Week incorrect'
        if self.julian_date!=None:
            if not 0<=self.julian_date<=366:
                raise StrptimeError,'Julian Date incorrect'
        if self.daylight!=None:
            if not -1<=self.daylight<=1:
                raise StrptimeError,'Daylight Savings incorrect'
        return 1

    def return_time(self):
        """Returns a tuple in the format used by time.gmtime().
        All instances of None in the information are replaced with 0."""
        temp_time=[self.year, self.month, self.day, self.hour, self.minute, self.second,
                   self.day_week, self.julian_date, self.daylight]
        return tuple([t or 0 for t in temp_time])  ###Python 2.2 -- change to:
            ###struct_time(tuple(...)
            ###Make sure to uncomment importation of struct_time at the top 
            ###of the file.

    def RECreation(self, format, DIRECTIVEDict):
        """Creates re based on format string and DIRECTIVEDict."""
        Directive=0
        REString=''
        for char in format:
            if char=='%' and not Directive:
                Directive=1
            elif Directive:
                try: REString='%s%s' % (REString,DIRECTIVEDict["%%%s" % char])
                except KeyError: raise StrptimeError
                Directive=0
            else:
		REString='%s%s' % (REString,char)
	return re.compile(REString,re.IGNORECASE)

    def convert(self, string, format, locale_setting):
        """Gets time info from string based on format string and a locale created by LocaleAssembly()."""
        DIRECTIVEDict, MONTHDict, DAYDict, AM_PM = locale_setting
        REComp = self.RECreation(format, DIRECTIVEDict)
        reobj = REComp.match(string)
        if not reobj: raise StrptimeError,"Format string does not match format of the data string"
        for found in reobj.groupdict().keys():
            if found in ('y','Y'): #Year
                if found=='y': #Without century
                    self.year=CENTURY+int(reobj.group('y'))
                else: #With century
                    self.year=int(reobj.group('Y'))
            elif found in ('b','B','m'): #Month
                if found=='m':
                    self.month=int(reobj.group(found))
                else: #Int
                    try:
                        self.month=MONTHDict[reobj.group(found)]
                    except KeyError:
                        raise StrptimeError, 'Unrecognized month'
            elif found=='d': #Day of the Month
                self.day=int(reobj.group(found))
            elif found in ('H','I'): #Hour
                hour=int(reobj.group(found))
                if found=='H':
                    self.hour=hour
                else:
                    try:
                        if reobj.group('p') in AM_PM[0]:
                            AP=0
                        else:
                            AP=1
                    except (KeyError,IndexError):
                        raise StrptimeError, 'Lacking needed AM/PM information'
                    if AP:
                        if hour==12:
                            self.hour=12
                        else:
                            self.hour=12+hour
                    else:
                        if hour==12:
                            self.hour=0
                        else:
                            self.hour=hour
            elif found=='M': #Minute
                self.minute=int(reobj.group(found))
            elif found=='S': #Second
                self.second=int(reobj.group(found))
            elif found in ('a','A','w'): #Day of the week
                if found=='w':
                    day_value=int(reobj.group(found))
                    if day_value==0:
                        self.day_week=6
                    else:
                        self.day_week=day_value-1
                else:
                    try:
                        self.day_week=DAYDict[reobj.group(found)]
                    except KeyError:
                        raise StrptimeError, 'Unrecognized day'
            elif found=='j': #Julian date
                self.julian_date=int(reobj.group(found))
            elif found=='Z': #Daylight savings
                TZ=reobj.group(found)
                if len(TZ)==3:
                    if TZ[1] in ('D','d'):
                        self.daylight=1
                    else:
                        self.daylight=0
                elif TZ.find('Daylight')!=-1:
                    self.daylight=1
                else:
                    self.daylight=0

def strptime(data, format='%a %b %d %H:%M:%S %Y', option=AS_IS, locale_setting=ENGLISH):
    """Returns a tuple representing the time represented in 'data'.
    Valid values for 'options' are AS_IS, CHECK, & FILL_IN.  'locale_setting' accepts
    locale tuples created by LocaleAssembly().

    """
    Obj=_StrpObj()
    Obj.convert(data, format, locale_setting)
    if option in (FILL_IN,CHECK):
        Obj.CheckIntegrity()
    if option in (FILL_IN,):
        Obj.FillInInfo()
    return Obj.return_time()


