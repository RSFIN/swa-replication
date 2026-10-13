from __future__ import annotations
import pendulum
from .base import BaseAdapter
from swa_appworld.common import *

class Adapter(BaseAdapter):
    scenario_id='4ec8de5'
    def _predicate(self,rt):
        t=rt.instruction.lower()
        start_this=rt.now.start_of('year')
        if 'this or last year' in t:
            th=rt.now.subtract(years=1).start_of('year'); return ('ge',th)
        if 'before this year' in t: return ('lt',start_this)
        if 'this year' in t: return ('ge',start_this)
        raise ValueError('Cannot parse year predicate')
    def collect_source(self,rt):
        tok=spotify_token(rt.apis)
        libs=paginate(rt.apis.spotify.show_song_library,access_token=tok)
        albums=paginate(rt.apis.spotify.show_album_library,access_token=tok)
        direct=[]
        for x in libs:
            d=rt.apis.spotify.show_song(song_id=x['song_id'])
            direct.append(pick(d,'song_id','title','release_date'))
        return {'direct_song_library':sorted(direct,key=lambda x:x['song_id']),
                'album_library':sorted([pick(x,'album_id','title','release_date','song_ids') for x in albums],key=lambda x:x['album_id'])}
    def _pass(self,dt,op,th):
        d=pendulum.parse(dt); return d>=th if op=='ge' else d<th
    def _qual(self,rt,s):
        op,th=self._predicate(rt)
        ds=[x for x in s['direct_song_library'] if self._pass(x['release_date'],op,th)]
        al=[x for x in s['album_library'] if self._pass(x['release_date'],op,th)]
        return ds,al
    def build_b0(self,rt,s): return {'source_interfaces':['spotify.show_song_library+show_song','spotify.show_album_library'],**s}
    def build_b1(self,rt,s):
        ds,al=self._qual(rt,s)
        return {'qualifying_direct_song_records':ds,'qualifying_album_records':al}
    def build_b2(self,rt,s):
        ds,al=self._qual(rt,s)
        ids={x['song_id'] for x in ds}
        for a in al: ids.update(a.get('song_ids',[]))
        return {'unique_qualifying_song_evidence_ids':sorted(ids)}
    def oracle_answer(self,rt,s): return len(self.build_b2(rt,s)['unique_qualifying_song_evidence_ids'])
    def evidence_ids(self,rt,s): return [f"spotify:song:{x}" for x in self.build_b2(rt,s)['unique_qualifying_song_evidence_ids']]
