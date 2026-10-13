from __future__ import annotations
import json
from swa_appworld.row_table import EXPLANATION

SYSTEM="You are solving a frozen AppWorld decision task from provided text context only. Do not use tools or external knowledge. Use only the task instruction and supplied context. Return the required externally auditable fields; do not provide hidden chain-of-thought."

CONTRACT="Return exactly three lines:\nEVIDENCE_IDS: <JSON array of stable evidence IDs you used>\nCOMPUTATION: <brief externally verifiable aggregation/ranking statement>\nFINAL_ANSWER: <native AppWorld answer format>"

def render_context(obj):
    if 'primitive_social_feed_table' not in obj:
        return json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)
    table=obj['primitive_social_feed_table']
    base={k:v for k,v in obj.items() if k!='primitive_social_feed_table'}
    schema={k:v for k,v in table.items() if k!='tsv'}
    schema['tsv_chars']=len(table['tsv'])
    schema['decoding']=EXPLANATION
    return (json.dumps(base,ensure_ascii=False,sort_keys=True,separators=(',',':'))
            +'\nSOCIAL_FEED_TABLE_SCHEMA:\n'+json.dumps(schema,ensure_ascii=False,sort_keys=True)
            +'\nSOCIAL_FEED_TSV:\n'+table['tsv'])


def parse_rendered_context(text):
    decoder=json.JSONDecoder()
    obj,end=decoder.raw_decode(text)
    tail=text[end:]
    if not tail: return obj
    marker='\nSOCIAL_FEED_TABLE_SCHEMA:\n'
    if not tail.startswith(marker): raise ValueError('Unexpected context suffix')
    schema,end=decoder.raw_decode(tail[len(marker):])
    remainder=tail[len(marker)+end:]
    marker='\nSOCIAL_FEED_TSV:\n'
    if not remainder.startswith(marker): raise ValueError('Missing TSV block')
    tsv=remainder[len(marker):]
    if len(tsv)!=schema.pop('tsv_chars'): raise ValueError('TSV length mismatch')
    schema.pop('decoding')
    obj['primitive_social_feed_table']={**schema,'tsv':tsv}
    return obj


def parse_prompt(text):
    header,rest=text.split('\n\nTASK INSTRUCTION:\n',1)
    instruction,rest=rest.split('\n\nFROZEN CONTEXT:\n',1)
    body,contract=rest.rsplit('\n\nOUTPUT CONTRACT:\n',1)
    if contract != CONTRACT+'\n': raise ValueError('Output contract mismatch')
    lines=header.splitlines()
    return {'task_id':lines[0].removeprefix('TASK_ID: '),
            'condition':lines[1].removeprefix('SCB_CONDITION: '),
            'instruction':instruction,'context':parse_rendered_context(body)}


def render(task_id,instruction,condition,obj):
    return (f"TASK_ID: {task_id}\nSCB_CONDITION: {condition}\n\nTASK INSTRUCTION:\n{instruction}\n\n"
            f"FROZEN CONTEXT:\n{render_context(obj)}\n\n"
            f"OUTPUT CONTRACT:\n{CONTRACT}\n")
