"""One explicit official source; all unsupported facts remain unknown."""
import base64
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo
from .cli import resource, validate


class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.hidden=0
    def handle_starttag(self, tag, attrs):
        if tag in {'script','style'}: self.hidden += 1
    def handle_endtag(self, tag):
        if tag in {'script','style'}: self.hidden = max(0,self.hidden-1)
    def handle_data(self, value):
        if not self.hidden: self.parts.append(value)


def _normalize_generic(raw, source, checked_at):
    if source.get('access') == 'govuk-api':
        body = json.loads(raw)
        if not isinstance(body, dict) or not isinstance(body.get('details'), dict):
            raise ValueError('unexpected GOV.UK document')
        text = ' '.join(str(body.get(key, '')) for key in ('title', 'description', 'details'))
    else:
        parser = Text(); parser.feed(raw.decode('utf-8'))
        text = ' '.join(' '.join(parser.parts).split())
    folded = text.casefold()
    markers = source.get('required_markers') or [source['title']]
    if not all(marker.casefold() in folded for marker in markers):
        raise ValueError('generic grant source drift or challenge page')
    schema = resource('schema-v2.json')
    terms = {key: None for key in schema['properties']['items']['items']['properties']['terms']['properties']}
    terms.update(source.get('normalized_terms', {}))
    record_id = source['id']
    item = {
        'id': record_id, 'title': source['title'], 'record_kind': source['record_kind'],
        'category': source['category'], 'source_url': source['source_url'],
        'provider': source['provider'], 'status': source.get('status', 'unknown'),
        'deadline': {'kind': source.get('deadline_kind', 'unknown'), 'at': None},
        'eligible_countries': source.get('eligible_countries', ['GLOBAL']),
        'eligibility_text': source['eligibility_text'],
        'value': {'kind': source.get('value_kind', 'unknown'), 'amount': source.get('value_amount'),
                  'currency': source.get('value_currency'), 'guaranteed': source.get('value_guaranteed')},
        'cost': {'fee_amount': None, 'currency': None, 'auto_renewal': None, 'notes': source['cost_notes']},
        'terms': terms, 'related_records': [],
        'provenance': {'evidence_kind': 'captured', 'source_id': source['id'],
                       'source_record_id': record_id, 'checked_at': checked_at,
                       'raw_object_key': None, 'bronze_manifest_key': None},
    }
    return {'schema_version': source['schema_version'], 'source': source['product'],
            'retrieved_at': checked_at, 'data_status': 'live', 'items': [item]}


def normalize(raw, source, checked_at):
    if source.get('generic_html'):
        return _normalize_generic(raw, source, checked_at)
    schema=resource('schema-v2.json')
    terms={key:None for key in schema['properties']['items']['items']['properties']['terms']['properties']}
    deadline={'kind':'unknown','at':None}
    status='unknown'
    countries=[]
    if source['access']=='govuk-api':
        body=json.loads(raw)
        if body.get('base_path') != source['source_url'].removeprefix('https://www.gov.uk') or not isinstance(body.get('details'),dict):
            raise ValueError('unexpected GOV.UK document')
        title=body.get('title')
        expected={'grant':'Apply for innovation funding','benefit':'Universal Credit'}[source['domain']]
        if title != expected: raise ValueError('source title drift')
        eligibility='UK program; read current eligibility and residence or organization requirements at the official source.'
        if source['domain']=='benefit': terms['jurisdiction']='United Kingdom'
    elif source['access']=='github-api':
        body=json.loads(raw)
        if body.get('encoding')!='base64' or body.get('name')!='about-github-education-for-students.md':
            raise ValueError('unexpected GitHub content')
        text=base64.b64decode(''.join(body['content'].split()),validate=True).decode('utf-8')
        if 'title: About GitHub Education for students' not in text or 'student' not in text.lower():
            raise ValueError('student benefits source drift')
        title='GitHub Education student benefits'
        terms['delivery_kind']='access'
        eligibility='Student verification and current GitHub Education requirements apply; partner offers have separate terms.'
    elif source['id']=='depa-digital-startup-fund':
        parser=Text(); parser.feed(raw.decode('utf-8'))
        text=' '.join(' '.join(parser.parts).split())
        if 'Digital Startup Fund' not in text or 'depa' not in text.lower() or 'Idea Stage' not in text:
            raise ValueError('depa source drift or challenge page')
        title='depa Digital Startup Fund (Thailand)'
        countries=['TH']
        eligibility='Thailand digital startup funding directory; current round, applicant type, required documents and submission window must be verified at the official depa source.'
        terms['funding_purpose']='Digital startup business promotion and support.'
        terms['applicant_type']='either'
    elif source['id']=='iuk-zevi2-alternative-fuels':
        parser=Text(); parser.feed(raw.decode('utf-8'))
        text=' '.join(' '.join(parser.parts).split())
        lower=text.casefold()
        required=('zero emission vessels and infrastructure two: alternative fuels' in lower and 'closing date:' in lower and '16 september 2026' in lower and 'funding type:' in lower and 'grant' in lower and 'uk registered' in lower)
        if not required:
            raise ValueError('Innovate UK ZEVI source drift or challenge page')
        title='Zero Emission Vessels and Infrastructure 2: Alternative Fuels'
        countries=['GB']
        eligibility='UK registered organisations can apply for a share of the published competition funding; project, collaboration and clean maritime eligibility terms must be verified at the official source.'
        terms['funding_purpose']='Develop, deploy and operate innovative clean maritime solutions in a real-world environment.'
        terms['applicant_type']='organization'
        terms['reporting_obligation']='Project delivery, monitoring and competition-specific reporting terms apply; verify the official brief.'
        cutoff=datetime.strptime('16 September 2026 11:00','%d %B %Y %H:%M').replace(tzinfo=ZoneInfo('Europe/London')).astimezone(timezone.utc)
        deadline={'kind':'fixed','at':cutoff.isoformat().replace('+00:00','Z')}
        status='open' if cutoff > datetime.fromisoformat(checked_at.replace('Z','+00:00')) else 'closed'
    else:
        parser=Text(); parser.feed(raw.decode('utf-8'))
        text=' '.join(' '.join(parser.parts).split())
        if 'Chevening in Thailand' not in text:
            raise ValueError('Chevening source drift or challenge page')
        title='Chevening in Thailand'
        countries=['TH']
        terms['study_level']='postgraduate'
        eligibility='Thailand program; nationality alone does not establish eligibility. Verify all Chevening requirements.'
        match=re.search(r'Open for applications until (\d{1,2} [A-Za-z]+ \d{4}), at (\d{2}:\d{2}) \(UTC\)',text)
        if match:
            cutoff=datetime.strptime(match[1]+' '+match[2],'%d %B %Y %H:%M').replace(tzinfo=timezone.utc)
            deadline={'kind':'fixed','at':cutoff.isoformat().replace('+00:00','Z')}
            status='open' if cutoff > datetime.fromisoformat(checked_at.replace('Z','+00:00')) else 'closed'
        elif re.search(r'Applications (?:are |have )?closed',text,re.I): status='closed'
    record_id=source['id']+(':'+deadline['at'][:10] if deadline['kind']=='fixed' else '')
    value_kind='access' if source['domain']=='freebie' else ('cash' if source['id'] in {'depa-digital-startup-fund','iuk-zevi2-alternative-fuels'} else 'unknown')
    value_currency='GBP' if source['id']=='iuk-zevi2-alternative-fuels' else None
    item={'id':record_id,'title':title,'record_kind':source['record_kind'],'category':source['category'],'source_url':source['source_url'],'provider':source['provider'],'status':status,'deadline':deadline,'eligible_countries':countries,'eligibility_text':eligibility,'value':{'kind':value_kind,'amount':None,'currency':value_currency,'guaranteed':False if source['id']=='iuk-zevi2-alternative-fuels' else None},'cost':{'fee_amount':None,'currency':None,'auto_renewal':None,'notes':'Not extracted; review official terms before applying or claiming.'},'terms':terms,'related_records':[],'provenance':{'evidence_kind':'captured','source_id':source['id'],'source_record_id':record_id,'checked_at':checked_at,'raw_object_key':None,'bronze_manifest_key':None}}
    return {'schema_version':source['schema_version'],'source':source['product'],'retrieved_at':checked_at,'data_status':'live','items':[item]}


def source_config(source_id=None):
    if source_id is None:
        return resource('source.json')
    if not re.fullmatch(r'[a-z0-9-]+', source_id):
        raise ValueError('invalid source id')
    base = resource('source.json')
    if base['id'] == source_id:
        return base
    try:
        return resource('source-' + source_id + '.json')
    except FileNotFoundError:
        raise ValueError('unknown source id') from None


def main(argv=None):
    selector = argparse.ArgumentParser(add_help=False)
    selector.add_argument('--source-id')
    selected, remaining = selector.parse_known_args(argv)
    root=os.environ.get('SOLO_EMPIRE_ROOT')
    if not root:
        print('Set SOLO_EMPIRE_ROOT to the local shared capture/lake runtime.',file=sys.stderr)
        return 2
    runtime=Path(root).resolve()/'infra/scripts'
    if not (runtime/'discovery/capture_runtime.py').is_file():
        print('Shared discovery runtime is unavailable.',file=sys.stderr)
        return 2
    sys.path.insert(0,str(runtime))
    from discovery.capture_runtime import run, VERSION
    if VERSION != 1: raise RuntimeError('unsupported shared capture runtime')
    return run(source_config(selected.source_id),normalize,validate,remaining)


if __name__=='__main__': raise SystemExit(main())
