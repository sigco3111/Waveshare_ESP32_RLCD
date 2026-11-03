# Syna project-specific code and modifications: Copyright (c) 2026 Heimu.
# SPDX-License-Identifier: MIT; third-party notices remain applicable.
import unittest
import os
import psutil
import asyncio
import threading

from media_monitor import lyric_at, parse_lrc, NeteaseLocalState
from media_monitor import DESKTOP_LYRICS_TITLE, NETEASE_APP_TITLE
from media_monitor import NeteaseMediaMonitor
from media_monitor import NeteaseLyricsResolver, _title_candidates
from macos_media import MacNeteaseTimeline
from unittest.mock import patch, Mock


class AsyncMetadataTests(unittest.IsolatedAsyncioTestCase):
    def monitor(self, duration=200):
        monitor = NeteaseMediaMonitor()
        monitor._mac = None
        monitor._cdp = Mock()
        monitor._cdp.read.return_value = None
        monitor._local = Mock()
        monitor._local.read.return_value = dict(title="Old", artist="Artist", song_id=1,
            playback_status="playing", position=0, duration=duration)
        return monitor

    async def test_slow_lyrics_do_not_block_switch_pause_or_leak_old_song(self):
        monitor = self.monitor()
        release = threading.Event()
        def resolve(title, artist, song):
            release.wait(3)
            return song, [(0, title + " lyric")]
        monitor._resolver.resolve = resolve
        try:
            first = await asyncio.wait_for(monitor._read(None), 0.5)
            self.assertEqual((first.title, first.playback_status, first.song_id), ("Old", "playing", 1))
            monitor._local.read.return_value.update(title="New", song_id=2, playback_status="paused", position=42)
            new = await asyncio.wait_for(monitor._read(None), 0.5)
            self.assertEqual((new.title, new.playback_status, new.position_seconds, new.song_id), ("New", "paused", 42, 2))
            self.assertEqual(new.lyric, "No lyrics")
            release.set()
            await monitor._lyrics_task
            new = await monitor._read(None)
            self.assertNotEqual(new.lyric, "Old lyric")
            await monitor._lyrics_task
            self.assertEqual((await monitor._read(None)).lyric, "New lyric")
        finally:
            release.set()
            if monitor._lyrics_task is not None:
                await monitor._lyrics_task

    async def test_slow_duration_does_not_block_or_apply_to_different_song(self):
        monitor = self.monitor(duration=0)
        release = threading.Event()
        monitor._resolver.resolve = lambda title, artist, song: (song, [])
        def duration(song):
            release.wait(3)
            return 100 + song
        monitor._resolver.duration_seconds = duration
        try:
            first = await asyncio.wait_for(monitor._read(None), 0.5)
            self.assertEqual(first.duration_seconds, 0)
            monitor._local.read.return_value.update(title="New", song_id=2)
            new = await asyncio.wait_for(monitor._read(None), 0.5)
            self.assertEqual((new.title, new.duration_seconds), ("New", 0))
            release.set()
            await monitor._duration_task
            new = await monitor._read(None)
            self.assertEqual(new.duration_seconds, 0)
            await monitor._duration_task
            self.assertEqual((await monitor._read(None)).duration_seconds, 102)
        finally:
            release.set()
            for task in (monitor._lyrics_task, monitor._duration_task):
                if task is not None:
                    await task


@unittest.skipUnless(os.name == "nt", "Windows audio sessions")
class AudioSessionTests(unittest.TestCase):
    def test_stale_session_does_not_hide_playing_netease(self):
        stale = Mock()
        stale.Process.name.side_effect = psutil.NoSuchProcess(42)
        live = Mock()
        live.Process.name.return_value = "cloudmusic.exe"
        live.State = 1
        live._ctl.QueryInterface.return_value.GetPeakValue.return_value = 0.5
        with patch("media_monitor.comtypes.CoInitializeEx") as init, \
                patch("media_monitor.comtypes.CoUninitialize") as uninit, \
                patch("media_monitor.AudioUtilities.GetAllSessions", return_value=[stale, live]):
            self.assertEqual(NeteaseLocalState._audio_session_sample(), (True, 0.5))
        init.assert_called_once()
        uninit.assert_called_once()

    def test_com_is_released_when_enumeration_fails(self):
        with patch("media_monitor.comtypes.CoInitializeEx"), \
                patch("media_monitor.comtypes.CoUninitialize") as uninit, \
                patch("media_monitor.AudioUtilities.GetAllSessions", side_effect=OSError("device lost")):
            self.assertIsNone(NeteaseLocalState._audio_session_sample())
        uninit.assert_called_once()

    def test_existing_apartment_is_not_uninitialized(self):
        error = OSError("existing STA")
        error.hresult = -2147417850
        with patch("media_monitor.comtypes.CoInitializeEx", side_effect=error), \
                patch("media_monitor.comtypes.CoUninitialize") as uninit, \
                patch("media_monitor.AudioUtilities.GetAllSessions", return_value=[]):
            self.assertIsNone(NeteaseLocalState._audio_session_sample())
        uninit.assert_not_called()

    def test_play_pause_and_resume_follow_samples(self):
        local = NeteaseLocalState()
        with patch.object(local, "_audio_session_sample", side_effect=[(True, 0.5), (True, 0), (True, 0), (True, 0.5)]), \
                patch("media_monitor.time.monotonic", side_effect=[100, 100.4, 101, 102]):
            self.assertEqual([local._read_playback_status() for _ in range(4)],
                             ["playing", "playing", "paused", "playing"])


class WindowTitleTests(unittest.TestCase):
    def test_desktop_lyrics_does_not_replace_song_in_either_order(self):
        song = "Episode 33 - She Her Her Hers"
        for titles in ([DESKTOP_LYRICS_TITLE, song], [song, DESKTOP_LYRICS_TITLE]):
            self.assertEqual(NeteaseLocalState._select_window_title(titles), song)

    def test_auxiliary_windows_alone_are_not_tracks(self):
        self.assertEqual(NeteaseLocalState._select_window_title(
            [NETEASE_APP_TITLE, DESKTOP_LYRICS_TITLE, "Settings", "Desktop Lyrics"]), "")

    def test_known_track_takes_priority_over_other_window(self):
        self.assertEqual(NeteaseLocalState._select_window_title(
            ["Help - " + NETEASE_APP_TITLE, "Episode 33 - She Her Her Hers"],
            [{"name": "Episode 33"}]), "Episode 33 - She Her Her Hers")

    def test_known_title_without_artist_is_supported(self):
        self.assertEqual(NeteaseLocalState._select_window_title(
            [DESKTOP_LYRICS_TITLE, "Episode 33"], [{"name": "Episode 33"}]), "Episode 33")

    def test_read_refreshes_playlist_before_selecting_window(self):
        local = NeteaseLocalState()
        tracks = [{"name": "Episode 33", "id": 123, "duration": 258000}]
        def refresh():
            local._tracks = tracks
        with patch.object(local, "_refresh_tracks", side_effect=refresh), \
                patch.object(local, "_window_title", return_value="Episode 33") as title, \
                patch.object(local, "_read_playback_status", return_value="paused"), \
                patch.object(local, "_read_position_checkpoint", return_value=0):
            snapshot = local.read()
        title.assert_called_once_with(tracks)
        self.assertEqual(snapshot["title"], "Episode 33")


class LyricsTests(unittest.TestCase):
    def test_parse_and_select_current_line(self):
        lines = parse_lrc("[00:01.00]First line\n[00:03.500][00:05.00]Second line")
        self.assertEqual([(1.0, "First line"), (3.5, "Second line"), (5.0, "Second line")], lines)
        self.assertEqual("♪", lyric_at(lines, 0.5))
        self.assertEqual("First line", lyric_at(lines, 2.0))
        self.assertEqual("Second line", lyric_at(lines, 4.0))

    def test_empty_lyrics(self):
        self.assertEqual("No lyrics", lyric_at([], 10))


class BrowserTitleTests(unittest.TestCase):
    """Browser media titles carry prose around the real song name."""

    def test_quoted_song_name_is_preferred(self):
        title = "IU 'Love wins all' Live Clip (2024 TOUR CONCERT ENCORE : THE WINNING)"
        candidates = _title_candidates(title)
        self.assertEqual("Love wins all", candidates[0])

    def test_parens_and_brackets_are_stripped(self):
        title = "'모두 잠든 후에' [김원준] 시티팝 여자 커버"
        candidates = _title_candidates(title)
        self.assertEqual("모두 잠든 후에", candidates[0])
        self.assertNotIn("[", candidates[0])
        self.assertNotIn("(", candidates[0])

    def test_official_video_suffix_is_removed(self):
        title = "Some Song - Artist Official Video"
        self.assertIn("Some Song - Artist", _title_candidates(title))

    def test_plain_title_still_produces_candidate(self):
        self.assertEqual("Plain Song", _title_candidates("Plain Song")[0])

    def test_search_query_uses_song_name_without_artist(self):
        resolver = NeteaseLyricsResolver()
        song = {"id": 42, "name": "Love wins all", "artists": [{"name": "IU"}]}
        with patch.object(resolver, "_get_json", return_value={"result": {"songs": [song]}}) as get_json:
            found = resolver._search_song("IU 'Love wins all' Live Clip", "IU")
        self.assertEqual(42, found)
        body = get_json.call_args.args[1].decode("utf-8")
        self.assertIn("s=Love+wins+all", body)
        self.assertNotIn("IU", body)

    def test_search_falls_back_to_title_only_match(self):
        resolver = NeteaseLyricsResolver()
        song = {"id": 7, "name": "Cover Song", "artists": [{"name": "Other Artist"}]}
        with patch.object(resolver, "_get_json", return_value={"result": {"songs": [song]}}):
            found = resolver._search_song("Cover Song", "Reina&Mika")
        self.assertEqual(7, found)


class MacMediaTests(unittest.TestCase):
    def test_any_bundle_is_accepted(self):
        sample = {
            "bundle": "com.google.Chrome",
            "title": "IU 'Love wins all' Live Clip",
            "artist": "IU Official",
            "duration": 385.3,
            "rate": 1,
            "position": 139.9,
        }
        normalized = MacNeteaseTimeline.normalize(sample)
        self.assertIsNotNone(normalized)
        self.assertEqual("IU 'Love wins all' Live Clip", normalized["title"])
        self.assertEqual("playing", normalized["playback_status"])

    def test_netease_bundle_is_still_accepted(self):
        sample = {
            "bundle": "com.netease.163music",
            "title": "Love wins all",
            "artist": "IU",
            "duration": 200.0,
            "rate": 1,
            "position": 10.0,
        }
        self.assertIsNotNone(MacNeteaseTimeline.normalize(sample))

    def test_missing_title_is_rejected(self):
        self.assertIsNone(MacNeteaseTimeline.normalize({"bundle": "com.google.Chrome", "title": ""}))
        self.assertIsNone(MacNeteaseTimeline.normalize({}))


if __name__ == "__main__":
    unittest.main()
