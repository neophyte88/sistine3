import urllib.parse
import datetime
import ast
import json

import humanize
from mongoengine import connect, Document, EmbeddedDocument, ReferenceField, StringField, BooleanField, DateTimeField, \
    EmbeddedDocumentListField, BinaryField, DictField, Q, IntField, FloatField, CASCADE

from quartz.lib.util import str_interval_to_datetime


def set_db_parameters(db_url):
    parse_result = urllib.parse.urlparse(db_url)
    if parse_result.scheme != "mongo":
        raise ValueError("Invalid scheme: {}".format(parse_result.scheme))

    if not parse_result.hostname:
        hostname = "127.0.0.1"
    else:
        hostname = parse_result.hostname

    if not parse_result.port:
        port = 27017
    else:
        port = parse_result.port
    connect(db=parse_result.path.lstrip("/"), host=hostname, port=port)


class Project(Document):
    name = StringField(unique=True, required=True)
    description = StringField(default="")
    owner = StringField(required=True)

    created = DateTimeField(default=datetime.datetime.now())

    def event_count(self, hours=None):
        categories = EventCategory.objects(project=self).all()
        if hours is None:
            return sum([Event.objects(category=categ).count() for categ in categories])
        else:
            target_time = datetime.datetime.now() - datetime.timedelta(hours=hours)
            return sum(
                [Event.objects(category=categ).filter(Q(timestamp__gte=target_time)).count() for categ in categories])

    @property
    def event_category_count(self):
        return EventCategory.objects(project=self).count()

    def last_event_humanized(self):
        return "No events"


class FieldSpecs(EmbeddedDocument):
    name = StringField()
    description = StringField(default="")
    required = BooleanField(default=False)
    default = StringField(default="null")
    type = StringField(choices=("int", "str", "bool"))


class EventCategory(Document):
    name = StringField(unique=True, required=True)
    description = StringField(default="")
    project = ReferenceField(Project, reverse_delete_rule=CASCADE)

    fields = EmbeddedDocumentListField(FieldSpecs)

    @property
    def event_count(self):
        return Event.objects(category=self).count()


class Event(Document):
    category = ReferenceField(EventCategory, index=True, reverse_delete_rule=CASCADE)
    timestamp = DateTimeField(default=datetime.datetime.now)
    source = StringField(required=False)
    values = DictField()

    meta = {
        "indexes": [
            "-timestamp",
            "#category"
        ]
    }

    def set_values(self, **kwargs):
        values_dict = {}
        if isinstance(self.category, str):
            self.category = EventCategory.objects.get(id=self.category)
        fieldspecs = self.category.fields
        fieldspecs = {spec.name: spec for spec in fieldspecs}
        for k, v in kwargs.items():
            if k not in fieldspecs:
                raise ValueError("Unknown event field: {}".format(k))

            values_dict[k] = v

        for registered_field in fieldspecs:
            if registered_field not in values_dict.keys():
                if fieldspecs[registered_field].required:
                    raise ValueError("Requiered field not set: {}".format(registered_field))
                else:
                    values_dict[registered_field] = json.loads(fieldspecs[registered_field].default)

        for valuename, value in values_dict.items():
            if not self.type_matches(value, fieldspecs[valuename].type):
                raise ValueError("Type mismatch: {}".format(valuename))
        self.values = values_dict

    def type_matches(self, value, type):
        if type not in ("int", "str", "bool"):
            raise ValueError("Invalid type name")
        type_class = eval(type)
        return isinstance(value, type_class)

    @classmethod
    def filter_by_query(cls, query_parse_result):
        """
        Filters queries based on the query parse result

        :param parse_result:
        :return:
        """
        operator_sign_to_string = {
            "=": "",
            ">": "__gt",
            "<": "__lt",
            ">=": "__gte",
            "<=": "__lte"
        }
        metadata_fields = {
            "__timestamp__": "timestamp",
            "__source__": "source"
        }

        print(query_parse_result)
        category = EventCategory.objects.get(name=query_parse_result.category_name)

        final_clauses = {}
        for clause in query_parse_result.clauses:
            key = metadata_fields.get(clause.name, clause.name)
            key += operator_sign_to_string[clause.operator]
            final_clauses[key] = clause.value

        events = cls.objects(Q(**final_clauses) & Q(category=category)).order_by("timestamp").all()
        return events


class QueryHistory(Document):
    from_ip = StringField()
    query = StringField()
    timestamp = DateTimeField(default=datetime.datetime.now)
    result_count = IntField(default=0)
    runtime = FloatField()

    meta = {
        "indexes": [
            "-timestamp"
        ]
    }

    @classmethod
    def get_last_queries(cls, count=5):
        return cls.objects().all().order_by("-timestamp").limit(count)

    @classmethod
    def create_new(cls, from_ip, query, results, runtime):
        instance = cls()
        instance.from_ip = from_ip
        instance.query = query
        instance.result_count = len(results)
        instance.runtime = runtime
        instance.save()

    @property
    def humanized_timestamp(self):
        return humanize.naturaltime(self.timestamp)


class Template(Document):
    """
    Default context:

    datetime_now - datetime.datetime.now()
    query("...") - yields events based on the query
    plot("line", query("..."), "field") - draws a plot of type "line" with the queries yielded by the query using the
        "field" field.

    """
    name = StringField()
    description = StringField()
    body = BinaryField()


class ReportSchedule(Document):
    name = StringField()
    description = StringField()
    smtp_parameters = DictField()
    template = ReferenceField(Template, reverse_delete_rule=CASCADE)
    crontab = StringField()


if __name__ == '__main__':
    Project(name="test.6", description="Just a test project", owner="rpg").save()
    Project(name="test.7", description="Just a test project", owner="rpg").save()
    Project(name="test.8", description="Just a test project", owner="rpg").save()
    Project(name="test.9", description="Just a test project", owner="rpg").save()
    Project(name="test.10", description="Just a test project", owner="rpg").save()
