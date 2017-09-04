from ConfigParser import ConfigParser
from sys import platform, stdout
from os import path, sep, listdir, access, X_OK, environ, pathsep
# from pkg_resources import resource_stream, resource_filename
from pysces import output_dir
from warnings import warn

_DEFAULT_CONFIG = {'Settings': {
    'maxima_path': 'C:\\Program Files?\\Maxima?\\bin\\maxima.bat'}}

_DEFAULT_CONF_NAME = 'default_config.ini'
_USER_CONF_PATH = path.join(output_dir, 'psctb_config.ini')


class ConfigReader:
    _config = None

    @classmethod
    def reload_config(cls):
        cls._config = None

    @classmethod
    def get_config(cls):
        if not cls._config:
            cls._setup_config()
        return cls._config

    @classmethod
    def _setup_config(cls):
        default_conf = ConfigParser()
        default_conf._sections = _DEFAULT_CONFIG
        try:
            if not path.exists(_USER_CONF_PATH):
                ConfigWriter.write_config(_DEFAULT_CONFIG, _USER_CONF_PATH)
                user_conf = ConfigParser()
                user_conf._sections = _DEFAULT_CONFIG
            else:
                user_conf = cls._read_config(_USER_CONF_PATH)
                ConfigChecker.check_config('user configuration',
                                           _USER_CONF_PATH,
                                           user_conf._sections)
        except MissingSection as e:
            solution = ('falling back to default configuration.'
                        '\nDelete configuration file to restore defaults')
            ConfigChecker.warn_user(e, solution)
            user_conf = ConfigParser()
            user_conf.add_section('Settings')
        except MissingSetting as e:
            solution = ('falling back to default configuration.'
                        '\nSpecify setting to avoid using defaults')
            ConfigChecker.warn_user(e, solution)

        cls._config = cls._compose_config(default_conf, user_conf)

        try:
            if platform == 'win32':
                maxima_path_list = PathFinder.find_path_to(
                    cls._config['maxima_path'])
                if not len(maxima_path_list) > 0:
                    raise IOError(2,
                                  'No valid path to specified file',
                                  cls._config['maxima_path'])

                maxima_path = sorted(maxima_path_list)[-1]
                cls._config['maxima_path'] = maxima_path
            else:
                maxima_path = PathFinder.which('maxima')
                if not maxima_path:
                    raise IOError(2,
                                  'Maxima not installed',
                                  'command not found')
                cls._config['maxima_path'] = 'maxima'
        except IOError as e:
            solution = ('Please check that configuration file specifies '
                        'the correct path for Maxima and '
                        'that Maxima is installed correctly before '
                        'attempting to generate new results with SymCA '
                        '(see documentation for details).')
            ConfigChecker.warn_user(e, solution)
            cls._config['maxima_path'] = None

        cls._config['platform'] = platform
        cls._config['stdout'] = stdout

    @staticmethod
    def _read_config(file_or_path):
        conf = ConfigParser()
        if type(file_or_path) is str:
            conf.read(file_or_path)
        else:
            conf.readfp(file_or_path)
        return conf

    @staticmethod
    def _compose_config(default_conf, user_conf):
        conf_dict = {}
        conf_dict.update(default_conf._sections['Settings'])
        conf_dict.update(user_conf._sections['Settings'])
        if '__name__' in conf_dict:
            conf_dict.pop('__name__')
        return conf_dict


class ConfigChecker:
    @staticmethod
    def _has_all_sections(config_name, config_path, config_dict):
        error_string = ('The {config_name} located at\n{config_path}\n'
                        'does not contain the required section\n'
                        '"{section}".')
        for section in _DEFAULT_CONFIG.keys():
            if section not in config_dict:
                raise MissingSection(
                    error_string.format(**locals()))

    @staticmethod
    def _has_all_settings(config_name, config_path, config_dict):
        error_string = ('The {config_name} located at\n{config_path}\n'
                        'does not contain the required setting\n'
                        '"{setting}"\nunder the section\n"{section}".')
        for section in _DEFAULT_CONFIG.keys():
            for setting in _DEFAULT_CONFIG[section].keys():
                if setting not in config_dict[section]:
                    raise MissingSetting(
                        error_string.format(**locals()))

    @staticmethod
    def check_config(config_name, config_path, config_dict):
        ConfigChecker._has_all_sections(config_name, config_path, config_dict)
        ConfigChecker._has_all_settings(config_name, config_path, config_dict)

    @staticmethod
    def _get_exception_name(exception):
        class_name = str(exception.__class__)
        return class_name[:-2].split('.')[-1]

    @staticmethod
    def warn_user(exception, solution):
        warning_string = ('\n\n'
                          'The following error was encountered:\n"{message}"'
                          '\n\n{solution}')
        if type(exception) is IOError:
            exception.message = exception.strerror + ':\n' + exception.filename
        message = ConfigChecker._get_exception_name(exception) + \
            ' - ' + exception.message
        warn(warning_string.format(**locals()))


class ConfigWriter:
    @staticmethod
    def write_config(config_dict, config_path):
        conf = ConfigParser()
        for section, settings in config_dict.iteritems():
            conf.add_section(section)
            for setting, value in settings.iteritems():
                conf.set(section, setting, value)
        with open(config_path, 'w') as f:
            conf.write(f)


class MissingSetting(Exception):
    pass


class MissingSection(Exception):
    pass


class PathFinder:
    @staticmethod
    def find_path_to(wildcard_path):
        path_parts = wildcard_path.split(sep)
        if platform == 'win32':
            new_paths = [path_parts.pop(0) + sep]
        else:
            new_paths = [sep]

        for i, path_part in enumerate(path_parts):
            if '?' in path_part:
                path_part = path_part[:-1]
                new_new_paths = []
                for each_base in new_paths:
                    possible_matches = PathFinder.find_match(each_base,
                                                             path_part)
                    if len(possible_matches) > 0:
                        for match in possible_matches:
                            new_new_paths.append(path.join(each_base, match))
                new_paths = new_new_paths
            else:
                new_new_paths = []
                for each_path in new_paths:
                    new_path = path.join(each_path, path_part)
                    if path.exists(new_path):
                        new_new_paths.append(new_path)
                new_paths = new_new_paths
        return new_paths

    @staticmethod
    def find_match(base_dir, to_match):
        matches = []
        try:
            dirs_in_basedir = listdir(base_dir)
        except OSError:
            dirs_in_basedir = []
        for directory in dirs_in_basedir:
            if to_match in directory:
                matches.append(directory)
        return matches

    @staticmethod
    def which(program):
        def is_exe(fpath):
            return path.isfile(fpath) and access(fpath, X_OK)

        fpath, fname = path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for epath in environ["PATH"].split(pathsep):
                epath = epath.strip('"')
                exe_file = path.join(epath, program)
                if is_exe(exe_file):
                    return exe_file

        return None
