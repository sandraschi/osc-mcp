"""Tests for ableton_manager, including the operations added to expose more
of AbletonOSC's real, documented address space (github.com/ideoforms/
AbletonOSC's own README) - scene firing, clip stopping, mute/solo, tap
tempo, and session record. All addresses verified against that README
before writing this test, not guessed.
"""

from unittest.mock import AsyncMock, patch

import pytest

from oscmcp.mcp_server import ableton_manager


@pytest.mark.asyncio
async def test_stop_all_clips_sends_real_address():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await ableton_manager("stop_all_clips")
    assert mock_send.await_args.args[2] == "/live/song/stop_all_clips"
    assert mock_send.await_args.args[3] == []


@pytest.mark.asyncio
async def test_tap_tempo_sends_real_address():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await ableton_manager("tap_tempo")
    assert mock_send.await_args.args[2] == "/live/song/tap_tempo"


@pytest.mark.asyncio
async def test_trigger_record_sends_real_session_record_address():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await ableton_manager("trigger_record")
    assert mock_send.await_args.args[2] == "/live/song/trigger_session_record"


@pytest.mark.asyncio
async def test_stop_clip_sends_track_and_slot():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await ableton_manager("stop_clip", track_index=2, clip_slot=1)
    assert mock_send.await_args.args[2] == "/live/clip/stop"
    assert mock_send.await_args.args[3] == [2, 1]


@pytest.mark.asyncio
async def test_stop_clip_requires_track_and_slot():
    result = await ableton_manager("stop_clip", track_index=None, clip_slot=None)
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_fire_scene_sends_scene_id():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await ableton_manager("fire_scene", scene_id=3)
    assert mock_send.await_args.args[2] == "/live/scene/fire"
    assert mock_send.await_args.args[3] == [3]


@pytest.mark.asyncio
async def test_fire_scene_requires_scene_id():
    result = await ableton_manager("fire_scene", scene_id=None)
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_set_mute_sends_binary_arg():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await ableton_manager("set_mute", track_index=0, mute=True)
    assert mock_send.await_args.args[2] == "/live/track/set/mute"
    assert mock_send.await_args.args[3] == [0, 1]

    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await ableton_manager("set_mute", track_index=0, mute=False)
    assert mock_send.await_args.args[3] == [0, 0]


@pytest.mark.asyncio
async def test_set_solo_sends_binary_arg():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await ableton_manager("set_solo", track_index=1, solo=True)
    assert mock_send.await_args.args[2] == "/live/track/set/solo"
    assert mock_send.await_args.args[3] == [1, 1]


@pytest.mark.asyncio
async def test_play_and_stop_still_use_the_real_song_addresses():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await ableton_manager("play")
    assert mock_send.await_args.args[2] == "/live/song/start_playing"

    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await ableton_manager("stop")
    assert mock_send.await_args.args[2] == "/live/song/stop_playing"
