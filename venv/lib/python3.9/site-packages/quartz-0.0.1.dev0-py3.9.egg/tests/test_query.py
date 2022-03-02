from unittest import TestCase

from quartz.lib.query import QueryParser, ParsedQuery


class QueryUnitTests(TestCase):
    def test_query_category_name(self):
        query = 'select "category" where name = "irrelevant"'
        parsed = QueryParser().parse_query(query)
        self.assertEqual(parsed.category_name, "category")

        query = 'select "name.with.dots" where name = 1'
        parsed = QueryParser().parse_query(query)
        self.assertEqual(parsed.category_name, "name.with.dots")

        query = 'select "name_with_underscores" where name = 1'
        parsed = QueryParser().parse_query(query)
        self.assertEqual(parsed.category_name, "name_with_underscores")

        query = 'select "invalid,name,with,commas" where name = 1'
        with self.assertRaises(SyntaxError):
            parsed = QueryParser().parse_query(query)

        query = 'select "invalid name with spaces" where name = 1'
        with self.assertRaises(SyntaxError):
            parsed = QueryParser().parse_query(query)

    @staticmethod
    def contains_clause(clauses, name):
        for clause in clauses:
            if clause.name == name:
                return True
        return False

    def test_query_metadata_fields(self):
        query = 'select "category" where __timestamp__ >= 24h'
        parsed = QueryParser().parse_query(query)
        self.assertTrue(self.contains_clause(parsed.clauses, "__timestamp__"))

        query = 'select "category" where __source__ = "tester"'
        parsed = QueryParser().parse_query(query)
        self.assertTrue(self.contains_clause(parsed.clauses, "__source__"))
