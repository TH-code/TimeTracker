from google.appengine.ext import ndb

class Entry(ndb.Model):
    activity = ndb.PickleProperty()
    datetime = ndb.DateTimeProperty()
    start = ndb.BooleanProperty()
    pause = ndb.BooleanProperty()
    
class UserData(ndb.Model):
    separator = ndb.StringProperty()
    date_repr = ndb.StringProperty()
    time_repr = ndb.StringProperty()
    new_day_time = ndb.IntegerProperty()
    time_span = ndb.IntegerProperty()
    time_zone = ndb.IntegerProperty()
    log = ndb.PickleProperty(repeated=True)
    timelog = ndb.StructuredProperty(Entry, repeated=True)
