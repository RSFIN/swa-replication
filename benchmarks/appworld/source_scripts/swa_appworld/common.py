from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
import json, re, hashlib

@dataclass(frozen=True)
class CompilerRuntime:
    task_id: str
    instruction: str
    apis: Any
    now: Any


def paginate(fn: Callable, *, access_token: str | None = None, max_pages: int = 100, **kwargs):
    rows=[]
    for page_index in range(max_pages):
        call=dict(kwargs)
        call['page_index']=page_index
        call['page_limit']=20
        if access_token is not None:
            call['access_token']=access_token
        page=fn(**call)
        if not page:
            break
        rows.extend(page)
        if len(page)<20:
            break
    return rows


def auth_profile(apis):
    profile=apis.supervisor.show_profile()
    passwords={x['account_name']:x['password'] for x in apis.supervisor.show_account_passwords()}
    return profile,passwords


def spotify_token(apis):
    p,pw=auth_profile(apis)
    return apis.spotify.login(username=p['email'],password=pw['spotify'])['access_token']


def venmo_token(apis):
    p,pw=auth_profile(apis)
    return apis.venmo.login(username=p['email'],password=pw['venmo'])['access_token']


def phone_token(apis):
    p,pw=auth_profile(apis)
    return apis.phone.login(username=p['phone_number'],password=pw['phone'])['access_token']


def supervisor_email(apis):
    return apis.supervisor.show_profile()['email']


def stable_json(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'))


def sha256_obj(obj):
    return hashlib.sha256(stable_json(obj).encode('utf-8')).hexdigest()


def pick(d,*keys):
    return {k:d.get(k) for k in keys if k in d}


def family_id(task_id):
    return task_id.rsplit('_',1)[0]


def parse_final_answer(text: str):
    m=re.search(r'(?im)^FINAL_ANSWER\s*:\s*(.*)$',text or '')
    return m.group(1).strip() if m else None
