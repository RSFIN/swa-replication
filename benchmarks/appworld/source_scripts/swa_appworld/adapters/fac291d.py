from __future__ import annotations
from .base import BaseAdapter
from swa_appworld.common import *

class Adapter(BaseAdapter):
    scenario_id='fac291d'
    def collect_source(self,rt):
        tok=spotify_token(rt.apis)
        songs=paginate(rt.apis.spotify.show_song_library,access_token=tok)
        albums=paginate(rt.apis.spotify.show_album_library,access_token=tok)
        playlists=paginate(rt.apis.spotify.show_playlist_library,access_token=tok)
        return {
          'song_library':sorted([{'song_id':x['song_id']} for x in songs],key=lambda x:x['song_id']),
          'album_library':sorted([{'album_id':x['album_id'],'song_ids':list(x.get('song_ids',[]))} for x in albums],key=lambda x:x['album_id']),
          'playlist_library':sorted([{'playlist_id':x['playlist_id'],'song_ids':list(x.get('song_ids',[]))} for x in playlists],key=lambda x:x['playlist_id'])}
    def _edges(self,s):
        e=[]
        for x in s['song_library']: e.append({'source_type':'song_library','source_id':'direct','song_id':x['song_id']})
        for a in s['album_library']:
            for sid in a['song_ids']: e.append({'source_type':'album','source_id':a['album_id'],'song_id':sid})
        for p in s['playlist_library']:
            for sid in p['song_ids']: e.append({'source_type':'playlist','source_id':p['playlist_id'],'song_id':sid})
        return sorted(e,key=lambda x:(x['source_type'],str(x['source_id']),x['song_id']))
    def build_b0(self,rt,s): return {'source_interfaces':['spotify.show_song_library','spotify.show_album_library','spotify.show_playlist_library'],**s}
    def build_b1(self,rt,s): return {'resolved_source_membership_edges':self._edges(s)}
    def build_b2(self,rt,s): return {'unique_song_evidence_ids':sorted({x['song_id'] for x in self._edges(s)})}
    def oracle_answer(self,rt,s): return len({x['song_id'] for x in self._edges(s)})
    def evidence_ids(self,rt,s): return [f"spotify:song:{x}" for x in sorted({e['song_id'] for e in self._edges(s)})]
