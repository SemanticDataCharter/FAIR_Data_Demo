"""
The entity graph is derived, never invented: every node is a record the query
returned, every edge a value two of them share in an identifier component.
These tests feed the builder canned triple-store answers and check the shape
it hands the page.
"""
from django.test import SimpleTestCase, override_settings

from . import entity_graph as eg

SDC4 = eg.SDC4


def _res(rows):
    """A SPARQL JSON result from plain dict rows."""
    return {'head': {'vars': list(rows[0]) if rows else []},
            'results': {'bindings': [{k: {'type': 'uri' if str(v).startswith('http') else 'literal', 'value': v}
                                      for k, v in r.items()} for r in rows]}}


class FakeClient:
    """Answers each of the builder's four queries by what the query asks for."""

    def __init__(self, nodes, titles, values, parties, fail=False):
        self.nodes, self.titles, self.values, self.parties, self.fail = nodes, titles, values, parties, fail
        self.queries = []

    def query_sparql(self, q):
        self.queries.append(q)
        if self.fail:
            raise RuntimeError('down')
        if 'sdc4:partyRef' in q:
            return _res(self.parties)
        if 'VALUES ?mc ' in q:
            return _res(self.values)
        if 'VALUES ?label' in q:
            return _res(self.titles)
        return _res(self.nodes)


CIVIL = f'{SDC4}i-civil000000000000000001'
HEALTH = f'{SDC4}i-health00000000000000001'
EMPLOY = f'{SDC4}i-employ00000000000000001'
BIZ = f'{SDC4}i-biz00000000000000000001'
DM_CIVIL = f'{SDC4}dm-etkbxubkngv0v81yvqz77xrs'
DM_HEALTH = f'{SDC4}dm-dcsd8bxr8a6lzcptwwyms44t'
DM_EMPLOY = f'{SDC4}dm-rxv2ck9k9r1bqkggeydam32s'
DM_BIZ = f'{SDC4}dm-nb7gtyimcusmritzx0o0x40o'


def client():
    return FakeClient(
        nodes=[{'inst': CIVIL, 'dm': DM_CIVIL, 'status': 'valid', 'title': 'Civil Registry'},
               {'inst': HEALTH, 'dm': DM_HEALTH, 'status': 'invalid', 'title': 'Healthcare Record'},
               {'inst': EMPLOY, 'dm': DM_EMPLOY, 'status': 'valid', 'title': 'Employment Record'},
               {'inst': BIZ, 'dm': DM_BIZ, 'status': 'valid', 'title': 'Business Registry'}],
        titles=[{'inst': CIVIL, 'label': 'Given Name (Person)', 'v': 'Carlos'},
                {'inst': CIVIL, 'label': 'Surname (Person)', 'v': 'Mendoza'},
                {'inst': HEALTH, 'label': 'Medical Record Number', 'v': 'MRN-000001'},
                {'inst': EMPLOY, 'label': 'Employee Occupation', 'v': 'Deckhand'},
                {'inst': BIZ, 'label': 'Organization Name', 'v': 'Cordova Shipping'}],
        values=[{'a': CIVIL, 'la': 'National ID (CID)', 'mc': f'{SDC4}mc-nj7s1gk45tfgyooxpz0qaha3', 'v': 'COR-AL01-271845'},
                {'a': HEALTH, 'la': 'National ID (CID)', 'mc': f'{SDC4}mc-nj7s1gk45tfgyooxpz0qaha3', 'v': 'COR-AL01-271845'},
                {'a': BIZ, 'la': 'Business Registry Number', 'mc': f'{SDC4}mc-l8f0m7op4xhrxqy1jrnvbuly', 'v': 'BIZ-000573'},
                {'a': EMPLOY, 'la': 'Business Registry Number', 'mc': f'{SDC4}mc-l8f0m7op4xhrxqy1jrnvbuly', 'v': 'BIZ-000573'},
                {'a': CIVIL, 'la': 'City', 'mc': f'{SDC4}mc-atdtdfzruh7tya0iv5cz365l', 'v': 'Campoluz'}],
        parties=[],
    )


@override_settings(GRAPHDB_WORKBENCH_URL='http://wb.example:7200/')
class EntityGraphTests(SimpleTestCase):
    def test_every_record_is_a_node_addressed_by_the_console(self):
        g = eg.build([CIVIL, HEALTH, EMPLOY, BIZ], client())
        by = {n['iri']: n for n in g['nodes'] if n['type'] == 'record'}
        self.assertEqual(set(by), {CIVIL, HEALTH, EMPLOY, BIZ})
        self.assertEqual(by[CIVIL]['title'], 'Carlos Mendoza')
        self.assertEqual(by[CIVIL]['console_url'], '/console/instance/etkbxubkngv0v81yvqz77xrs/i-civil000000000000000001/')
        self.assertEqual(by[HEALTH]['status'], 'invalid')
        self.assertEqual(by[BIZ]['workbench_url'],
                         'http://wb.example:7200/graphs-visualizations?uri=' + BIZ.replace(':', '%3A').replace('/', '%2F'))

    def test_shared_identifiers_are_nodes_with_an_edge_per_record(self):
        g = eg.build([CIVIL, HEALTH, EMPLOY, BIZ], client())
        ids = {n['id']: n for n in g['nodes'] if n['type'] == 'identifier'}
        self.assertEqual(set(ids), {'id:person:COR-AL01-271845', 'id:business:BIZ-000573'})
        person = ids['id:person:COR-AL01-271845']
        self.assertEqual((person['kind'], person['title'], person['components'], person['degree']),
                         ('person', 'COR-AL01-271845', ['National ID (CID)'], 2))
        biz = ids['id:business:BIZ-000573']
        self.assertEqual(biz['degree'], 2)
        edges = {(e['source'], e['target']): e['label'] for e in g['edges']}
        self.assertEqual(edges[(CIVIL, 'id:person:COR-AL01-271845')], 'National ID (CID)')
        self.assertEqual(edges[(HEALTH, 'id:person:COR-AL01-271845')], 'National ID (CID)')
        self.assertEqual(edges[(BIZ, 'id:business:BIZ-000573')], 'Business Registry Number')
        self.assertEqual(edges[(EMPLOY, 'id:business:BIZ-000573')], 'Business Registry Number')
        self.assertEqual(len(g['edges']), 4)

    def test_a_value_only_one_record_carries_is_not_a_join(self):
        g = eg.build([CIVIL, HEALTH, EMPLOY, BIZ], client())
        self.assertNotIn('id:place:Campoluz', {n['id'] for n in g['nodes']})
        self.assertEqual(g['legend'], ['Business Registry', 'Civil Registry', 'Employment Record', 'Healthcare Record'])

    def test_the_join_components_are_the_only_ones_asked_for(self):
        c = client(); eg.build([CIVIL, HEALTH], c)
        value_query = next(q for q in c.queries if 'VALUES ?mc ' in q)
        for comps in eg.JOIN_KEYS.values():
            for ct in comps:
                self.assertIn(f'sdc4:mc-{ct}', value_query)
        self.assertNotIn('mc-kv5qqs3o4jwcwz9javgw1pzh', value_query)  # Province has three values: not a join

    def test_a_record_the_store_cannot_describe_still_counts(self):
        ghost = f'{SDC4}i-ghost0000000000000000001'
        g = eg.build([CIVIL, ghost], client())
        by = {n['iri']: n for n in g['nodes'] if n['type'] == 'record'}
        self.assertEqual(by[ghost]['domain'], 'unknown')
        self.assertEqual(by[ghost]['console_url'], '')

    def test_more_records_than_the_cap_is_said_not_hidden(self):
        many = [f'{SDC4}i-{i:024d}' for i in range(eg.MAX_RECORDS + 5)]
        c = client(); g = eg.build(many, c)
        self.assertTrue(g['truncated'])
        self.assertEqual(sum(1 for q in c.queries if f'<{many[-1]}>' in q), 0)

    def test_a_dead_store_leaves_a_reason_not_an_error(self):
        c = client(); c.fail = True
        g = eg.build([CIVIL], c)
        self.assertEqual(g['nodes'], [])
        self.assertIn('did not answer', g['reason'])

    def test_no_records_no_queries(self):
        c = client()
        self.assertEqual(eg.build([], c)['nodes'], [])
        self.assertEqual(c.queries, [])


class RecordVariableTests(SimpleTestCase):
    def test_record_variables_are_inst_and_numbered_inst(self):
        for v in ('inst', 'inst_2', 'inst_10'):
            self.assertTrue(eg.RECORD_VAR.fullmatch(v), v)
        for v in ('instance', 'inst_city', 'institution', 'domain'):
            self.assertIsNone(eg.RECORD_VAR.fullmatch(v), v)

    def test_record_iris_are_distinct_and_in_result_order(self):
        bindings = [{'inst': {'type': 'uri', 'value': HEALTH}, 'inst_2': {'type': 'uri', 'value': CIVIL}},
                    {'inst': {'type': 'uri', 'value': HEALTH}},
                    {'inst': {'type': 'literal', 'value': 'not an iri'}}]
        self.assertEqual(eg.record_iris_from_bindings(['x', 'inst', 'inst_2'], bindings), [HEALTH, CIVIL])
