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
        raw=b'<h1>depa Digital Startup Fund</h1><h2>Idea Stage</h2><p>Digital Startup Fund</p>'
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
        raw=(b'Zero emission vessels and infrastructure two: alternative fuels '
             b'UK registered organisations can apply. Closing date: 16 September 2026 11:00am UK time '
             b'Funding type: Grant')
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

    def test_iuk_extended_closed_opportunity_uses_current_deadline(self):
        source=source_config('iuk-zevi2-alternative-fuels')
        raw=(b'Zero emission vessels and infrastructure two: alternative fuels '
             b'Opportunity status: Closed. Closing date: 17 September 2026 11:00am UK time. '
             b'The closing date has been extended to 17 September 11am UK time due to technical issues. '
             b'Funding type: Grant. UK registered organisations can apply.')
        data=normalize(raw,source,'2026-09-23T14:47:14Z')
        for item in data['items']:
            item['provenance'].update(raw_object_key='landing/test',bronze_manifest_key='control/manifests/test')
        self.assertEqual(validate(data)['schema_version'],'grant.v2')
        item=data['items'][0]
        self.assertEqual(item['deadline'],{'kind':'fixed','at':'2026-09-17T10:00:00Z'})
        self.assertEqual(item['status'],'closed')

    def zevi(self, closing):
        return ('Zero emission vessels and infrastructure two: alternative fuels '
                'UK registered organisations can apply. Closing date: ' + closing + ' UK time '
                'Funding type: Grant').encode()

    def test_iuk_cutoff_follows_uk_summer_and_winter_time(self):
        source=source_config('iuk-zevi2-alternative-fuels')
        cases={
            '16 September 2026 11:00am':'2026-09-16T10:00:00Z',  # BST, UTC+1
            '5 November 2026 11:00am':'2026-11-05T11:00:00Z',    # GMT after 25 Oct
            '16 SEPTEMBER 2026 12:00pm':'2026-09-16T11:00:00Z',  # noon, case-insensitive month
            '16 September 2026 12:30am':'2026-09-15T23:30:00Z',  # just after midnight BST
            '25 October 2026 1:30am':'2026-10-25T00:30:00Z',     # repeated hour: earlier (BST) instant
        }
        for closing,expected in cases.items():
            with self.subTest(closing=closing):
                item=normalize(self.zevi(closing),source,'2026-09-07T00:00:00Z')['items'][0]
                self.assertEqual(item['deadline'],{'kind':'fixed','at':expected})

    def test_iuk_status_compares_instants_across_offsets(self):
        source=source_config('iuk-zevi2-alternative-fuels')
        raw=self.zevi('16 September 2026 11:00am')
        cases={'2026-09-16T09:59:59Z':'open','2026-09-16T10:00:00Z':'closed',
               '2026-09-16T16:59:59+07:00':'open','2026-09-16T17:00:00+07:00':'closed',
               '2026-09-16T05:59:59-04:00':'open'}
        for checked_at,status in cases.items():
            with self.subTest(checked_at=checked_at):
                self.assertEqual(normalize(raw,source,checked_at)['items'][0]['status'],status)

    def test_iuk_rejects_naive_clock_and_impossible_times(self):
        source=source_config('iuk-zevi2-alternative-fuels')
        with self.assertRaises(ValueError):
            normalize(self.zevi('16 September 2026 11:00am'),source,'2026-09-16T10:00:00')
        for closing in ('16 Septembre 2026 11:00am','16 September 2026 13:00pm','31 September 2026 11:00am'):
            with self.subTest(closing=closing),self.assertRaises(ValueError):
                normalize(self.zevi(closing),source,'2026-09-07T00:00:00Z')

if __name__=='__main__': unittest.main()
