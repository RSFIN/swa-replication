"""Natural lossless TSV serialization for the 383cbac B0 source envelope.

This module performs serialization only. It does not filter rows, intern participants,
canonicalize entities, deduplicate records, or apply any task-dependent transformation.
"""
from __future__ import annotations
import csv
import io
import json

COLUMNS = ['transaction_id', 'amount', 'description', 'created_at', 'like_count',
           'sender.email', 'sender.name', 'receiver.email', 'receiver.name']
TYPES = ['int', 'float', 'str', 'str', 'int', 'str', 'str', 'str', 'str']
EXPLANATION = (
    'Plain TSV rows preserve every source record in transaction-ID order, including duplicates. '
    'Standard CSV double-quote escaping is used with TAB separators. Each row is read directly '
    'using the declared columns and types. There is no custom decompression, participant '
    'dictionary, entity interning, deduplication, canonicalization, or target-dependent filtering.'
)

def _values(record):
    if set(record) != {'transaction_id', 'amount', 'description', 'created_at', 'like_count', 'sender', 'receiver'}:
        raise ValueError('Unexpected transaction schema; refusing lossy projection')
    if any(set(record[role]) != {'email', 'name'} for role in ['sender', 'receiver']):
        raise ValueError('Unexpected participant schema; refusing lossy projection')
    return [record['transaction_id'], record['amount'], record['description'], record['created_at'],
            record['like_count'], record['sender']['email'], record['sender']['name'],
            record['receiver']['email'], record['receiver']['name']]

def encode_feed(rows):
    output = io.StringIO(newline='')
    writer = csv.writer(output, delimiter='\t', lineterminator='\n')
    for record in rows:
        values = _values(record)
        # Validate numeric fields without changing their semantics.
        for value, kind in zip(values, TYPES):
            if kind == 'int' and (isinstance(value, bool) or not isinstance(value, int)):
                raise ValueError('Expected integer cell')
            if kind == 'float' and (isinstance(value, bool) or not isinstance(value, (int, float))):
                raise ValueError('Expected numeric amount')
            if kind == 'str' and not isinstance(value, str):
                raise ValueError('Expected string cell')
        writer.writerow(values)
    return {'encoding': 'tsv-plain-v1', 'columns': COLUMNS, 'column_types': TYPES, 'tsv': output.getvalue()}

def decode_feed(table):
    if table['encoding'] != 'tsv-plain-v1' or table['columns'] != COLUMNS or table['column_types'] != TYPES:
        raise ValueError('Unsupported row-table schema')
    output = []
    for row in csv.reader(io.StringIO(table['tsv'], newline=''), delimiter='\t', strict=True):
        if len(row) != len(COLUMNS):
            raise ValueError('Wrong TSV column count')
        values=[]
        for cell,kind in zip(row,TYPES):
            if kind == 'str':
                value=cell
            elif kind == 'int':
                value=json.loads(cell)
                if isinstance(value,bool) or not isinstance(value,int): raise ValueError('Expected integer')
            else:
                value=json.loads(cell)
                if isinstance(value,bool) or not isinstance(value,(int,float)): raise ValueError('Expected amount')
            values.append(value)
        output.append({'transaction_id': values[0], 'amount': values[1], 'description': values[2],
                       'created_at': values[3], 'like_count': values[4],
                       'sender': {'email': values[5], 'name': values[6]},
                       'receiver': {'email': values[7], 'name': values[8]}})
    return output
