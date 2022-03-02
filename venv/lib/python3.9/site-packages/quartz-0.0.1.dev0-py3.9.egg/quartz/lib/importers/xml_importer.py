import xml.etree.ElementTree as ET

from .base_importer import BaseImporter
from quartz.models import Event


class XmlImporter(BaseImporter):
    """

    The XML data that must be in the following format

        <data>
            <event>
                <source>Some name</source>
                <field name="some_field" value="some_value">
                <field name="some_boolean_field" value="true">
                <field name="some_int_field" value="10">
            </event>
            <event>
                ...
            </event>
        </data>

    """

    def __init__(self, *args, **kwargs):
        super(XmlImporter, self).__init__(*args, **kwargs)

    def preprocess_file_content(self):
        if isinstance(self.file_content, bytes):
            self.file_content = self.file_content.decode()
        tree = ET.fromstring(self.file_content)
        return tree

    def iter_entries(self):
        for entry in self.content:
            if entry.tag != "event":
                raise ValueError("Invalid tag: {}".format(entry.tag))
            yield entry

    def make_event(self, values):
        # TODO: Make this accept values other than strings
        event_source = None
        element_values = {}
        for child in values:
            if child.tag == "source" and event_source is None:
                event_source = child.text
            elif child.tag == "field":
                element_values[child.attrib["name"]] = child.attrib["value"]
            else:
                if child.tag == "source":
                    raise ValueError("Duplicate tag 'source'")
                raise ValueError("Invalid tag: '{}'".format(child.tag))
        event = Event()

        event.category = self.category
        event.source = event_source
        event.set_values(**element_values)
        return event
