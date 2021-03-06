from os.path import expandvars
import six
from six.moves import configparser as CP
from sqlalchemy.engine.url import URL
import re

def parse(cell, config):
    """Separate input into (connection info, SQL statement)"""

    parts = [part.strip() for part in cell.split(None, 1)]
    if not parts:
        return {'connection': '', 'sql': '', 'flags': {}}
    parts[0] = expandvars(parts[0])  # for environment variables
    if parts[0].startswith('[') and parts[0].endswith(']'):
        section = parts[0].lstrip('[').rstrip(']')
        parser = CP.ConfigParser()
        parser.read(config.dsn_filename)
        cfg_dict = dict(parser.items(section))

        connection = str(URL(**cfg_dict))
        sql = parts[1] if len(parts) > 1 else ''
    elif '@' in parts[0] or '://' in parts[0]:
        connection = parts[0]
        if len(parts) > 1:
            sql = parts[1]
        else:
            sql = ''
    else:
        connection = ''
        sql = cell
    flags, sql = parse_sql_flags(sql.strip())
    return {'connection': connection.strip(),
            'sql': sql,
            'flags': flags}


def parse_sql_flags(sql):
    words = sql.split()
    flags = {
        'persist': False,
        'result_var': None
    }
    if not words:
        return (flags, "")
    num_words = len(words)
    trimmed_sql = sql
    if words[0].lower() == 'persist':
        flags['persist'] = True
        trimmed_sql =  " ".join(words[1:])
    elif num_words >= 2 and words[1] == '<<':
        flags['result_var'] = words[0]
        alpha_numeric_regex = "^[a-zA-Z]+[a-zA-Z0-9_]*$"
        if not re.match(alpha_numeric_regex, flags['result_var']):
             raise ValueError('Invalid variable name %s. Variable name must start with alphabet followed by letters, underscores or digits.' % flags['result_var'])
        query_start_point = sql.find('<<') + 2
        #trimmed_sql = " ".join(words[2:])
        # Joining by space destroys comments out everything after first single line comment. Preserving original spacing now.
        trimmed_sql = sql[query_start_point:].strip()
    return (flags, trimmed_sql.strip())
