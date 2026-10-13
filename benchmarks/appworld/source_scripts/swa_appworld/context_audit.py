"""Independent, context-only reference decisions and semantic treatment checks.

This module never receives a runtime, API object, original source, or native answer.
It is used only in the separate audit/scoring layer, never by treatment builders.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
import pendulum
from swa_appworld.row_table import decode_feed


def _body(context):
    return {k: v for k, v in context.items() if k != 'task_metadata'}


def _now(context):
    return pendulum.parse(context['task_metadata']['current_datetime'])


def _top_params(instruction):
    match = re.search(r'top\s+(\d+)\s+most played\s+(.+?)\s+song titles', instruction, re.I)
    if not match: raise ValueError('Unrecognized ranking instruction')
    return int(match.group(1)), match.group(2).strip()


def _meal_params(instruction):
    restaurant = re.search(r'yesterday at (.*?)\. My manager', instruction, re.I)
    share = re.search(r'My share was \$([0-9]+(?:\.[0-9]+)?)', instruction, re.I)
    if not restaurant or not share: raise ValueError('Unrecognized payment instruction')
    return restaurant.group(1), float(share.group(1))


def _like_rows(instruction, context):
    text = instruction.lower()
    now = _now(context)
    if 'this month' in text: cutoff = now.start_of('month')
    elif 'this year' in text: cutoff = now.start_of('year')
    else: raise ValueError('Unrecognized time window')
    me = context['task_metadata']['user_email']
    direction = None if 'sent or received' in text else ('sender' if ' sent ' in text else 'receiver')
    return [row for row in context['primitive_transactions']
            if pendulum.parse(row['created_at']) >= cutoff and (direction is None or row[direction]['email'] == me)]


def _payment_rows(instruction, context):
    contacts = context['primitive_contacts']
    managers = [c for c in contacts if 'manager' in c['relationships']]
    if len(managers) != 1: raise ValueError('Ambiguous manager')
    manager = managers[0]
    coworkers = [c for c in contacts if 'coworker' in c['relationships'] and c['email'] != manager['email']]
    emails = {c['email'] for c in coworkers}
    feed = decode_feed(context['primitive_social_feed_table'])
    restaurant, share = _meal_params(instruction)
    end = _now(context).start_of('day'); start = end.subtract(days=1)
    rows = [row for row in feed if start <= pendulum.parse(row['created_at']) < end
            and row['sender']['email'] in emails and row['receiver']['email'] == manager['email']
            and restaurant.lower() in row['description'].lower()]
    return manager, coworkers, rows, restaurant, share


def _memberships(context):
    edges = [{'source_type': 'song_library', 'source_id': 'direct', 'song_id': row['song_id']} for row in context['song_library']]
    for kind, key, id_key in [('album', 'album_library', 'album_id'), ('playlist', 'playlist_library', 'playlist_id')]:
        for row in context[key]:
            edges.extend({'source_type': kind, 'source_id': row[id_key], 'song_id': sid} for sid in row['song_ids'])
    return sorted(edges, key=lambda e: (e['source_type'], str(e['source_id']), e['song_id']))


def _year_records(instruction, context):
    text = instruction.lower(); now = _now(context)
    if 'this or last year' in text: threshold = now.subtract(years=1).start_of('year'); before = False
    elif 'before this year' in text: threshold = now.start_of('year'); before = True
    elif 'this year' in text: threshold = now.start_of('year'); before = False
    else: raise ValueError('Unrecognized release-year instruction')
    def passing(row):
        date = pendulum.parse(row['release_date'])
        return date < threshold if before else date >= threshold
    return ([r for r in context['direct_song_library'] if passing(r)],
            [r for r in context['album_library'] if passing(r)])


def _song_ids(direct, albums):
    ids = {row['song_id'] for row in direct}
    for row in albums: ids.update(row['song_ids'])
    return sorted(ids)


def _rank_records(instruction, context, condition):
    n, genre = _top_params(instruction)
    if condition == 'B2': return n, genre, context['unique_song_evidence']
    if condition == 'B0': details = context['primitive_song_details']; edges = context['primitive_source_memberships']
    elif condition == 'B1': details = context['candidate_song_details']; edges = context['candidate_occurrences_with_source_provenance']
    else: raise ValueError('Unknown condition')
    member_ids = {edge['song_id'] for edge in edges}
    records = {r['song_id']: r for r in details if r['song_id'] in member_ids and r['genre'].lower() == genre.lower()}
    return n, genre, [records[k] for k in sorted(records)]


def oracle_from_context(family, condition, instruction, context):
    if condition not in {'B0', 'B1', 'B2'}: raise ValueError('Unknown condition')
    if family == '23cf851':
        if condition == 'B0': rows = _like_rows(instruction, context)
        elif condition == 'B1': rows = context['task_relevant_primitive_transactions']
        else: rows = context['evidence_items']
        return sum(r['like_count'] for r in rows)
    if family == '383cbac':
        if condition == 'B0':
            _, _, rows, _, share = _payment_rows(instruction, context)
            return share + sum(r['amount'] for r in rows)
        if condition == 'B1':
            return context['task_user_share'] + sum(r['amount'] for r in context['task_relevant_primitive_feed_records'])
        return sum(r['amount'] for r in context['payment_evidence_items'])
    if family == 'fac291d':
        if condition == 'B0': ids = [r['song_id'] for r in _memberships(context)]
        elif condition == 'B1': ids = [r['song_id'] for r in context['resolved_source_membership_edges']]
        else: ids = context['unique_song_evidence_ids']
        return len(set(ids))
    if family == '4ec8de5':
        if condition == 'B0': direct, albums = _year_records(instruction, context)
        elif condition == 'B1': direct, albums = context['qualifying_direct_song_records'], context['qualifying_album_records']
        else: return len(set(context['unique_qualifying_song_evidence_ids']))
        return len(_song_ids(direct, albums))
    if family == '50e1ac9':
        n, _, records = _rank_records(instruction, context, condition)
        ranked = sorted(records, key=lambda r: (-r['play_count'], r['song_id']))
        return ', '.join(r['title'] for r in ranked[:n])
    raise ValueError('Unknown family')


def _expected_treatments(family, instruction, b0):
    if family == '23cf851':
        rows = _like_rows(instruction, b0)
        b1 = {'resolved_user_email': b0['task_metadata']['user_email'], 'task_relevant_primitive_transactions': rows}
        b2 = {'evidence_items': [{'transaction_id': r['transaction_id'], 'like_count': r['like_count']} for r in rows]}
    elif family == '383cbac':
        manager, coworkers, rows, restaurant, share = _payment_rows(instruction, b0)
        keys = ['contact_id', 'first_name', 'last_name', 'email']
        project = lambda row: {k: row[k] for k in keys}
        b1 = {'resolved_manager': project(manager), 'resolved_coworkers': [project(c) for c in coworkers],
              'task_restaurant': restaurant, 'task_user_share': share, 'task_relevant_primitive_feed_records': rows}
        evidence = [{'evidence_id': f"venmo:transaction:{r['transaction_id']}", 'coworker_email': r['sender']['email'], 'amount': r['amount']}
                    for r in sorted(rows, key=lambda r: (r['sender']['email'], r['transaction_id']))]
        evidence.append({'evidence_id': 'task:user_share', 'role': 'user_share', 'amount': share})
        b2 = {'manager_email': manager['email'], 'payment_evidence_items': evidence}
    elif family == 'fac291d':
        edges = _memberships(b0)
        b1 = {'resolved_source_membership_edges': edges}
        b2 = {'unique_song_evidence_ids': sorted({r['song_id'] for r in edges})}
    elif family == '4ec8de5':
        direct, albums = _year_records(instruction, b0)
        b1 = {'qualifying_direct_song_records': direct, 'qualifying_album_records': albums}
        b2 = {'unique_qualifying_song_evidence_ids': _song_ids(direct, albums)}
    elif family == '50e1ac9':
        n, genre, records = _rank_records(instruction, b0, 'B0')
        ids = {r['song_id'] for r in records}
        occurrences = [e for e in b0['primitive_source_memberships'] if e['song_id'] in ids]
        b1 = {'target_genre': genre, 'candidate_occurrences_with_source_provenance': occurrences, 'candidate_song_details': records}
        b2 = {'target_genre': genre, 'top_n_requested': n,
              'unique_song_evidence': [{k: r[k] for k in ['song_id', 'title', 'play_count']} for r in records]}
    else: raise ValueError('Unknown family')
    return b1, b2


def semantic_boundary(family, instruction, b0, b1, b2):
    expected_b1, expected_b2 = _expected_treatments(family, instruction, b0)
    checks = {
        'b1_schema_and_complete_task_records': _body(b1) == expected_b1,
        'b2_exact_schema_without_aggregates': set(_body(b2)) == set(expected_b2),
        'b2_complete_primitive_evidence_in_prescribed_order': _body(b2) == expected_b2,
        'common_public_metadata_equal': b0['task_metadata'] == b1['task_metadata'] == b2['task_metadata'],
    }
    if family == '50e1ac9':
        n, _, records = _rank_records(instruction, b0, 'B0')
        counts = sorted([r['play_count'] for r in records], reverse=True)
        checks['no_cutoff_tie'] = len(counts) <= n or counts[n-1] != counts[n]
    return {'pass': all(checks.values()), 'checks': checks}


def evidence_ids_from_context(family, instruction, b0):
    _, evidence = _expected_treatments(family, instruction, b0)
    if family == '23cf851': return [f"venmo:transaction:{r['transaction_id']}" for r in evidence['evidence_items']]
    if family == '383cbac': return [r['evidence_id'] for r in evidence['payment_evidence_items']]
    if family == 'fac291d': ids = evidence['unique_song_evidence_ids']
    elif family == '4ec8de5': ids = evidence['unique_qualifying_song_evidence_ids']
    else: ids = [r['song_id'] for r in evidence['unique_song_evidence']]
    return [f'spotify:song:{sid}' for sid in ids]
