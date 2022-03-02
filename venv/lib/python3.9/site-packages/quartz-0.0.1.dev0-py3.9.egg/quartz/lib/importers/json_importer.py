import json

from .base_importer import BaseImporter
from quartz.models import Event


class JsonImporter(BaseImporter):
    """

    The JSON data that must be parsed must be an array with objects
    in the following format

        {
            "__source__": "some_source",
            "field_1": "Value1",
            "field_2": "value2",
            "some_Bool_value": true,
            "some_int_value": 100
        }

    """

    def __init__(self, *args, **kwargs):
        super(JsonImporter, self).__init__(*args, **kwargs)

    def preprocess_file_content(self):
        if isinstance(self.file_content, bytes):
            self.file_content = self.file_content.decode()
        return json.loads(self.file_content)

    def iter_entries(self):
        for entry in self.content:
            yield entry

    def make_event(self, values):
        event_source = values.pop("__source__")
        event = Event()

        event.category = self.category
        event.source = event_source
        event.set_values(**values)
        return event
