import re
import datetime

from pyparsing import oneOf, Regex, QuotedString, Literal, delimitedList, Optional

"""
query :- action + collection + "where" + filter_clauses + compact_clauses

action :- "select"

collection :- ("\"" + [a-zA-Z0-9_\.]+ + "\"") OR ("\'" + [a-zA-Z0-9_\.]+ + "\'")

filter_clauses :- single_filter_clause OR (single_filter_clause + "and" + filter_clauses)
single_filter_clause :- basic_filter OR predicate_filter
basic_filter :- identifier + operator + value
predicate_filter :- predicate_name + "(" + parameters + ")"

compact_clauses :- "compact by" + single_compact_clause
single_compact_clause :- compact_rule + "(" + identifier + "," + value + ")"

parameters :- single_param OR (single_param + "," + parameters)
single_parameter :- identifier OR value

identifier :- special_attr OR regular_attr
value :- string_value OR integer_value OR boolean_value

operator :- "=" OR "<" OR ">" OR "<=" OR ">="
special_attr :- "__timestamp__" OR "__source__"
regular_attr :- [a-zA-Z9-0_]+
string_value :- ("'" + .* + "'") OR ("\"" + .* + "\"")
integer_value :- \d+
boolean_value :- "True" OR "TRUE" OR "true" OR "False" OR "FALSE" OR "false"

"""

# region Query grammar definition

boolean_value = oneOf("True TRUE true False FALSE false")
integer_value = Regex(r'\d+')
float_value = Regex(r'\d+\.\d*')
string_value = QuotedString("'") | QuotedString('"')
relative_time_value = Regex("\d+[hm]")

operator = oneOf("= < > <= >=")

regular_attribute = Regex("[a-zA-Z_]+[a-zA-Z0-9_]*")
special_attribute = oneOf("__timestamp__ __source__")

identifier = regular_attribute | special_attribute
value = boolean_value | relative_time_value | float_value | integer_value | string_value

compact_function_name = oneOf("sum avg max min")

action = oneOf("select")
category_name = ("'" + Regex(r"[a-zA-Z_]+[a-zA-Z._]*") + "'") | \
                ('"' + Regex(r"[a-zA-Z_]+[a-zA-Z._]*") + '"')

single_filter_clause = identifier + operator + value
filter_clauses = delimitedList(single_filter_clause, delim="and")

compact_clause = compact_function_name + "(" + delimitedList(identifier | value) + ")"

query_grammar = action + category_name + "where" + filter_clauses + Optional("compact by" + compact_clause)


# endregion

class ParsedClause(object):
    relative_datetime_pattern = re.compile("(\d+)(h|m)")

    def __init__(self, name, operator, value):
        self.name = name
        self.operator = operator
        self.value = self._parse_value(value)

    def _parse_value(self, value):
        normalized_value = None

        # check if it is a string
        if value.startswith("'") and value.endswith("'"):
            normalized_value = value.strip("'")
        if value.startswith('"') and value.endswith('"'):
            normalized_value = value.strip('"')
        if normalized_value:
            return normalized_value

        # check if int
        try:
            normalized_value = int(value)
        except ValueError:
            pass
        else:
            return normalized_value

        # check if bool
        if value.lower() == "true":
            normalized_value = True
        if value.lower() == "false":
            normalized_value = False
        if normalized_value:
            return normalized_value

        # check if datetime relative to today
        check = self.relative_datetime_pattern.match(value)
        if check:
            if check.group(2) == "h":
                relative_delta = datetime.timedelta(hours=int(check.group(1)))
            elif check.group(2) == "m":
                relative_delta = datetime.timedelta(minutes=int(check.group(1)))
            else:
                raise ValueError("Invalid relative time delta suffix: {}".format(check.group(2)))
            normalized_value = datetime.datetime.now() - relative_delta

        if normalized_value:
            return normalized_value

        raise ValueError("Could not determine the type of value: {}".format(value))

    def __repr__(self):
        return "<{0} {1} {2}>".format(self.name, self.operator, self.value)


class ParsedQuery(object):
    def __init__(self):
        self.action = None
        self.category_name = None
        self.clauses = []
        self.compact_clause = None

    def add_clause(self, clause):
        self.clauses.append(clause.asList())

    def set_action(self, a, b, action):
        self.action = action.asList()

    def set_category_name(self, a, b, catname):
        self.category_name = catname.asList()[1]

    def set_compact_clause(self, a, b, compact_clause):
        tmp = compact_clause.asList()
        self.compact_clause = (tmp[0], tmp[2:-1])

    def __repr__(self):
        return "<ParsedQuery category={0} clauses={1} compact={2}>".format(self.category_name, self.clauses,
                                                                           self.compact_clause)


class QueryParser(object):
    def __init__(self):
        pass

    def parse_query(self, query_string):
        parsed = ParsedQuery()

        action.setParseAction(parsed.set_action)
        category_name.setParseAction(parsed.set_category_name)
        single_filter_clause.setParseAction(parsed.add_clause)
        compact_clause.setParseAction(parsed.set_compact_clause)

        query_grammar.parseString(query_string)
        print(parsed)

        return None


if __name__ == '__main__':
    query = 'select "relevant_events" where __timestamp__ >= 1h and field_1 == "hello" and field_2>=0'
    parse_result = QueryParser().parse_query(
        'select "relevant_events" where __timestamp__ >= 2h and __timestamp__ <= 1h and field_1 '
        '= "hello world" and field_2 = 0 and field_3 = "qweqweqwe" compact by sum(field_1, 3)')

    print(parse_result)
