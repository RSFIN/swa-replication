from __future__ import annotations
import re
import pendulum
from .base import BaseAdapter
from swa_appworld.common import *
from swa_appworld.row_table import encode_feed

class Adapter(BaseAdapter):
    scenario_id='383cbac'

    def _params(self,rt):
        m_share=re.search(r"My share was \$([0-9]+(?:\.[0-9]+)?)",rt.instruction,re.I)
        m_rest=re.search(r"yesterday at (.*?)\. My manager",rt.instruction,re.I)
        if not (m_share and m_rest): raise ValueError('Cannot parse restaurant/share')
        return m_rest.group(1).strip(),float(m_share.group(1))

    def collect_source(self,rt):
        pt=phone_token(rt.apis); vt=venmo_token(rt.apis)
        contacts=paginate(rt.apis.phone.search_contacts,access_token=pt)
        feed=paginate(rt.apis.venmo.show_social_feed,access_token=vt)
        contacts=sorted([pick(x,'contact_id','first_name','last_name','email','relationships') for x in contacts],key=lambda x:x['contact_id'])
        feed=sorted([pick(x,'transaction_id','amount','description','created_at','like_count','sender','receiver') for x in feed],key=lambda x:x['transaction_id'])
        return {'contacts':contacts,'social_feed':feed}

    def _resolved(self,s):
        coworkers=[x for x in s['contacts'] if 'coworker' in (x.get('relationships') or [])]
        managers=[x for x in s['contacts'] if 'manager' in (x.get('relationships') or [])]
        if len(managers)!=1: raise ValueError(f'Expected one manager, got {len(managers)}')
        return coworkers,managers[0]

    def _relevant_feed(self,rt,s):
        restaurant,share=self._params(rt)
        coworkers,manager=self._resolved(s)
        cemails={x['email'] for x in coworkers if x['email']!=manager['email']}
        day_start=rt.now.subtract(days=1).start_of('day')
        day_end=rt.now.start_of('day')
        rows=[]
        for x in s['social_feed']:
            dt=pendulum.parse(x['created_at'])
            if not (day_start <= dt < day_end): continue
            if x['sender']['email'] not in cemails: continue
            if x['receiver']['email'] != manager['email']: continue
            if restaurant.lower() not in x['description'].lower(): continue
            rows.append(x)
        return coworkers,manager,rows,share,restaurant

    def build_b0(self,rt,s):
        return {'source_interfaces':['phone.search_contacts','venmo.show_social_feed'],'primitive_contacts':s['contacts'],'primitive_social_feed_table':encode_feed(s['social_feed'])}
    def build_b1(self,rt,s):
        coworkers,manager,rows,share,restaurant=self._relevant_feed(rt,s)
        return {'resolved_manager':pick(manager,'contact_id','first_name','last_name','email'),
                'resolved_coworkers':[pick(x,'contact_id','first_name','last_name','email') for x in coworkers if x['email']!=manager['email']],
                'task_restaurant':restaurant,'task_user_share':share,
                'task_relevant_primitive_feed_records':rows}
    def build_b2(self,rt,s):
        coworkers,manager,rows,share,restaurant=self._relevant_feed(rt,s)
        evidence=[]
        for tx in sorted(rows,key=lambda x:(x['sender']['email'],x['transaction_id'])):
            evidence.append({'evidence_id':f"venmo:transaction:{tx['transaction_id']}",'coworker_email':tx['sender']['email'],'amount':tx['amount']})
        evidence.append({'evidence_id':'task:user_share','role':'user_share','amount':share})
        return {'manager_email':manager['email'],'payment_evidence_items':evidence}
    def oracle_answer(self,rt,s):
        *_,rows,share,_=self._relevant_feed(rt,s)
        return share+sum(x['amount'] for x in rows)
    def evidence_ids(self,rt,s):
        *_,rows,share,_=self._relevant_feed(rt,s)
        return [f"venmo:transaction:{x['transaction_id']}" for x in rows]+['task:user_share']
