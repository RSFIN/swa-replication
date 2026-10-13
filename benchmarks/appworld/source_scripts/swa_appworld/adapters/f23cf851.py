from __future__ import annotations
import re
import pendulum
from .base import BaseAdapter
from swa_appworld.common import *

class Adapter(BaseAdapter):
    scenario_id='23cf851'

    def _params(self,rt):
        t=rt.instruction.lower()
        if 'sent or received' in t: direction=None
        elif ' received ' in ' '+t+' ': direction='received'
        elif ' sent ' in ' '+t+' ': direction='sent'
        else: raise ValueError('Cannot parse Venmo direction')
        if 'this month' in t:
            threshold=rt.now.start_of('month')
        elif 'this year' in t:
            threshold=rt.now.start_of('year')
        else: raise ValueError('Cannot parse time period')
        return direction,threshold

    def collect_source(self,rt):
        token=venmo_token(rt.apis)
        rows=paginate(rt.apis.venmo.show_transactions,access_token=token)
        me=supervisor_email(rt.apis)
        rows=sorted(rows,key=lambda x:x['transaction_id'])
        return {'me':me,'transactions':[pick(x,'transaction_id','amount','description','created_at','like_count','sender','receiver') for x in rows]}

    def _relevant(self,rt,s):
        direction,threshold=self._params(rt)
        out=[]
        for x in s['transactions']:
            dt=pendulum.parse(x['created_at'])
            if dt < threshold: continue
            if direction=='sent' and x['sender']['email']!=s['me']: continue
            if direction=='received' and x['receiver']['email']!=s['me']: continue
            out.append(x)
        return out

    def build_b0(self,rt,s):
        return {'source_interface':'venmo.show_transactions','primitive_transactions':s['transactions']}
    def build_b1(self,rt,s):
        return {'resolved_user_email':s['me'],'task_relevant_primitive_transactions':self._relevant(rt,s)}
    def build_b2(self,rt,s):
        return {'evidence_items':[{'transaction_id':x['transaction_id'],'like_count':x['like_count']} for x in self._relevant(rt,s)]}
    def oracle_answer(self,rt,s): return sum(x['like_count'] for x in self._relevant(rt,s))
    def evidence_ids(self,rt,s): return [f"venmo:transaction:{x['transaction_id']}" for x in self._relevant(rt,s)]
