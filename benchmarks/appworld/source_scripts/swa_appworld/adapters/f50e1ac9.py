from __future__ import annotations
import re
from .base import BaseAdapter
from swa_appworld.common import *

class Adapter(BaseAdapter):
    scenario_id='50e1ac9'
    def _params(self,rt):
        m=re.search(r'top\s+(\d+)\s+most played\s+(.+?)\s+song titles',rt.instruction,re.I)
        if not m: raise ValueError('Cannot parse top-N/genre')
        return int(m.group(1)),m.group(2).strip()
    def collect_source(self,rt):
        tok=spotify_token(rt.apis)
        songlib=paginate(rt.apis.spotify.show_song_library,access_token=tok)
        albumlib=paginate(rt.apis.spotify.show_album_library,access_token=tok)
        playlistlib=paginate(rt.apis.spotify.show_playlist_library,access_token=tok)
        occurrences=[]; details={}
        def add_song(sid,stype,sid_source):
            sid=int(sid)
            occurrences.append({'source_type':stype,'source_id':sid_source,'song_id':sid})
            if sid not in details:
                d=rt.apis.spotify.show_song(song_id=sid)
                details[sid]=pick(d,'song_id','title','genre','play_count')
        for x in songlib: add_song(x['song_id'],'song_library','direct')
        for x in albumlib:
            # library response already provides song_ids; details are resolved independently.
            for sid in x.get('song_ids',[]): add_song(sid,'album',x['album_id'])
        for x in playlistlib:
            # library response already provides song_ids.
            for sid in x.get('song_ids',[]): add_song(sid,'playlist',x['playlist_id'])
        return {'source_memberships':sorted(occurrences,key=lambda x:(x['source_type'],str(x['source_id']),x['song_id'])),
                'song_details':[details[k] for k in sorted(details)]}
    def _candidates(self,rt,s):
        n,genre=self._params(rt)
        d={x['song_id']:x for x in s['song_details'] if x.get('genre','').lower()==genre.lower()}
        occ=[x for x in s['source_memberships'] if x['song_id'] in d]
        return n,genre,d,occ
    def build_b0(self,rt,s): return {'source_interfaces':['spotify song/album/playlist libraries','spotify.show_song'],'primitive_source_memberships':s['source_memberships'],'primitive_song_details':s['song_details']}
    def build_b1(self,rt,s):
        n,genre,d,occ=self._candidates(rt,s)
        return {'target_genre':genre,'candidate_occurrences_with_source_provenance':occ,'candidate_song_details':[d[k] for k in sorted(d)]}
    def build_b2(self,rt,s):
        n,genre,d,occ=self._candidates(rt,s)
        # ID order is intentional: ranking remains decision execution.
        return {'target_genre':genre,'top_n_requested':n,'unique_song_evidence':[{'song_id':k,'title':d[k]['title'],'play_count':d[k]['play_count']} for k in sorted(d)]}
    def oracle_answer(self,rt,s):
        n,genre,d,occ=self._candidates(rt,s)
        # Stable tie handling based on song_id order; audit separately rejects cutoff ties.
        vals=[d[k] for k in sorted(d)]
        vals=sorted(vals,key=lambda x:x['play_count'],reverse=True)[:n]
        return ', '.join(x['title'] for x in vals)
    def evidence_ids(self,rt,s):
        n,genre,d,occ=self._candidates(rt,s)
        return [f"spotify:song:{k}" for k in sorted(d)]
    def cutoff_tie(self,rt,s):
        n,genre,d,occ=self._candidates(rt,s)
        vals=sorted([x['play_count'] for x in d.values()],reverse=True)
        return len(vals)>n and vals[n-1]==vals[n]
