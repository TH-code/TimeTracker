from google.appengine.ext import ndb

class UserData(ndb.Model):
    separator = ndb.StringProperty()
    date_repr = ndb.StringProperty()
    time_repr = ndb.StringProperty()
    new_day_time = ndb.IntegerProperty(repeated=True)
    time_span = ndb.IntegerProperty()
    time_zone = ndb.IntegerProperty()
    log = ndb.PickleProperty(repeated=True)
