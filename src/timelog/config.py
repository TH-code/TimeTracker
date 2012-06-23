import os
import jinja2

webapp2_config = {}
webapp2_config['webapp2_extras.sessions'] = {
'secret_key': 'DitIsEenGrootGeheim',
}

templates_path = os.path.join(os.path.dirname(__file__), 'templates')
jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(templates_path))
webapp2_config['webapp2_extras.jinja2'] = {
        'environment': jinja_environment
}
