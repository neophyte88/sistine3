import os
import time
import json
import base64

from tornado.web import RedirectHandler
from gemstone import MicroService, public_method

from quartz.handlers.page_handlers import DashboardHandler, ProjectsHandler, PlotsHandler, EventsHandler, \
    StatusHandler, CreateProjectHandler, ViewProjectHandler, EditProjectHandler, CreateEventCategoryHandler, \
    ViewEventCategory, AboutHandler, DocsHandler, EventsStatisticsHandler, ImportDataHandler, PlotsPyplotHandler, \
    ReportsRulesHandler, ReportsTemplatesHandler
from quartz.lib.query import QueryParser
from quartz.lib.importers.json_importer import JsonImporter
from quartz.lib.importers.xml_importer import XmlImporter
from quartz.models import Project, FieldSpecs, EventCategory, Event, QueryHistory
from quartz.lib.pyplot_charter import PyplotCharter


class QuartzService(MicroService):
    name = "quartz"
    host = "127.0.0.1"
    port = 8000

    api_token_header = "X-Api-Token"
    max_parallel_blocking_tasks = os.cpu_count()

    extra_handlers = [
        ("/projects/view/([a-f0-9]+)", ViewProjectHandler),
        ("/projects/view/([a-f0-9]+)/edit", EditProjectHandler),
        ("/projects/view/([a-f0-9]+)/create_category", CreateEventCategoryHandler),
        ("/projects/view/([a-f0-9]+)/categories/([a-f0-9]+)", ViewEventCategory),
        ("/dashboard", DashboardHandler),
        ("/reports/templates", ReportsTemplatesHandler),
        ("/reports/rules", ReportsRulesHandler),
        ("/projects", ProjectsHandler),
        ("/plots/pyplot", PlotsPyplotHandler),
        ("/plots", PlotsHandler),
        ("/events", EventsHandler),
        ("/events/statistics", EventsStatisticsHandler),
        ("/events/import", ImportDataHandler),
        ("/status", StatusHandler),
        ("/projects/create", CreateProjectHandler),
        ("/about", AboutHandler),
        ("/docs", DocsHandler),
        ("/", RedirectHandler, {"url": "/about"}),
    ]

    root_directory = os.path.dirname(os.path.abspath(__file__))
    # create your templates
    template_dir = os.path.join(root_directory, "html", "templates")

    # setup your static files
    static_dirs = [
        (r"/static", os.path.join(root_directory, "html", "static")),
    ]

    # service registries
    service_registry_urls = []
    service_registry_ping_interval = 30

    def __init__(self, host, port, registry=None, accessible_at=None):
        """
        Initializes some parameters of the Quartz service

        :param host: address to bind to
        :param port: port to bind to
        :param registry: a list of service registry hosts
        """
        super(QuartzService, self).__init__()
        self.host = host
        self.port = port
        if registry:
            self.service_registry_urls = registry
        if accessible_at:
            self.accessible_at = accessible_at

    @public_method
    def create_project(self, name, description, owner):
        if not name or not description or not owner:
            raise ValueError("Bad parameters submitted")
        project = Project(name=name, description=description, owner=owner)
        project.save()
        return str(project.id)

    @public_method
    def update_project(self, project_id, name=None, description=None, owner=None):
        project = Project.objects.get(id=project_id)
        if name:
            project.name = name
        if description:
            project.description = description
        if owner:
            project.owner = owner
        project.save()
        return True

    @public_method
    def delete_project(self, project_id):
        project = Project.objects.get(id=project_id)
        project.delete()
        return True

    @public_method
    def create_category(self, name, description, project_id, fields):
        field_specs = [FieldSpecs(**fieldspec) for fieldspec in fields]

        if len(set([f["name"] for f in field_specs])) != len(field_specs):
            raise ValueError("Duplicate value name")

        event_category = EventCategory(name=name, description=description, project=project_id, fields=field_specs)
        event_category.save()
        return str(event_category.id)

    @public_method
    def submit_event(self, source, category, values):
        event = Event()
        event.source = source
        event.category = category
        event.set_values(**values)

        event.save()
        return str(event.id)

    @public_method
    def query_events(self, query, save_history=True):
        _start = time.time()
        parse_result = QueryParser().parse_query(query)
        events = Event.filter_by_query(parse_result)
        to_return = [{
                         "timestamp": event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                         "values": event.values,
                         "source": event.source
                     } for event in events]
        _duration = time.time() - _start

        if save_history:
            QueryHistory.create_new("unknown", query, events, _duration)

        return to_return

    @public_method
    def query_events_for_field(self, query, field):
        items = self.query_events(query)
        return [{"timestamp": item["timestamp"], "value": item["values"][field]} for item in items]

    @public_method
    def import_event_data(self, category, source_type, content):
        if source_type == "csv":
            raise NotImplementedError()
        importers = {
            "json": JsonImporter,
            "xml": XmlImporter
        }

        if source_type not in ("csv", "xml", "json"):
            raise ValueError("Invalid source_type. Only 'csv', 'xml' or 'json' supported")
        category_obj = EventCategory.objects.get(id=category)
        source_content = base64.b64decode(content.encode())
        events = [ev for ev in importers[source_type](source_content, category_obj).iter_parsed_events()]

        Event.objects.insert(events)
        return {
            "count": len(events)
        }

    @public_method
    def build_pyplot_chart(self, query, title, by_field, chart_type):
        result = {}
        _time = time.time()
        print(query, title, by_field, chart_type)
        events = self.query_events(query, save_history=False)

        result["query_duration"] = time.time() - _time
        result["event_count"] = len(events)

        _time = time.time()
        plot_data = PyplotCharter(events).make_plot(by_field, chart_type, title)

        result["chart_generation_duration"] = time.time() - _time
        result["plot_image"] = plot_data
        return result

    # Implement your token validation logic
    def api_token_is_valid(self, api_token):
        return True
