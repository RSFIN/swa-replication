import requests,time,json

class ProviderError(RuntimeError): pass

def _usage_openai_chat(data):
    u=data.get('usage') or {}; det=u.get('completion_tokens_details') or {}
    pdet=u.get('prompt_tokens_details') or {}
    return {'input_tokens':u.get('prompt_tokens'),'output_tokens':u.get('completion_tokens'),
            'reasoning_tokens':det.get('reasoning_tokens'),'cached_input_tokens':pdet.get('cached_tokens')}

def _usage_openai_responses(data):
    u=data.get('usage') or {}; det=u.get('output_tokens_details') or {}; idet=u.get('input_tokens_details') or {}
    return {'input_tokens':u.get('input_tokens'),'output_tokens':u.get('output_tokens'),
            'reasoning_tokens':det.get('reasoning_tokens'),'cached_input_tokens':idet.get('cached_tokens')}

def _usage_anthropic(data):
    u=data.get('usage') or {}
    cached=(u.get('cache_read_input_tokens') or 0)+(u.get('cache_creation_input_tokens') or 0)
    return {'input_tokens':u.get('input_tokens'),'output_tokens':u.get('output_tokens'),
            'reasoning_tokens':None,'cached_input_tokens':cached or None}

def _text_openai_responses(data):
    parts=[]
    if data.get('output_text'): return data['output_text']
    for item in data.get('output') or []:
        if item.get('type')=='message':
            for c in item.get('content') or []:
                if c.get('type') in ('output_text','text') and c.get('text'): parts.append(c['text'])
    return '\n'.join(parts)

def _text_anthropic(data):
    return '\n'.join(x.get('text','') for x in (data.get('content') or []) if x.get('type')=='text')

def build_request(cfg,system,user,call_id):
    system=f"EXPERIMENT_CALL_ID: {call_id}\n{system}"
    adapter=cfg['adapter']; maxout=cfg.get('max_output_tokens',16384); over=dict(cfg.get('request_overrides') or {})
    if adapter=='openai_responses':
        body={'model':cfg['model'],'input':[{'role':'system','content':system},{'role':'user','content':user}],
              'max_output_tokens':maxout}
        body.update(over); return body
    if adapter=='anthropic_messages':
        body={'model':cfg['model'],'system':system,'messages':[{'role':'user','content':user}],
              'max_tokens':maxout}
        body.update(over); return body
    if adapter=='openai_chat':
        body={'model':cfg['model'],'messages':[{'role':'system','content':system},{'role':'user','content':user}],
              'stream':False}
        body[cfg.get('max_token_field','max_tokens')]=maxout
        body.update(over); return body
    raise ProviderError('Unknown adapter '+adapter)

def call(cfg,api_key,body,timeout=1800):
    url=cfg['base_url'].rstrip('/')+'/'+cfg['endpoint'].lstrip('/')
    headers={'content-type':'application/json'}
    if cfg['adapter']=='anthropic_messages':
        headers.update({'x-api-key':api_key,'anthropic-version':'2023-06-01'})
    else: headers['authorization']='Bearer '+api_key
    t=time.perf_counter(); r=requests.post(url,headers=headers,json=body,timeout=timeout)
    ms=round((time.perf_counter()-t)*1000)
    try: data=r.json()
    except Exception: data={'raw_text':r.text}
    if r.status_code>=400: raise ProviderError(json.dumps({'status':r.status_code,'data':data},ensure_ascii=False)[:10000])
    if cfg['adapter']=='openai_responses':
        text=_text_openai_responses(data); usage=_usage_openai_responses(data)
        finish=data.get('status') or data.get('incomplete_details',{}).get('reason') or ''
    elif cfg['adapter']=='anthropic_messages':
        text=_text_anthropic(data); usage=_usage_anthropic(data); finish=data.get('stop_reason','')
    else:
        ch=(data.get('choices') or [{}])[0]; msg=ch.get('message') or {}; text=msg.get('content') or ''
        usage=_usage_openai_chat(data); finish=ch.get('finish_reason','')
    return {'raw':data,'text':text,'usage':usage,'finish_reason':finish,'latency_ms':ms,
            'response_model':data.get('model',''),'request_id':data.get('id','')}
