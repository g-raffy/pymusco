from pathlib import Path
import json

class Settings(object):

    def __init__(self, workspace_root_path=None):
        """
        Parameters:

        settings_file_path : Path
            the path to the pymusco settings file (in json format)
        """
        if workspace_root_path is None:
            workspace_root_path = Path('~/private/pymusco/samples').expanduser()
        assert isinstance(workspace_root_path, Path)
        self.workspace_root_path = workspace_root_path
        self.settings_file_path = self.workspace_root_path / "pymusco_settings.json"
        self.scans_dir = workspace_root_path / 'scans'
        self.stubs_dir = workspace_root_path / 'stubs'
        self.prints_dir = workspace_root_path / 'prints'
        self.stamp_file_path = None
        if self.settings_file_path.exists():
            self.load()
        else:
            self.save()

    def load(self):
        """
        load the settings from pymuscos's settings file
        """
        with open(self.settings_file_path, 'r') as file:
            settings_dict = json.load(file)
        assert settings_dict['format'] == 'pymusco.settings.v1'
        self.scans_dir = Path(settings_dict['scans_dir'])
        self.stubs_dir = Path(settings_dict['stubs_dir'])
        self.prints_dir = Path(settings_dict['prints_dir'])

    def save(self):
        settings_dict = {}
        settings_dict['format'] = 'pymusco.settings.v1'
        settings_dict['scans_dir'] = str(self.scans_dir)
        settings_dict['stubs_dir'] = str(self.stubs_dir)
        settings_dict['prints_dir'] = str(self.prints_dir)
        self.settings_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings_file_path,'w') as file:
            json.dump(settings_dict, file, sort_keys=True, indent=4)



