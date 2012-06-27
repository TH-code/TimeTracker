import webapp2

from google.appengine.ext import ndb
from google.appengine.api import users

from config import jinja_environment
from datetime import datetime
from datetime import timedelta
from time import strptime

from models import UserData

hours_minutes = lambda td: str(td).split(':')[:2]
duration = lambda td: ':'.join(hours_minutes(td))
home_url = lambda uri: '/'.join(uri.split('/')[:3])


class Base(webapp2.RequestHandler):

    def get_base_values(self):
        user = users.get_current_user()
        
        if user:
            url = users.create_logout_url(home_url(self.request.uri))
            url_linktext = 'Logout'
            template = None
        else:
            url = users.create_login_url()
            url_linktext = 'Login'
            template = jinja_environment.get_template('index.html')

        return template, {'url': url, 'url_linktext': url_linktext}, user
    
    def get_data(self, uid):
        data = UserData.get_by_id(uid)
        if not data:
            data = UserData(
                id=uid,
                separator=' | ',
                date_repr = '%m-%d-%Y',
                time_repr = '%H:%M',
                start_time = (6, 0),
                data = [{'activity': ['start'],
                         'datetime': datetime.now(),
                         'break': False,
                         'start': True}]) 
            data.put()
        return data

    def massage(self, data):
        activities = []
        for i, entry in enumerate(data):
            entry['i'] = i
            if entry['activities'] not in activities: 
                activities.append(entry['activities'])
            entry['weekday'] = entry['datetime'].strftime('%a').lower()
            if not entry['start'] and not entry['break']:
                try:
                    td = entry['datetime'] - data[i+1]['datetime']
                    entry['hours'], entry['minutes'] = hours_minutes(td) 
                    entry['duration'] = duration(td)
                except IndexError:
                    pass
        activities.sort()
    
        return data, activities


class Timelog(Base):

    def get(self):
        massage_demodata(demodata)
        
        template, values, user = self.get_base_values()
        if user:
            uid = user.user_id()
            now = datetime.now()
            data = self.get_data(uid)
            _data, activity = self.massage(demodata)
            template = jinja_environment.get_template('timelog.html')
            values.update({
                'data': _data,
                'time': now.strftime(data.time_repr),
                'weekday': now.strftime('%a').lower(),
                'duration': duration(now - _data[0]['datetime']),
                'activity': [data.separator.join(a) for a in activity],
                'separator': data.separator,
            })
        
        self.response.out.write(template.render(values))

    def post(self):
        pass


class Report(Base):

    def get(self):
        massage_demodata(demodata)
        
        template, values, user = self.get_base_values()
        if user:
            uid = user.user_id()
            now = datetime.now()
            data = self.get_data(uid)
            _data, activity = self.massage(demodata)
            __data, report = self.strip(_data)
            template = jinja_environment.get_template('report.html')
            headers = [
                "activity", "mon","tue","wed","thu","fri","sat","sun","total"]
            values.update({
                'data': __data,
                'time': now.strftime(data.time_repr),
                'weekday': now.strftime('%a').lower(),
                'duration': duration(now - _data[0]['datetime']),
                'activity': [data.separator.join(a) for a in activity],
                'report': report,
                'headers': [{'class': h, 
                             'title': h.capitalize()} for h in headers],
                'days': headers[1:],
                'separator': data.separator,
            })
        
        self.response.out.write(template.render(values))

    def post(self):
        pass

    def add_time(self, x, y):
        x_h, x_m = x.split(':')
        y_h, y_m = y.split(':')
        seconds = (int(x_h) + int(y_h)) * 60 * 60 + (int(x_m) + int(y_m)) * 60
        
        days = seconds // 86400
        seconds = seconds % 86400
        
        t = timedelta(seconds=seconds)
        time = t.__str__()[:-3]
#        import pdb; pdb.set_trace()
        if days:
            hours, minutes = time.split(':')
            hours = str(int(hours) + days * 24)
            return ':'.join((hours, minutes))
        return time

    def strip(self, data):
        start = data[34]['datetime']
        end = data[5]['datetime']
        report = {
            'total': {
                'mon': '0:00', 'tue': '0:00', 'wed': '0:00', 'thu': '0:00',
                'fri': '0:00', 'sat': '0:00', 'sun': '0:00', 'total': '0:00'}}
        _data = []
        for i, entry in enumerate(data):
            if (start < entry['datetime'] < end 
                and not entry['start'] and not entry['break']):

                activity = entry['activity']
                weekday = entry['weekday']
                duration = entry['duration']

                if activity not in report: 
                    report[activity] = {
                        'mon': '0:00', 'tue': '0:00', 'wed': '0:00', 
                        'thu': '0:00', 'fri': '0:00', 'sat': '0:00', 
                        'sun': '0:00', 'total': '0:00'}

                report[activity][weekday] = self.add_time(
                    report[activity][weekday], duration)
                
                report['total'][weekday] = self.add_time(
                    report['total'][weekday], duration)
                
                report[activity]['total'] = self.add_time(
                    report[activity]['total'], duration)

                report['total']['total'] = self.add_time(
                    report['total']['total'], duration)

                _data.append(entry)
                    
        return _data, report


class Help(Base):

    def get(self):
        massage_demodata(demodata)
        
        template, values, user = self.get_base_values()
        if user:
#            uid = user.user_id()
#            data = self.get_data(uid)
            template = jinja_environment.get_template('help.html')
        
        self.response.out.write(template.render(values))


class Settings(Base):

    def get(self):
        massage_demodata(demodata)

        template, values, user = self.get_base_values()
        if user:
            uid = user.user_id()
            data = self.get_data(uid)
            template = jinja_environment.get_template('settings.html')

        self.response.out.write(template.render(values))


class TimelogStatic(webapp2.RequestHandler):

    def get(self):

        template = jinja_environment.get_template('timelog-static.html')
        self.response.out.write(template.render())


class ReportStatic(webapp2.RequestHandler):

    def get(self):

        template = jinja_environment.get_template('report-static.html')
        self.response.out.write(template.render())


class HelpStatic(webapp2.RequestHandler):

    def get(self):

        template = jinja_environment.get_template('help-static.html')
        self.response.out.write(template.render())


class SettingsStatic(webapp2.RequestHandler):

    def get(self):

        template = jinja_environment.get_template('settings-static.html')
        self.response.out.write(template.render())


app = webapp2.WSGIApplication([('/', Timelog),
                               ('/report', Report),
                               ('/help', Help),
                               ('/settings', Settings),
                               ('/timelog-static', TimelogStatic),
                               ('/report-static', ReportStatic),
                               ('/help-static', HelpStatic),
                               ('/settings-static', SettingsStatic)],
                              debug=True)

def massage_demodata(demodata):
    for d in demodata:
        try:
            d['datetime'] = datetime(*strptime(d['datetime'], 
                                               '%m-%d-%Y %H:%M')[0:6])
        except TypeError:
            pass
        if d['activity'] == 'start' and d['start'] == False:
            d['start'] = True

demodata = [
 {'activities': ['bavaria', 'com', 'meeting'],
  'activity': 'bavaria :: com :: meeting',
  'date': '07-05-2011',
  'datetime': '07-05-2011 16:00',
  'break': False,
  'start': False,
  'time': '16:00'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '07-05-2011',
  'datetime': '07-05-2011 08:00',
  'break': False,
  'start': False,
  'time': '08:00'},
 {'activities': ['knmp', 'sfk', 'design integration'],
  'activity': 'knmp :: sfk :: design integration',
  'date': '07-04-2011',
  'datetime': '07-04-2011 17:00',
  'break': False,
  'start': False,
  'time': '17:00'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '07-04-2011',
  'datetime': '07-04-2011 09:00',
  'break': False,
  'start': False,
  'time': '09:00'},
 {'activities': ['knmp', 'sfk', 'design integration'],
  'activity': 'knmp :: sfk :: design integration',
  'date': '07-01-2011',
  'datetime': '07-01-2011 17:00',
  'break': False,
  'start': False,
  'time': '17:00'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '07-01-2011',
  'datetime': '07-01-2011 09:00',
  'break': False,
  'start': False,
  'time': '09:00'},
 {'activities': ['bavaria', 'com', 'release/check'],
  'activity': 'bavaria :: com :: release/check',
  'date': '06-30-2011',
  'datetime': '06-30-2011 22:00',
  'break': False,
  'start': False,
  'time': '22:00'},
 {'activities': ['diner **'],
  'activity': 'diner **',
  'date': '06-30-2011',
  'datetime': '06-30-2011 19:00',
  'break': True,
  'start': False,
  'time': '19:00'},
 {'activities': ['bavaria', 'com', 'issue 102'],
  'activity': 'bavaria :: com :: issue 102',
  'date': '06-30-2011',
  'datetime': '06-30-2011 17:45',
  'break': False,
  'start': False,
  'time': '17:45'},
 {'activities': ['bavaria', 'com', 'issue 101'],
  'activity': 'bavaria :: com :: issue 101',
  'date': '06-30-2011',
  'datetime': '06-30-2011 16:45',
  'break': False,
  'start': False,
  'time': '16:45'},
 {'activities': ['bavaria', 'com', 'issue 99'],
  'activity': 'bavaria :: com :: issue 99',
  'date': '06-30-2011',
  'datetime': '06-30-2011 15:45',
  'break': False,
  'start': False,
  'time': '15:45'},
 {'activities': ['bavaria', 'com', 'issue 98'],
  'activity': 'bavaria :: com :: issue 98',
  'date': '06-30-2011',
  'datetime': '06-30-2011 15:15',
  'break': False,
  'start': False,
  'time': '15:15'},
 {'activities': ['bavaria', 'com', 'issue 93'],
  'activity': 'bavaria :: com :: issue 93',
  'date': '06-30-2011',
  'datetime': '06-30-2011 14:15',
  'break': False,
  'start': False,
  'time': '14:15'},
 {'activities': ['lunch **'],
  'activity': 'lunch **',
  'date': '06-30-2011',
  'datetime': '06-30-2011 12:45',
  'break': True,
  'start': False,
  'time': '12:45'},
 {'activities': ['bavaria', 'com', 'issue 93'],
  'activity': 'bavaria :: com :: issue 93',
  'date': '06-30-2011',
  'datetime': '06-30-2011 12:30',
  'break': False,
  'start': False,
  'time': '12:30'},
 {'activities': ['bavaria', 'com', 'issue 92'],
  'activity': 'bavaria :: com :: issue 92',
  'date': '06-30-2011',
  'datetime': '06-30-2011 11:30',
  'break': False,
  'start': False,
  'time': '11:30'},
 {'activities': ['bavaria', 'com', 'issue 91'],
  'activity': 'bavaria :: com :: issue 91',
  'date': '06-30-2011',
  'datetime': '06-30-2011 11:00',
  'break': False,
  'start': False,
  'time': '11:00'},
 {'activities': ['bavaria', 'com', 'issue 85'],
  'activity': 'bavaria :: com :: issue 85',
  'date': '06-30-2011',
  'datetime': '06-30-2011 10:00',
  'break': False,
  'start': False,
  'time': '10:00'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '06-30-2011',
  'datetime': '06-30-2011 09:00',
  'break': False,
  'start': False,
  'time': '09:00'},
 {'activities': ['bavaria', 'com', 'tube promo fix'],
  'activity': 'bavaria :: com :: tube promo fix',
  'date': '06-29-2011',
  'datetime': '06-29-2011 17:22',
  'break': False,
  'start': False,
  'time': '17:22'},
 {'activities': ['bavaria', 'com', 'glow'],
  'activity': 'bavaria :: com :: glow',
  'date': '06-29-2011',
  'datetime': '06-29-2011 16:37',
  'break': False,
  'start': False,
  'time': '16:37'},
 {'activities': ['bavaria', 'com', 'pubfacts'],
  'activity': 'bavaria :: com :: pubfacts',
  'date': '06-29-2011',
  'datetime': '06-29-2011 14:15',
  'break': False,
  'start': False,
  'time': '14:15'},
 {'activities': ['bavaria',
                 'com',
                 'update plone, add audiopool, add patches'],
  'activity': 'bavaria :: com :: update plone, add audiopool, add patches',
  'date': '06-29-2011',
  'datetime': '06-29-2011 12:15',
  'break': False,
  'start': False,
  'time': '12:15'},
 {'activities': ['bavaria', 'com', 'functionaliteit'],
  'activity': 'bavaria :: com :: functionaliteit',
  'date': '06-29-2011',
  'datetime': '06-29-2011 10:15',
  'break': False,
  'start': False,
  'time': '10:15'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '06-29-2011',
  'datetime': '06-29-2011 09:14',
  'break': False,
  'start': False,
  'time': '09:14'},
 {'activities': ['vvv', 'plone patch'],
  'activity': 'vvv :: plone patch',
  'date': '06-28-2011',
  'datetime': '06-28-2011 21:00',
  'break': False,
  'start': False,
  'time': '21:00'},
 {'activities': ['nuffic', 'plone patch'],
  'activity': 'nuffic :: plone patch',
  'date': '06-28-2011',
  'datetime': '06-28-2011 20:30',
  'break': False,
  'start': False,
  'time': '20:30'},
 {'activities': ['bavaria', 'com', 'plone patch'],
  'activity': 'bavaria :: com :: plone patch',
  'date': '06-28-2011',
  'datetime': '06-28-2011 19:30',
  'break': False,
  'start': False,
  'time': '19:30'},
 {'activities': ['diner **'],
  'activity': 'diner **',
  'date': '06-28-2011',
  'datetime': '06-28-2011 19:00',
  'break': True,
  'start': False,
  'time': '19:00'},
 {'activities': ['bavaria', 'com', 'demo'],
  'activity': 'bavaria :: com :: demo',
  'date': '06-28-2011',
  'datetime': '06-28-2011 18:30',
  'break': False,
  'start': False,
  'time': '18:30'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '06-28-2011',
  'datetime': '06-28-2011 09:00',
  'break': False,
  'start': False,
  'time': '09:00'},
 {'activities': ['bavaria', 'com', 'demo and research'],
  'activity': 'bavaria :: com :: demo and research',
  'date': '06-27-2011',
  'datetime': '06-27-2011 17:28',
  'break': False,
  'start': False,
  'time': '17:28'},
 {'activities': ['knmp', 'nl', 'script'],
  'activity': 'knmp :: nl :: script',
  'date': '06-27-2011',
  'datetime': '06-27-2011 11:25',
  'break': False,
  'start': False,
  'time': '11:25'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '06-27-2011',
  'datetime': '06-27-2011 09:43',
  'break': False,
  'start': False,
  'time': '09:43'},
 {'activities': ['at', 'issue 612 en 613'],
  'activity': 'at :: issue 612 en 613',
  'date': '06-23-2011',
  'datetime': '06-23-2011 15:13',
  'break': False,
  'start': False,
  'time': '15:13'},
 {'activities': ['bavaria', 'com', 'uitzoeken WebGL/Java Applet'],
  'activity': 'bavaria :: com :: uitzoeken WebGL/Java Applet',
  'date': '06-23-2011',
  'datetime': '06-23-2011 10:00',
  'break': False,
  'start': False,
  'time': '10:00'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '06-23-2011',
  'datetime': '06-23-2011 09:00',
  'break': False,
  'start': False,
  'time': '09:00'},
 {'activities': ['knmp', 'nl', 'login removal'],
  'activity': 'knmp :: nl :: login removal',
  'date': '06-22-2011',
  'datetime': '06-22-2011 17:15',
  'break': False,
  'start': False,
  'time': '17:15'},
 {'activities': ['bavaria', 'com', 'release, overleg'],
  'activity': 'bavaria :: com :: release, overleg',
  'date': '06-22-2011',
  'datetime': '06-22-2011 13:15',
  'break': False,
  'start': False,
  'time': '13:15'},
 {'activities': ['lunch **'],
  'activity': 'lunch **',
  'date': '06-22-2011',
  'datetime': '06-22-2011 12:45',
  'break': True,
  'start': False,
  'time': '12:45'},
 {'activities': ['bavaria', 'com', 'release, overleg'],
  'activity': 'bavaria :: com :: release, overleg',
  'date': '06-22-2011',
  'datetime': '06-22-2011 12:30',
  'break': False,
  'start': False,
  'time': '12:30'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '06-22-2011',
  'datetime': '06-22-2011 09:00',
  'break': False,
  'start': False,
  'time': '09:00'},
 {'activities': ['bavaria', 'com', 'issue pubfacts'],
  'activity': 'bavaria :: com :: issue pubfacts',
  'date': '06-21-2011',
  'datetime': '06-21-2011 23:59',
  'break': False,
  'start': False,
  'time': '23:59'},
 {'activities': ['diner **'],
  'activity': 'diner **',
  'date': '06-21-2011',
  'datetime': '06-21-2011 20:15',
  'break': True,
  'start': False,
  'time': '20:15'},
 {'activities': ['bavaria', 'com', 'issue pubfacts'],
  'activity': 'bavaria :: com :: issue pubfacts',
  'date': '06-21-2011',
  'datetime': '06-21-2011 18:15',
  'break': False,
  'start': False,
  'time': '18:15'},
 {'activities': ['lunch **'],
  'activity': 'lunch **',
  'date': '06-21-2011',
  'datetime': '06-21-2011 12:45',
  'break': True,
  'start': False,
  'time': '12:45'},
 {'activities': ['bavaria', 'com', 'issue pubfacts'],
  'activity': 'bavaria :: com :: issue pubfacts',
  'date': '06-21-2011',
  'datetime': '06-21-2011 12:30',
  'break': False,
  'start': False,
  'time': '12:30'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '06-21-2011',
  'datetime': '06-21-2011 09:15',
  'break': False,
  'start': False,
  'time': '09:15'},
 {'activities': ['bavaria', 'com', 'issue 91'],
  'activity': 'bavaria :: com :: issue 91',
  'date': '06-20-2011',
  'datetime': '06-20-2011 16:07',
  'break': False,
  'start': False,
  'time': '16:07'},
 {'activities': ['knmp', 'sfk', 'meeting'],
  'activity': 'knmp :: sfk :: meeting',
  'date': '06-20-2011',
  'datetime': '06-20-2011 10:48',
  'break': False,
  'start': False,
  'time': '10:48'},
 {'activities': ['zeelandia', 'sync'],
  'activity': 'zeelandia :: sync',
  'date': '06-20-2011',
  'datetime': '06-20-2011 09:40',
  'break': False,
  'start': False,
  'time': '09:40'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '06-20-2011',
  'datetime': '06-20-2011 09:16',
  'break': False,
  'start': False,
  'time': '09:16'},
 {'activities': ['bavaria', 'com', 'issue 94'],
  'activity': 'bavaria :: com :: issue 94',
  'date': '06-17-2011',
  'datetime': '06-17-2011 20:07',
  'break': False,
  'start': False,
  'time': '20:07'},
 {'activities': ['bavaria', 'com', 'issue 89'],
  'activity': 'bavaria :: com :: issue 89',
  'date': '06-17-2011',
  'datetime': '06-17-2011 20:07',
  'break': False,
  'start': False,
  'time': '20:07'},
 {'activities': ['bavaria', 'com', 'issue 91'],
  'activity': 'bavaria :: com :: issue 91',
  'date': '06-17-2011',
  'datetime': '06-17-2011 12:15',
  'break': False,
  'start': False,
  'time': '12:15'},
 {'activities': ['bavaria', 'com', 'issue 89'],
  'activity': 'bavaria :: com :: issue 89',
  'date': '06-17-2011',
  'datetime': '06-17-2011 11:45',
  'break': False,
  'start': False,
  'time': '11:45'},
 {'activities': ['bavaria', 'com', 'issue 105'],
  'activity': 'bavaria :: com :: issue 105',
  'date': '06-17-2011',
  'datetime': '06-17-2011 10:00',
  'break': False,
  'start': False,
  'time': '10:00'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '06-17-2011',
  'datetime': '06-17-2011 09:00',
  'break': False,
  'start': False,
  'time': '09:00'},
 {'activities': ['at', 'issue 624'],
  'activity': 'at :: issue 624',
  'date': '06-16-2011',
  'datetime': '06-16-2011 17:15',
  'break': False,
  'start': False,
  'time': '17:15'},
 {'activities': ['at', 'issue 593'],
  'activity': 'at :: issue 593',
  'date': '06-16-2011',
  'datetime': '06-16-2011 16:45',
  'break': False,
  'start': False,
  'time': '16:45'},
 {'activities': ['at', 'issue 323'],
  'activity': 'at :: issue 323',
  'date': '06-16-2011',
  'datetime': '06-16-2011 16:15',
  'break': False,
  'start': False,
  'time': '16:15'},
 {'activities': ['at', 'issue 549'],
  'activity': 'at :: issue 549',
  'date': '06-16-2011',
  'datetime': '06-16-2011 15:45',
  'break': False,
  'start': False,
  'time': '15:45'},
 {'activities': ['at', 'issue 613'],
  'activity': 'at :: issue 613',
  'date': '06-16-2011',
  'datetime': '06-16-2011 13:15',
  'break': False,
  'start': False,
  'time': '13:15'},
 {'activities': ['lunch **'],
  'activity': 'lunch **',
  'date': '06-16-2011',
  'datetime': '06-16-2011 12:45',
  'break': True,
  'start': False,
  'time': '12:45'},
 {'activities': ['at', 'issue 613'],
  'activity': 'at :: issue 613',
  'date': '06-16-2011',
  'datetime': '06-16-2011 12:30',
  'break': False,
  'start': False,
  'time': '12:30'},
 {'activities': ['at', 'issue 566'],
  'activity': 'at :: issue 566',
  'date': '06-16-2011',
  'datetime': '06-16-2011 10:30',
  'break': False,
  'start': False,
  'time': '10:30'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '06-16-2011',
  'datetime': '06-16-2011 09:00',
  'break': False,
  'start': False,
  'time': '09:00'},
 {'activities': ['bavaria', 'com', 'issue 105'],
  'activity': 'bavaria :: com :: issue 105',
  'date': '06-15-2011',
  'datetime': '06-15-2011 17:15',
  'break': False,
  'start': False,
  'time': '17:15'},
 {'activities': ['vvv', 'patch'],
  'activity': 'vvv :: patch',
  'date': '06-15-2011',
  'datetime': '06-15-2011 15:15',
  'break': False,
  'start': False,
  'time': '15:15'},
 {'activities': ['nuffic', 'issues'],
  'activity': 'nuffic :: issues',
  'date': '06-15-2011',
  'datetime': '06-15-2011 13:15',
  'break': False,
  'start': False,
  'time': '13:15'},
 {'activities': ['lunch **'],
  'activity': 'lunch **',
  'date': '06-15-2011',
  'datetime': '06-15-2011 12:45',
  'break': True,
  'start': False,
  'time': '12:45'},
 {'activities': ['nuffic', 'issues'],
  'activity': 'nuffic :: issues',
  'date': '06-15-2011',
  'datetime': '06-15-2011 12:30',
  'break': False,
  'start': False,
  'time': '12:30'},
 {'activities': ['fenelab', 'style fix and release'],
  'activity': 'fenelab :: style fix and release',
  'date': '06-15-2011',
  'datetime': '06-15-2011 10:30',
  'break': False,
  'start': False,
  'time': '10:30'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '06-15-2011',
  'datetime': '06-15-2011 09:00',
  'break': False,
  'start': False,
  'time': '09:00'},
 {'activities': ['at', 'issue 612'],
  'activity': 'at :: issue 612',
  'date': '06-14-2011',
  'datetime': '06-14-2011 17:45',
  'break': False,
  'start': False,
  'time': '17:45'},
 {'activities': ['lunch **'],
  'activity': 'lunch **',
  'date': '06-14-2011',
  'datetime': '06-14-2011 12:45',
  'break': True,
  'start': False,
  'time': '12:45'},
 {'activities': ['at', 'issue 612'],
  'activity': 'at :: issue 612',
  'date': '06-14-2011',
  'datetime': '06-14-2011 12:30',
  'break': False,
  'start': False,
  'time': '12:30'},
 {'activities': ['at', 'overleg'],
  'activity': 'at :: overleg',
  'date': '06-14-2011',
  'datetime': '06-14-2011 10:00',
  'break': False,
  'start': False,
  'time': '10:00'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '06-14-2011',
  'datetime': '06-14-2011 09:00',
  'break': False,
  'start': False,
  'time': '09:00'},
 {'activities': ['pareto', 'feestdag'],
  'activity': 'pareto :: feestdag',
  'date': '06-13-2011',
  'datetime': '06-13-2011 17:00',
  'break': False,
  'start': False,
  'time': '17:00'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '06-13-2011',
  'datetime': '06-13-2011 09:00',
  'break': False,
  'start': False,
  'time': '09:00'},
 {'activities': ['bavaria', 'com', 'beer selector'],
  'activity': 'bavaria :: com :: beer selector',
  'date': '06-10-2011',
  'datetime': '06-10-2011 21:00',
  'break': False,
  'start': False,
  'time': '21:00'},
 {'activities': ['diner **'],
  'activity': 'diner **',
  'date': '06-10-2011',
  'datetime': '06-10-2011 19:00',
  'break': True,
  'start': False,
  'time': '19:00'},
 {'activities': ['bavaria', 'com', 'beer selector'],
  'activity': 'bavaria :: com :: beer selector',
  'date': '06-10-2011',
  'datetime': '06-10-2011 17:00',
  'break': False,
  'start': False,
  'time': '17:00'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '06-10-2011',
  'datetime': '06-10-2011 09:00',
  'break': False,
  'start': False,
  'time': '09:00'},
 {'activities': ['bavaria', 'com', 'pub facts'],
  'activity': 'bavaria :: com :: pub facts',
  'date': '06-09-2011',
  'datetime': '06-09-2011 21:00',
  'break': False,
  'start': False,
  'time': '21:00'},
 {'activities': ['diner **'],
  'activity': 'diner **',
  'date': '06-09-2011',
  'datetime': '06-09-2011 19:00',
  'break': True,
  'start': False,
  'time': '19:00'},
 {'activities': ['bavaria', 'com', 'quality'],
  'activity': 'bavaria :: com :: quality',
  'date': '06-09-2011',
  'datetime': '06-09-2011 17:00',
  'break': False,
  'start': False,
  'time': '17:00'},
 {'activities': ['bavaria', 'com', 'tricoid link and rotation'],
  'activity': 'bavaria :: com :: tricoid link and rotation',
  'date': '06-09-2011',
  'datetime': '06-09-2011 13:00',
  'break': False,
  'start': False,
  'time': '13:00'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '06-09-2011',
  'datetime': '06-09-2011 09:00',
  'break': False,
  'start': False,
  'time': '09:00'},
 {'activities': ['bavaria', 'com', 'tricoid link and rotation'],
  'activity': 'bavaria :: com :: tricoid link and rotation',
  'date': '06-08-2011',
  'datetime': '06-08-2011 17:00',
  'break': False,
  'start': False,
  'time': '17:00'},
 {'activities': ['bavaria', 'com', 'background blue'],
  'activity': 'bavaria :: com :: background blue',
  'date': '06-08-2011',
  'datetime': '06-08-2011 16:00',
  'break': False,
  'start': False,
  'time': '16:00'},
 {'activities': ['bavaria', 'com', 'translation'],
  'activity': 'bavaria :: com :: translation',
  'date': '06-08-2011',
  'datetime': '06-08-2011 15:00',
  'break': False,
  'start': False,
  'time': '15:00'},
 {'activities': ['nuffic', 'issues'],
  'activity': 'nuffic :: issues',
  'date': '06-08-2011',
  'datetime': '06-08-2011 13:00',
  'break': False,
  'start': False,
  'time': '13:00'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '06-08-2011',
  'datetime': '06-08-2011 09:00',
  'break': False,
  'start': False,
  'time': '09:00'},
 {'activities': ['fenelab', 'additional styling'],
  'activity': 'fenelab :: additional styling',
  'date': '06-07-2011',
  'datetime': '06-07-2011 17:00',
  'break': False,
  'start': False,
  'time': '17:00'},
 {'activities': ['floravontuur', 'issues'],
  'activity': 'floravontuur :: issues',
  'date': '06-07-2011',
  'datetime': '06-07-2011 10:00',
  'break': False,
  'start': False,
  'time': '10:00'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '06-07-2011',
  'datetime': '06-07-2011 09:00',
  'break': False,
  'start': False,
  'time': '09:00'},
 {'activities': ['floravontuur', 'issues'],
  'activity': 'floravontuur :: issues',
  'date': '06-06-2011',
  'datetime': '06-06-2011 17:00',
  'break': False,
  'start': False,
  'time': '17:00'},
 {'activities': ['start'],
  'activity': 'start',
  'date': '06-06-2011',
  'datetime': '06-06-2011 09:00',
  'break': False,
  'start': False,
  'time': '09:00'}]