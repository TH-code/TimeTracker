from google.appengine.ext import ndb

class UserData(ndb.Model):
    separator = ndb.StringProperty()
    date_repr = ndb.StringProperty()
    time_repr = ndb.StringProperty()
    start_time = ndb.IntegerProperty(repeated=True)
    time_span = ndb.IntegerProperty(repeated=True)
    data = ndb.PickleProperty(repeated=True)
