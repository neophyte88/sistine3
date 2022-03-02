import abc


class BaseImporter(abc.ABC):
    def __init__(self, file_content, category):
        self.file_content = file_content
        self.content = self.preprocess_file_content()
        self.category = category

    def parse_events(self):
        return [event for event in self.iter_parsed_events()]

    def iter_parsed_events(self):
        for entry in self.iter_entries():
            event = self.make_event(entry)
            yield event

    @abc.abstractmethod
    def preprocess_file_content(self):
        """
        Transforms the file content into a format that can actually help
        us parse the data

        :return:
        """
        pass

    @abc.abstractmethod
    def iter_entries(self):
        """
        Iterates through all the submitted data one entry at a time.
        For example, for CSV files, one entry is represented by a row of values

        :return: a generator object that at each iteration yields a single entry
        """
        pass

    @abc.abstractmethod
    def make_event(self, values):
        """
        Creates an event instance based on the extracted values

        :param values:
        :return:
        """
        pass
