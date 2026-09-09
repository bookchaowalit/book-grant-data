import base64
import json
import unittest
from book_grant_data.capture import normalize, source_config
from book_grant_data.cli import resource, validate


class SourceTests(unittest.TestCase):
    def raw(self):
        source=resource('source.json')
        if source['access']=='html': return b'<h1>Chevening in Thailand</h1><p>Open for applications until 6 October 2026, at 11:00 (UTC)</p>'
        if source['access']=='github-api': return json.dumps({'encoding':'base64','name':'about-github-education-for-students.md','content':base64.b64encode(b'title: About GitHub Education for students').decode()}).encode()
        return json.dumps({'base_path':source['source_url'].removeprefix('https://www.gov.uk'),'title':'Universal Credit' if source['domain']=='benefit' else 'Apply for innovation funding','details':{}}).encode()

    def test_parse_and_validate_v2(self):
        source=resource('source.json')
        data=normalize(self.raw(),source,'2026-09-07T00:00:00Z')
        for item in data['items']: item['provenance'].update(raw_object_key='landing/test',bronze_manifest_key='control/manifests/test')
        self.assertEqual(validate(data)['schema_version'],source['schema_version'])
        self.assertTrue(any(v is None for v in data['items'][0]['terms'].values()))

    def test_unknown_terms_not_false(self):
        data=normalize(self.raw(),resource('source.json'),'2026-09-07T00:00:00Z')
        self.assertNotIn(False,data['items'][0]['terms'].values())

    def test_source_drift_rejected(self):
        with self.assertRaises((ValueError,KeyError)):
            normalize(b'{}',resource('source.json'),'2026-09-07T00:00:00Z')

    def test_missing_lineage_rejected(self):
        data=normalize(self.raw(),resource('source.json'),'2026-09-07T00:00:00Z')
        with self.assertRaises(ValueError): validate(data)

    def test_v1_still_supported(self):
        self.assertEqual(validate(resource('demo.json'))['data_status'],'fixture')

    def test_exact_deadline_or_unknown(self):
        source=resource('source.json')
        item=normalize(self.raw(),source,'2026-09-07T00:00:00Z')['items'][0]
        if source['domain']=='scholarship':
            self.assertEqual(item['deadline']['at'],'2026-10-06T11:00:00Z')
            self.assertEqual(item['status'],'open')
            later=normalize(self.raw(),source,'2026-10-06T11:00:00Z')['items'][0]
            self.assertEqual(later['status'],'closed')
        else:
            self.assertEqual(item['deadline']['kind'],'unknown')
            self.assertEqual(item['status'],'unknown')

    def test_depa_official_directory_fixture(self):
        source=source_config('depa-digital-startup-fund')
        raw='<h1>depa Digital Startup Fund</h1><h2>Idea Stage</h2><p>Digital Startup Fund</p>'.encode()
        data=normalize(raw,source,'2026-09-07T00:00:00Z')
        for item in data['items']:
            item['provenance'].update(raw_object_key='landing/test',bronze_manifest_key='control/manifests/test')
        self.assertEqual(validate(data)['schema_version'],'grant.v2')
        item=data['items'][0]
        self.assertEqual(item['eligible_countries'],['TH'])
        self.assertEqual(item['terms']['applicant_type'],'either')
        self.assertEqual(item['value']['kind'],'cash')
        self.assertEqual(item['deadline']['kind'],'unknown')

    def test_iuk_competition_fixture_has_deadline(self):
        source=source_config('iuk-zevi2-alternative-fuels')
        raw=('Zero emission vessels and infrastructure two: alternative fuels '
             'UK registered organisations can apply. Closing date: 16 September 2026 11:00am UK time '
             'Funding type: Grant').encode()
        data=normalize(raw,source,'2026-09-07T00:00:00Z')
        for item in data['items']:
            item['provenance'].update(raw_object_key='landing/test',bronze_manifest_key='control/manifests/test')
        self.assertEqual(validate(data)['schema_version'],'grant.v2')
        item=data['items'][0]
        self.assertEqual(item['category'],'climate')
        self.assertEqual(item['eligible_countries'],['GB'])
        self.assertEqual(item['deadline'],{'kind':'fixed','at':'2026-09-16T10:00:00Z'})
        self.assertEqual(item['status'],'open')
        self.assertEqual(item['value'],{'kind':'cash','amount':None,'currency':'GBP','guaranteed':False})

if __name__=='__main__': unittest.main()
