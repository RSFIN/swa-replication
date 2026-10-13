import re,json

def _line(text,key):
    m=re.search(r'^'+re.escape(key)+r':\s*(.*?)\s*$',text,re.M|re.I); return m.group(1).strip() if m else None

def _parse_obj(s):
    if s is None or s.upper()=='NOT_REACHED': return None
    try: return json.loads(s)
    except Exception: return None

def evaluate(text,oracle):
    final=_line(text,'FINAL_ANSWER')
    if not final:
        ids=re.findall(r'005Ws[0-9A-Za-z]+',text); final=ids[-1] if ids else None
    ti=_line(text,'TARGET_ISSUE'); tp=_line(text,'TARGET_PRODUCT')
    issue=_parse_obj(_line(text,'ISSUE_STAGE')); prod=_parse_obj(_line(text,'PRODUCT_STAGE')); work=_parse_obj(_line(text,'WORKLOAD_STAGE'))
    out={'predicted':final,'gold':oracle['gold'],'correct':int(final==oracle['gold']),
         'protocol_ok':int(_line(text,'FINAL_ANSWER') is not None),'target_issue_correct':None,'target_product_correct':None,
         'issue_stage_correct':None,'product_stage_correct':None,'workload_stage_correct':None,'auto_failure_class':''}
    if ti is not None: out['target_issue_correct']=int(oracle['target_issue_name'].lower() in ti.lower())
    if tp is not None: out['target_product_correct']=int(oracle['target_product_name'].lower() in tp.lower())
    def stage_ok(obj,gold,count_key):
        if gold is None: return int(obj is None)
        if obj is None: return 0
        try:
            cnt=int(obj[count_key]); fins=sorted(obj['finalists'])
            return int(cnt==int(gold[count_key]) and fins==sorted(gold['finalists']))
        except Exception: return 0
    out['issue_stage_correct']=stage_ok(issue,oracle['issue_stage'],'top_count')
    out['product_stage_correct']=stage_ok(prod,oracle['product_stage'],'top_count')
    out['workload_stage_correct']=stage_ok(work,oracle['workload_stage'],'min_count')
    if out['correct']: out['auto_failure_class']='E0'
    elif out['target_issue_correct']==0 or out['target_product_correct']==0: out['auto_failure_class']='E1_TARGET'
    elif out['issue_stage_correct']==0 or out['product_stage_correct']==0 or out['workload_stage_correct']==0: out['auto_failure_class']='E2_E3_EVIDENCE_OR_AGGREGATION'
    elif out['protocol_ok']==0: out['auto_failure_class']='E6_PROTOCOL'
    else: out['auto_failure_class']='E5_FINAL'
    return out
