import webapp2

from google.appengine.ext import ndb
from google.appengine.api import users

from config import jinja_environment
from datetime import datetime
from datetime import timedelta

from time import strptime, strftime, gmtime

from models import UserData, Entry

hours_minutes = lambda td: (td.seconds // 60 // 60, td.seconds // 60 % 60) 
duration = lambda td: '%d:%02d' % hours_minutes(td)
home_url = lambda uri: '/'.join(uri.split('/')[:3])

defaults = {
    'separator': '|',
    'date_repr': '%m-%d-%Y',
    'time_repr': '%H:%M',
    'new_day_time': 0,
    'time_span': 2,
    'time_zone': 0,
    'entries': [],
    'log': [],
}

class Base(webapp2.RequestHandler):

    def get_base_values(self):
        user = users.get_current_user()
        
        if user:
            url = users.create_logout_url(home_url(self.request.uri))
            url_linktext = 'Logout'
            template = None
            
            uid = user.user_id()
            data = self.get_data(uid)
            now = datetime.now() + timedelta(seconds=3600 * data.time_zone)

            values = {'url': url, 
                      'url_linktext': url_linktext,
                      'user': user,
                      'uid': uid,
                      'data': data,
                      'now': now}
            
            step = int(self.request.get('step', u'0'))
            if step:
                values['step'] = step
        else:
            url = users.create_login_url()
            url_linktext = 'Login'
            values = {'url': url, 
                      'url_linktext': url_linktext }
            template = jinja_environment.get_template('index.html')
            
        return template, values, user

    def get_data(self, uid):
        data = UserData.get_by_id(uid)
        if data:
            changed = 0
            
            if not data.separator:
                data.separator = defaults['separator']
                changed += 1
            if not data.date_repr:
                data.date_repr = defaults['date_repr']
                changed += 1
            if not data.time_repr:
                data.time_repr = defaults['time_repr']
                changed += 1
            if not data.new_day_time:
                data.new_day_time = defaults['new_day_time']
                changed += 1
            if type(data.new_day_time) == tuple:
                data.new_day_time = defaults['new_day_time']
            if not data.time_span:
                data.time_span = defaults['time_span'] 
                changed += 1
            if not data.time_zone:
                data.time_zone = defaults['time_zone'] 
                changed += 1
            if not data.log:
                data.log = defaults['log'] 
                changed += 1
            
            if changed:
                data.put()
        else:
            data = UserData(
                id=uid,
                separator = defaults['separator'],
                date_repr = defaults['date_repr'],
                time_repr = defaults['time_repr'],
                new_day_time = defaults['new_day_time'],
                time_span = defaults['time_span'],
                time_zone = defaults['time_zone'],
                log = defaults['log']) 
            data.put()
        return data

    def massage(self, log):
        activities = []
        entries = []
        for i, d in enumerate(log):
            meta = {'i': i}
            if not d['start']:
                if d['activity'] not in activities: 
                    activities.append(d['activity'])
                if not d['break']:
                    try:
                        td = d['datetime'] - log[i+1]['datetime']
                        meta['hours'], meta['minutes'] = hours_minutes(td) 
                        meta['duration'] = duration(td)
                    except IndexError:
                        pass
            entries.append({'meta': meta, 
                            'data': d})
        activities.sort()
    
        return entries, activities


class Timelog(Base):
    
    def get_base_timelog_values(self):
        
        template, values, user = self.get_base_values()
        if template:
            return template, values, user
        
        template = jinja_environment.get_template('timelog.html')
        
        data = values.get('data', None) 
        now = values.get('now', None) 
        step = values.get('step', 0)
        experienced = len(data.log)

        entries, activities = self.massage(data.log)
        try:
            most_recent = entries[0]['data']
            last_date = most_recent['datetime'].strftime(data.date_repr)
            now_date = now.strftime(data.date_repr)
            login = last_date != now_date
        except IndexError:
            login = True

        if not experienced and login and not step:
            self.redirect('/settings?step=1')
            return template, values, user

        if step == 2 or step == 2 or login:
            start_entry = {'activity': ['start'],                
                           'datetime': now,
                           'start': True,
                           'break': False }
            if login:
                data.log.insert(0, start_entry)
                data.put()
#                if step != 2:
#                    self.redirect('/')

        days = []
        for i in range((31 * data.time_span) + 1, -1, -1):
            _min = now + timedelta(days=(-31 * data.time_span))
            _cur = _min + timedelta(i)
            wrong_month = int(_min.strftime('%m'))
            if int(_cur.strftime('%m')) != wrong_month:
                days.append(_cur)
        
        values.update({
            'data': data,
            'entries': entries,
            'days': days,
            'now': now,
            'time': now.strftime(data.time_repr),
            'time_repr': data.time_repr,
            'date': now.strftime(data.date_repr),
            'date_repr': data.date_repr,
            'weekday': now.strftime('%a').lower(),
            'duration': duration(now - data.log[0]['datetime']
                                 ) if data.log else '',
            'activities': activities,
            'separator': data.separator,
        })
    
        return template, values, user

    def update_values(self, values):
        data, changed, errors = values['data'], [], {}
        
#        dd = self.request.get('date')
#        hh = self.request.get('hour')
#        mm = self.request.get('min')
#        if dd and hh and mm:
#            import pdb; pdb.set_trace()

        activity = self.request.get('new') 
        existing = self.request.get('existing')
        if activity or existing:
            activity = [i.strip() for i in 
                        (activity or existing).split(data.separator)]
            
            if activity not in [['start'], [u'start']]:
                data.log.insert(0, {
                    'activity': activity,                
                    'datetime': values['now'],
                    'start': False,
                    'break': True if self.request.get('break') else False })
                data.put()
        entries, activities = self.massage(data.log)
        
        values.update({
            'data': data,
            'entries': entries,
            'activities': activities,
        })

    def get(self):

        massage_demodata(demodata)
        template, values, user = self.get_base_timelog_values()

        self.response.out.write(template.render(values))
        
    def post(self):

        massage_demodata(demodata)
        template, values, user = self.get_base_timelog_values()
        self.update_values(values)
        
        step = values.get('step', 0) 
        if step == 3:
            self.redirect('/report?step=3')
        if step == 6:
            self.redirect('/report?step=6')
        
        self.response.out.write(template.render(values))


class Report(Base):

    def get(self):
        massage_demodata(demodata)
        
        template, values, user = self.get_base_values()
        if user:
            uid = user.user_id()
            now = datetime.now()
            data = self.get_data(uid)
            entries, activity = self.massage(demodata)
            _entries, report = self.strip(entries)
            template = jinja_environment.get_template('report.html')
            headers = [
                "activity", "mon","tue","wed","thu","fri","sat","sun","total"]
            values.update({
                'data': _entries,
                'time': now.strftime(data.time_repr),
                'weekday': now.strftime('%a').lower(),
                'duration': duration(now - entries[0]['data']['datetime']),
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
        if days:
            hours, minutes = time.split(':')
            hours = str(int(hours) + days * 24)
            return ':'.join((hours, minutes))
        return time

    def strip(self, data):
        start = data[34]['data']['datetime']
        end = data[5]['data']['datetime']
        report = {
            'total': {
                'mon': '0:00', 'tue': '0:00', 'wed': '0:00', 'thu': '0:00',
                'fri': '0:00', 'sat': '0:00', 'sun': '0:00', 'total': '0:00'}}
        entries = []
        for i, entry in enumerate(data):
            if (start < entry['data']['datetime'] < end 
                and not entry['data']['start'] and not entry['data']['break']):

                activity = ' | '.join(entry['data']['activity'])
                weekday = entry['data']['datetime'].strftime('%a').lower()
                duration = entry['meta']['duration']

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

                entries.append(entry)
                    
        return entries, report


class Help(Base):

    def get(self):
        massage_demodata(demodata)
        
        template, values, user = self.get_base_values()
        if user:
            template = jinja_environment.get_template('help.html')
        
        self.response.out.write(template.render(values))


class Settings(Base):
    
    def get_base_settings_values(self):
        
        template, values, user = self.get_base_values()
        if template:
            return template, values, user
        
        template = jinja_environment.get_template('settings.html')
        data = values.get('data', None) 
        now = datetime.now()
        
        values.update({
            'separator': data.separator,
            'date_repr': data.date_repr,
            'date_vars': ['%Y-%m-%d', '%m-%d-%Y', '%d-%m-%Y'],
            'time_repr': data.time_repr,
            'time_vars': ['%H:%M', '%I:%M %p'],
            'time_zone': data.time_zone,
            'times': [{'td': i, 'representation': (
                now + timedelta(seconds=3600 * i)
                ).strftime(data.date_repr + ' ' + data.time_repr)} 
                for i in range(-12, +14)
            ],
            'new_day_time': data.new_day_time,
            'new_day_times': [(i, strftime(data.time_repr, gmtime(i * 3600))) for i in range(24)],
            'time_span': data.time_span,
        })

        return template, values, user
    
    def update_values(self, values):
        data, changed, errors = values['data'], [], {}
        
        rs = self.request.get('separator')
        ds = data.separator
        if rs and rs != ds:
            data.separator = rs
            changed.append('Separator')

        rdr = self.request.get('date_repr')
        ddr = data.date_repr
        if rdr and rdr != ddr:
            data.date_repr = rdr
            changed.append('Date representation')

        rtr = self.request.get('time_repr')
        dtr = data.time_repr
        if rtr and rtr != dtr:
            data.time_repr = rtr
            changed.append('Time representation')
        
        rndt = int(self.request.get('new_day_time', -1))
        dndt = data.new_day_time
        if rndt != -1 and rndt != dndt:
            data.new_day_time = rndt 
            changed.append('New day time')

        try:
            rts = int(self.request.get('time_span', -1))
            dts = data.time_span
            if rts != -1 and rts != dts:
                data.time_span = rts
                changed.append('Time span')
        except ValueError:
            errors['time_span'] = 'This needs to be an integer.'
    
        rtz = int(self.request.get('time_zone', -1))
        dtz = data.time_zone
        if rtz != -1 and rtz != dtz:
            data.time_zone = rtz
            changed.append('Current time')
    
        if changed:
            data.put()
            
        now = datetime.now()
        
        values.update({
            'changed': changed,
            'errors' : errors,
            'now': now,
            'separator': data.separator,
            'date_repr': data.date_repr,
            'time_repr': data.time_repr,
            'times': [{'td': i, 'representation': (
                now + timedelta(seconds=3600 * i)
                ).strftime(data.date_repr + ' ' + data.time_repr)} 
                for i in range(-12, +14)
            ],
            'new_day_time': data.new_day_time,
            'new_day_times': [(i, strftime(data.time_repr, gmtime(i * 3600))) for i in range(24)],
            'time_span': data.time_span,
            'time_zone': data.time_zone,
        })
    
    def get(self):
        template, values, user = self.get_base_settings_values()
        self.response.out.write(template.render(values))

    def post(self):
        template, values, user = self.get_base_settings_values()
        self.update_values(values)
        
        step = values.get('step', 0) 
        if step:
            self.redirect('/?step=2')
        
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

demodata = [
 {'activity': ['brandbeer', 'com', 'meeting'],
  'break': False,
  'datetime': '06-26-2012 16:00',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '06-26-2012 08:00',
  'start': True},
 {'activity': ['knapmap', 'fork', 'design integration'],
  'break': False,
  'datetime': '06-25-2012 17:00',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '06-25-2012 09:00',
  'start': True},
 {'activity': ['knapmap', 'fork', 'design integration'],
  'break': False,
  'datetime': '06-22-2012 17:00',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '06-22-2012 09:00',
  'start': True},
 {'activity': ['brandbeer', 'com', 'release/check'],
  'break': False,
  'datetime': '06-21-2012 22:00',
  'start': False},
 {'activity': ['diner'],
  'break': True,
  'datetime': '06-21-2012 19:00',
  'start': False},
 {'activity': ['brandbeer', 'com', 'issue 102'],
  'break': False,
  'datetime': '06-21-2012 17:45',
  'start': False},
 {'activity': ['brandbeer', 'com', 'issue 101'],
  'break': False,
  'datetime': '06-21-2012 16:45',
  'start': False},
 {'activity': ['brandbeer', 'com', 'issue 99'],
  'break': False,
  'datetime': '06-21-2012 15:45',
  'start': False},
 {'activity': ['brandbeer', 'com', 'issue 98'],
  'break': False,
  'datetime': '06-21-2012 15:15',
  'start': False},
 {'activity': ['brandbeer', 'com', 'issue 93'],
  'break': False,
  'datetime': '06-21-2012 14:15',
  'start': False},
 {'activity': ['lunch'],
  'break': True,
  'datetime': '06-21-2012 12:45',
  'start': False},
 {'activity': ['brandbeer', 'com', 'issue 93'],
  'break': False,
  'datetime': '06-21-2012 12:30',
  'start': False},
 {'activity': ['brandbeer', 'com', 'issue 92'],
  'break': False,
  'datetime': '06-21-2012 11:30',
  'start': False},
 {'activity': ['brandbeer', 'com', 'issue 91'],
  'break': False,
  'datetime': '06-21-2012 11:00',
  'start': False},
 {'activity': ['brandbeer', 'com', 'issue 85'],
  'break': False,
  'datetime': '06-21-2012 10:00',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '06-21-2012 09:00',
  'start': True},
 {'activity': ['brandbeer', 'com', 'tube promo fix'],
  'break': False,
  'datetime': '06-20-2012 17:22',
  'start': False},
 {'activity': ['brandbeer', 'com', 'glow'],
  'break': False,
  'datetime': '06-20-2012 16:37',
  'start': False},
 {'activity': ['brandbeer', 'com', 'pubfacts'],
  'break': False,
  'datetime': '06-20-2012 14:15',
  'start': False},
 {'activity': ['brandbeer',
               'com',
               'update plone, add audiopool, add patches'],
  'break': False,
  'datetime': '06-20-2012 12:15',
  'start': False},
 {'activity': ['brandbeer', 'com', 'functionaliteit'],
  'break': False,
  'datetime': '06-20-2012 10:15',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '06-20-2012 09:14',
  'start': True},
 {'activity': ['vouvouvou', 'plone patch'],
  'break': False,
  'datetime': '06-19-2012 21:00',
  'start': False},
 {'activity': ['nufnuf', 'plone patch'],
  'break': False,
  'datetime': '06-19-2012 20:30',
  'start': False},
 {'activity': ['brandbeer', 'com', 'plone patch'],
  'break': False,
  'datetime': '06-19-2012 19:30',
  'start': False},
 {'activity': ['diner'],
  'break': True,
  'datetime': '06-19-2012 19:00',
  'start': False},
 {'activity': ['brandbeer', 'com', 'demo'],
  'break': False,
  'datetime': '06-19-2012 18:30',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '06-19-2012 09:00',
  'start': True},
 {'activity': ['brandbeer', 'com', 'demo and research'],
  'break': False,
  'datetime': '06-18-2012 17:28',
  'start': False},
 {'activity': ['knapmap', 'nl', 'script'],
  'break': False,
  'datetime': '06-18-2012 11:25',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '06-18-2012 09:43',
  'start': True},
 {'activity': ['cat', 'issue 612 en 613'],
  'break': False,
  'datetime': '06-14-2012 15:13',
  'start': False},
 {'activity': ['brandbeer', 'com', 'uitzoeken WebGL/Java Applet'],
  'break': False,
  'datetime': '06-14-2012 10:00',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '06-14-2012 09:00',
  'start': True},
 {'activity': ['knapmap', 'nl', 'login removal'],
  'break': False,
  'datetime': '06-13-2012 17:15',
  'start': False},
 {'activity': ['brandbeer', 'com', 'release, overleg'],
  'break': False,
  'datetime': '06-13-2012 13:15',
  'start': False},
 {'activity': ['lunch'],
  'break': True,
  'datetime': '06-13-2012 12:45',
  'start': False},
 {'activity': ['brandbeer', 'com', 'release, overleg'],
  'break': False,
  'datetime': '06-13-2012 12:30',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '06-13-2012 09:00',
  'start': True},
 {'activity': ['brandbeer', 'com', 'issue pubfacts'],
  'break': False,
  'datetime': '06-12-2012 23:59',
  'start': False},
 {'activity': ['diner'],
  'break': True,
  'datetime': '06-12-2012 20:15',
  'start': False},
 {'activity': ['brandbeer', 'com', 'issue pubfacts'],
  'break': False,
  'datetime': '06-12-2012 18:15',
  'start': False},
 {'activity': ['lunch'],
  'break': True,
  'datetime': '06-12-2012 12:45',
  'start': False},
 {'activity': ['brandbeer', 'com', 'issue pubfacts'],
  'break': False,
  'datetime': '06-12-2012 12:30',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '06-12-2012 09:15',
  'start': True},
 {'activity': ['brandbeer', 'com', 'issue 91'],
  'break': False,
  'datetime': '06-11-2012 16:07',
  'start': False},
 {'activity': ['knapmap', 'fork', 'meeting'],
  'break': False,
  'datetime': '06-11-2012 10:48',
  'start': False},
 {'activity': ['new-zeeland', 'sync'],
  'break': False,
  'datetime': '06-11-2012 09:40',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '06-11-2012 09:16',
  'start': True},
 {'activity': ['brandbeer', 'com', 'issue 94'],
  'break': False,
  'datetime': '06-08-2012 20:07',
  'start': False},
 {'activity': ['brandbeer', 'com', 'issue 89'],
  'break': False,
  'datetime': '06-08-2012 20:07',
  'start': False},
 {'activity': ['brandbeer', 'com', 'issue 91'],
  'break': False,
  'datetime': '06-08-2012 12:15',
  'start': False},
 {'activity': ['brandbeer', 'com', 'issue 89'],
  'break': False,
  'datetime': '06-08-2012 11:45',
  'start': False},
 {'activity': ['brandbeer', 'com', 'issue 105'],
  'break': False,
  'datetime': '06-08-2012 10:00',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '06-08-2012 09:00',
  'start': True},
 {'activity': ['cat', 'issue 624'],
  'break': False,
  'datetime': '06-07-2012 17:15',
  'start': False},
 {'activity': ['cat', 'issue 593'],
  'break': False,
  'datetime': '06-07-2012 16:45',
  'start': False},
 {'activity': ['cat', 'issue 323'],
  'break': False,
  'datetime': '06-07-2012 16:15',
  'start': False},
 {'activity': ['cat', 'issue 549'],
  'break': False,
  'datetime': '06-07-2012 15:45',
  'start': False},
 {'activity': ['cat', 'issue 613'],
  'break': False,
  'datetime': '06-07-2012 13:15',
  'start': False},
 {'activity': ['lunch'],
  'break': True,
  'datetime': '06-07-2012 12:45',
  'start': False},
 {'activity': ['cat', 'issue 613'],
  'break': False,
  'datetime': '06-07-2012 12:30',
  'start': False},
 {'activity': ['cat', 'issue 566'],
  'break': False,
  'datetime': '06-07-2012 10:30',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '06-07-2012 09:00',
  'start': True},
 {'activity': ['brandbeer', 'com', 'issue 105'],
  'break': False,
  'datetime': '06-06-2012 17:15',
  'start': False},
 {'activity': ['vouvouvou', 'patch'],
  'break': False,
  'datetime': '06-06-2012 15:15',
  'start': False},
 {'activity': ['nufnuf', 'issues'],
  'break': False,
  'datetime': '06-06-2012 13:15',
  'start': False},
 {'activity': ['lunch'],
  'break': True,
  'datetime': '06-06-2012 12:45',
  'start': False},
 {'activity': ['nufnuf', 'issues'],
  'break': False,
  'datetime': '06-06-2012 12:30',
  'start': False},
 {'activity': ['penelap', 'style fix and release'],
  'break': False,
  'datetime': '06-06-2012 10:30',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '06-06-2012 09:00',
  'start': True},
 {'activity': ['cat', 'issue 612'],
  'break': False,
  'datetime': '06-05-2012 17:45',
  'start': False},
 {'activity': ['lunch'],
  'break': True,
  'datetime': '06-05-2012 12:45',
  'start': False},
 {'activity': ['cat', 'issue 612'],
  'break': False,
  'datetime': '06-05-2012 12:30',
  'start': False},
 {'activity': ['cat', 'overleg'],
  'break': False,
  'datetime': '06-05-2012 10:00',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '06-05-2012 09:00',
  'start': True},
 {'activity': ['proleto', 'feestdag'],
  'break': False,
  'datetime': '06-04-2012 17:00',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '06-04-2012 09:00',
  'start': True},
 {'activity': ['brandbeer', 'com', 'beer selector'],
  'break': False,
  'datetime': '06-01-2012 21:00',
  'start': False},
 {'activity': ['diner'],
  'break': True,
  'datetime': '06-01-2012 19:00',
  'start': False},
 {'activity': ['brandbeer', 'com', 'beer selector'],
  'break': False,
  'datetime': '06-01-2012 17:00',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '06-01-2012 09:00',
  'start': True},
 {'activity': ['brandbeer', 'com', 'pub facts'],
  'break': False,
  'datetime': '05-31-2012 21:00',
  'start': False},
 {'activity': ['diner'],
  'break': True,
  'datetime': '05-31-2012 19:00',
  'start': False},
 {'activity': ['brandbeer', 'com', 'quality'],
  'break': False,
  'datetime': '05-31-2012 17:00',
  'start': False},
 {'activity': ['brandbeer', 'com', 'tricoid link and rotation'],
  'break': False,
  'datetime': '05-31-2012 13:00',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '05-31-2012 09:00',
  'start': True},
 {'activity': ['brandbeer', 'com', 'tricoid link and rotation'],
  'break': False,
  'datetime': '05-30-2012 17:00',
  'start': False},
 {'activity': ['brandbeer', 'com', 'background blue'],
  'break': False,
  'datetime': '05-30-2012 16:00',
  'start': False},
 {'activity': ['brandbeer', 'com', 'translation'],
  'break': False,
  'datetime': '05-30-2012 15:00',
  'start': False},
 {'activity': ['nufnuf', 'issues'],
  'break': False,
  'datetime': '05-30-2012 13:00',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '05-30-2012 09:00',
  'start': True},
 {'activity': ['penelap', 'additional styling'],
  'break': False,
  'datetime': '05-29-2012 17:00',
  'start': False},
 {'activity': ['adventure', 'issues'],
  'break': False,
  'datetime': '05-29-2012 10:00',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '05-29-2012 09:00',
  'start': True},
 {'activity': ['adventure', 'issues'],
  'break': False,
  'datetime': '05-28-2012 17:00',
  'start': False},
 {'activity': ['start'],
  'break': False,
  'datetime': '05-28-2012 09:00',
  'start': True}]