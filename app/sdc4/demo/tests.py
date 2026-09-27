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
        if 'VALUES ?ra ' in q:
            return _res(self.values)
        if 'VALUES ?r ' in q:
            return _res(self.titles)
        return _res(self.nodes)


PART = f'{SDC4}i-nhanesp0000000000000001'
MED = f'{SDC4}i-nhanesm0000000000000001'
RESP = f'{SDC4}i-brfss000000000000000001'
BENE = f'{SDC4}i-cmsbene00000000000000001'
DM_PART = f'{SDC4}dm-xy8upneajsb8vdcmnve01g6g'
DM_MED = f'{SDC4}dm-epbdfmvxc3gbh5f66hhb3o2m'
DM_RESP = f'{SDC4}dm-iymux9kjv8ndbkoi36xzx17i'
DM_BENE = f'{SDC4}dm-fnv3zi2btk3s0sfodjsc25eb'
SEQN = f'{SDC4}mc-uto4zszvpicva38wx77knz5y'
SMOKING = f'{SDC4}mc-n7pn5ctqo81v0v418hez5zv5'
DIABETES = f'{SDC4}mc-fzpb9xr5jg2m3e3dzmvi1v3h'
SYSTOLIC = f'{SDC4}mc-r1ve12xphsb5hu2yjmhksw5h'


def client():
    return FakeClient(
        nodes=[{'inst': PART, 'dm': DM_PART, 'status': 'valid', 'title': 'NHANES Participant'},
               {'inst': MED, 'dm': DM_MED, 'status': 'invalid', 'title': 'NHANES Medication'},
               {'inst': RESP, 'dm': DM_RESP, 'status': 'valid', 'title': 'BRFSS Respondent'},
               {'inst': BENE, 'dm': DM_BENE, 'status': 'valid', 'title': 'CMS Beneficiary'}],
        titles=[{'inst': PART, 'label': 'Respondent Sequence Number (SEQN)', 'v': '93705'},
                {'inst': MED, 'label': 'Generic Drug Name (RXDDRUG)', 'v': 'ATORVASTATIN'},
                {'inst': MED, 'label': 'Respondent Sequence Number (SEQN)', 'v': '93705'},
                {'inst': RESP, 'label': 'Annual Sequence Number (SEQNO)', 'v': '2022000001'},
                {'inst': BENE, 'label': 'Beneficiary Code (DESYNPUF_ID)', 'v': '00013D2EFD8E45D1'}],
        values=[{'a': PART, 'la': 'Respondent Sequence Number (SEQN)', 'mc': SEQN, 'v': '93705'},
                {'a': MED, 'la': 'Respondent Sequence Number (SEQN)', 'mc': SEQN, 'v': '93705'},
                {'a': PART, 'la': 'Smoking Status', 'mc': SMOKING, 'v': 'Former smoker'},
                {'a': RESP, 'la': 'Smoking Status', 'mc': SMOKING, 'v': 'Never smoker'},
                {'a': RESP, 'la': 'Condition: Diabetes', 'mc': DIABETES, 'v': 'No'},
                {'a': BENE, 'la': 'Condition: Diabetes', 'mc': DIABETES, 'v': 'Yes'},
                {'a': PART, 'la': 'Systolic Blood Pressure', 'mc': SYSTOLIC, 'v': '124'}],
        parties=[],
    )


@override_settings(GRAPHDB_WORKBENCH_URL='http://wb.example:7200/')
class EntityGraphTests(SimpleTestCase):
    def test_every_record_is_a_node_addressed_by_the_console(self):
        g = eg.build([PART, MED, RESP, BENE], client())
        by = {n['iri']: n for n in g['nodes'] if n['type'] == 'record'}
        self.assertEqual(set(by), {PART, MED, RESP, BENE})
        self.assertEqual(by[PART]['title'], '93705')
        self.assertEqual(by[MED]['title'], 'ATORVASTATIN')   # the drug name names the record, the SEQN is the fallback
        self.assertEqual(by[PART]['console_url'], '/console/instance/xy8upneajsb8vdcmnve01g6g/i-nhanesp0000000000000001/')
        self.assertEqual(by[MED]['status'], 'invalid')
        self.assertEqual(by[BENE]['workbench_url'],
                         'http://wb.example:7200/graphs-visualizations?uri=' + BENE.replace(':', '%3A').replace('/', '%2F'))

    def test_a_shared_subject_identifier_is_a_node_with_an_edge_per_record(self):
        g = eg.build([PART, MED, RESP, BENE], client())
        ids = {n['id']: n for n in g['nodes'] if n['type'] == 'identifier'}
        self.assertEqual(set(ids), {'id:nhanes-participant:93705'})
        seqn = ids['id:nhanes-participant:93705']
        self.assertEqual((seqn['kind'], seqn['title'], seqn['components'], seqn['degree']),
                         ('nhanes-participant', '93705', ['Respondent Sequence Number (SEQN)'], 2))
        edges = {(e['source'], e['target']): e['label'] for e in g['edges']}
        self.assertEqual(edges[(PART, 'id:nhanes-participant:93705')], 'Respondent Sequence Number (SEQN)')
        self.assertEqual(edges[(MED, 'id:nhanes-participant:93705')], 'Respondent Sequence Number (SEQN)')

    def test_a_component_two_studies_compose_is_a_node_labelled_with_each_value(self):
        g = eg.build([PART, MED, RESP, BENE], client())
        comps = {n['id']: n for n in g['nodes'] if n['type'] == 'component'}
        self.assertEqual(set(comps), {f'comp:{eg._local(SMOKING)[3:]}', f'comp:{eg._local(DIABETES)[3:]}'})
        smoking = comps[f'comp:{eg._local(SMOKING)[3:]}']
        self.assertEqual((smoking['title'], smoking['degree'], smoking['studies']),
                         ('Smoking Status', 2, ['BRFSS Respondent', 'NHANES Participant']))
        edges = {(e['source'], e['target']): e['label'] for e in g['edges']}
        self.assertEqual(edges[(PART, smoking['id'])], 'Smoking Status = Former smoker')
        self.assertEqual(edges[(RESP, smoking['id'])], 'Smoking Status = Never smoker')
        self.assertEqual(edges[(BENE, f'comp:{eg._local(DIABETES)[3:]}')], 'Condition: Diabetes = Yes')
        self.assertEqual(len(g['edges']), 6)

    def test_a_value_only_one_record_carries_is_not_a_join(self):
        g = eg.build([PART, MED, RESP, BENE], client())
        self.assertNotIn(f'comp:{eg._local(SYSTOLIC)[3:]}', {n['id'] for n in g['nodes']})
        self.assertEqual(g['legend'], ['BRFSS Respondent', 'CMS Beneficiary', 'NHANES Medication', 'NHANES Participant'])

    def test_the_join_components_are_the_only_ones_asked_for(self):
        c = client(); eg.build([PART, RESP], c)
        value_query = next(q for q in c.queries if 'VALUES ?ra ' in q)
        for comps in eg.JOIN_KEYS.values():
            for ct in comps:
                self.assertIn(f'/dm/v_{ct}_nhanesp0000000000000001>', value_query)   # the reifier of the component in the record
        for ct in eg.SHARED_COMPONENTS:
            self.assertIn(f'/dm/v_{ct}_brfss000000000000000001>', value_query)
        self.assertNotIn('v_uk8p1ggkgmm2ma4q97htm5lb_', value_query)  # income-to-poverty ratio: one study, not a join

    def test_a_record_the_store_cannot_describe_still_counts(self):
        ghost = f'{SDC4}i-ghost0000000000000000001'
        g = eg.build([PART, ghost], client())
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
        g = eg.build([PART], c)
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
        bindings = [{'inst': {'type': 'uri', 'value': MED}, 'inst_2': {'type': 'uri', 'value': PART}},
                    {'inst': {'type': 'uri', 'value': MED}},
                    {'inst': {'type': 'literal', 'value': 'not an iri'}}]
        self.assertEqual(eg.record_iris_from_bindings(['x', 'inst', 'inst_2'], bindings), [MED, PART])
