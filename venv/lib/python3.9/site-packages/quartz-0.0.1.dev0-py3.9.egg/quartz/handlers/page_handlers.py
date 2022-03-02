import datetime
from collections import namedtuple
import random
from concurrent.futures import ThreadPoolExecutor
import logging

import humanize
from mongoengine import DoesNotExist
from mongoengine.connection import get_connection
from tornado.web import RequestHandler, HTTPError
from tornado.gen import coroutine

from quartz import __version__
from quartz.models import Project, EventCategory, FieldSpecs, Event, QueryHistory

ProjectMock = namedtuple("Project", "name description owner category_count event_count last_event_humanized")


def test_get_projects():
    for i in range(30):
        yield ProjectMock(name="test.project.{}".format(i), description="Test project", owner="Vlad Calin",
                          category_count=random.randint(10, 200), event_count=random.randint(0, 100000),
                          last_event_humanized=humanize.naturaltime(
                              datetime.datetime.now() - datetime.timedelta(minutes=random.randint(0, 100))))


_executor = ThreadPoolExecutor()


class DashboardHandler(RequestHandler):
    @coroutine
    def get(self):
        projects = yield _executor.submit(Project.objects.all())
        ordered = list(sorted(projects, key=lambda x: x.event_count(hours=1)))[:5]

        event_category_count = sum([x.event_category_count for x in projects])
        event_count = Event.objects.count()

        self.render("dashboard.html", version=__version__, require_plots=True, require_datatable=False,
                    project_count=len(projects),
                    projects=ordered, event_count=event_count, event_category_count=event_category_count)


class AboutHandler(RequestHandler):
    @coroutine
    def get(self):
        self.render("about.html", version=__version__, require_plots=False, require_datatable=False)


class ReportsTemplatesHandler(RequestHandler):
    @coroutine
    def get(self):
        self.render("reports_templates.html", version=__version__, require_plots=False, require_datatable=False)


class ReportsRulesHandler(RequestHandler):
    @coroutine
    def get(self):
        self.render("reports_rules.html", version=__version__, require_plots=False, require_datatable=False)


class DocsHandler(RequestHandler):
    @coroutine
    def get(self):
        self.render("docs.html", version=__version__, require_plots=False, require_datatable=False)


class EventsStatisticsHandler(RequestHandler):
    @coroutine
    def get(self):
        self.render("events_statistics.html", version=__version__, require_plots=False, require_datatable=False)


class ImportDataHandler(RequestHandler):
    @coroutine
    def get(self):
        categories = yield _executor.submit(EventCategory.objects.all)
        self.render("events_import_data.html", version=__version__, require_plots=False, require_datatable=False,
                    categories=categories)


class ProjectsHandler(RequestHandler):
    @coroutine
    def get(self):
        projects = yield _executor.submit(Project.objects.all())

        self.render("projects.html", version=__version__, require_plots=False, require_datatable=True,
                    projects=projects)


class PlotsHandler(RequestHandler):
    @coroutine
    def get(self):
        self.render("plots.html", version=__version__, require_plots=True, require_datatable=False)


class PlotsPyplotHandler(RequestHandler):
    @coroutine
    def get(self):
        self.render("plots_img.html", version=__version__, require_plots=False, require_datatable=False)


class EventsHandler(RequestHandler):
    @coroutine
    def get(self):
        initial_query = self.get_argument("query", None)
        history = QueryHistory.get_last_queries(10)

        self.render("events.html", version=__version__, require_plots=False, require_datatable=True,
                    initial_query=initial_query, history=history)


class StatusHandler(RequestHandler):
    @coroutine
    def get(self):
        db_conn = get_connection()
        eventer_db = db_conn["eventer"]
        project_stats = eventer_db.command("collstats", "project")
        category_stats = eventer_db.command("collstats", "event_category")
        event_stats = eventer_db.command("collstats", "event")

        project_size = humanize.naturalsize(project_stats["storageSize"])
        project_index_size = humanize.naturalsize(project_stats["totalIndexSize"])

        category_size = humanize.naturalsize(category_stats["storageSize"])
        category_index_size = humanize.naturalsize(category_stats["totalIndexSize"])

        event_size = humanize.naturalsize(event_stats["storageSize"])
        event_index_size = humanize.naturalsize(event_stats["totalIndexSize"])
        event_count = event_stats["count"]
        event_avg_size = humanize.naturalsize(event_stats.get("avgObjSize", 0))

        self.render("status.html", version=__version__, require_plots=True, require_datatable=False,

                    project_size=project_size, project_index_size=project_index_size,
                    category_size=category_size, category_index_size=category_index_size,
                    event_size=event_size, event_index_size=event_index_size, event_count=event_count,
                    event_avg_size=event_avg_size)


class CreateProjectHandler(RequestHandler):
    @coroutine
    def get(self):
        self.render("create_project.html", version=__version__, require_plots=False, require_datatable=False)


class ViewProjectHandler(RequestHandler):
    @coroutine
    def get(self, proj_id, *args, **kwargs):
        try:
            project = yield _executor.submit(Project.objects.get, id=proj_id)
            categories = yield _executor.submit(EventCategory.objects, project=proj_id)
        except DoesNotExist:
            raise HTTPError(404)
        self.render("project_view.html", version=__version__, require_plots=False, require_datatable=False,
                    project=project, categories=categories)


class EditProjectHandler(RequestHandler):
    @coroutine
    def get(self, proj_id, *args, **kwargs):
        try:
            project = yield _executor.submit(Project.objects.get, id=proj_id)
        except DoesNotExist:
            raise HTTPError(404)
        self.render("project_edit.html", version=__version__, require_plots=False, require_datatable=False,
                    project=project)


class CreateEventCategoryHandler(RequestHandler):
    @coroutine
    def get(self, proj_id, *args, **kwargs):
        try:
            project = yield _executor.submit(Project.objects.get, id=proj_id)
        except DoesNotExist:
            raise HTTPError(404)
        self.render("create_category.html", version=__version__, require_plots=False, require_datatable=False,
                    project=project)


class ViewEventCategory(RequestHandler):
    @coroutine
    def get(self, proj_id, event_category_id):
        try:
            project = yield _executor.submit(Project.objects.get, id=proj_id)
            event_category = yield _executor.submit(EventCategory.objects.get, id=event_category_id)

            total_events = yield _executor.submit(Event.objects(category=event_category).count)
            last_submitted_event = yield _executor.submit(
                Event.objects(category=event_category).only('timestamp', 'source').order_by("-timestamp").first)
        except DoesNotExist:
            raise HTTPError(404)
        self.render("category_view.html", version=__version__, require_plots=False, require_datatable=True,
                    project=project, event_category=event_category, event_count=total_events,
                    last_submit_time=(
                        humanize.naturaltime(last_submitted_event.timestamp) if last_submitted_event else "No events"),
                    last_submit_source=(last_submitted_event.source if last_submitted_event else "No events"))
