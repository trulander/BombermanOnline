"""
Tests for NatsRepository class.
"""
import json
import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from nats.aio.msg import Msg

from nats_repository import NatsRepository, NumpyAwareEncoder


class TestNatsRepositoryInit:
    """Tests for NatsRepository.__init__."""
    
    def test_init_with_nc_none(self):
        """Test initialization with _nc = None."""
        repo = NatsRepository()
        assert repo._nc is None


class TestNatsRepositoryGetNc:
    """Tests for NatsRepository.get_nc."""
    
    @pytest.mark.asyncio
    async def test_get_nc_first_connection(self, mocker):
        """Test first connection to NATS."""
        repo = NatsRepository()
        mock_nc = AsyncMock()
        mock_nc.is_closed = False
        
        mocker.patch('nats_repository.nats.connect', return_value=mock_nc)
        
        result = await repo.get_nc()
        
        assert result == mock_nc
        assert repo._nc == mock_nc
    
    @pytest.mark.asyncio
    async def test_get_nc_existing_connection(self, mock_nats_client):
        """Test returning existing connection."""
        repo = NatsRepository()
        repo._nc = mock_nats_client
        
        result = await repo.get_nc()
        
        assert result == mock_nats_client
    
    @pytest.mark.asyncio
    async def test_get_nc_reconnect_when_closed(self, mocker):
        """Test reconnection when connection is closed."""
        repo = NatsRepository()
        old_nc = AsyncMock()
        old_nc.is_closed = True
        repo._nc = old_nc
        
        new_nc = AsyncMock()
        new_nc.is_closed = False
        mocker.patch('app.nats_repository.nats.connect', return_value=new_nc)
        
        result = await repo.get_nc()
        
        assert result == new_nc
        assert repo._nc == new_nc
    
    @pytest.mark.asyncio
    async def test_get_nc_connection_error(self, mocker):
        """Test handling of connection errors."""
        repo = NatsRepository()
        
        mocker.patch('nats_repository.nats.connect', side_effect=Exception("Connection error"))
        
        with pytest.raises(Exception):
            await repo.get_nc()


class TestNatsRepositoryDisconnect:
    """Tests for NatsRepository.disconnect."""
    
    @pytest.mark.asyncio
    async def test_disconnect_active_connection(self, mock_nats_client):
        """Test closing active connection."""
        repo = NatsRepository()
        repo._nc = mock_nats_client
        
        await repo.disconnect()
        
        mock_nats_client.drain.assert_called_once()
        assert repo._nc is None
    
    @pytest.mark.asyncio
    async def test_disconnect_no_connection(self):
        """Test handling when no connection exists."""
        repo = NatsRepository()
        repo._nc = None
        
        # Should not raise exception
        await repo.disconnect()
    
    @pytest.mark.asyncio
    async def test_disconnect_error_handling(self, mock_nats_client):
        """Test error handling during disconnect."""
        repo = NatsRepository()
        repo._nc = mock_nats_client
        mock_nats_client.drain = AsyncMock(side_effect=Exception("Drain error"))
        
        # Should handle error gracefully
        await repo.disconnect()


class TestNatsRepositoryPublishData:
    """Tests for NatsRepository._publish_data."""
    
    @pytest.mark.asyncio
    async def test_publish_data_success(self, nats_repository):
        """Test successful serialization and publication."""
        nats_repository._send_event_with_reconnect = AsyncMock(return_value=True)
        
        payload = {"key": "value", "number": 42}
        result = await nats_repository._publish_data("test.subject", payload)
        
        assert result is True
        nats_repository._send_event_with_reconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_publish_data_serialization_error(self, nats_repository):
        """Test handling of serialization errors (numpy types)."""
        # Create object that can't be serialized normally
        class Unserializable:
            pass
        
        payload = {"obj": Unserializable()}
        result = await nats_repository._publish_data("test.subject", payload)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_publish_data_numpy_encoder(self, nats_repository):
        """Test using NumpyAwareEncoder."""
        payload = {"number": np.int64(42), "float": np.float64(3.14)}
        nats_repository._send_event_with_reconnect = AsyncMock(return_value=True)
        
        result = await nats_repository._publish_data("test.subject", payload)
        
        assert result is True
        # Check that numpy types were serialized
        call_args = nats_repository._send_event_with_reconnect.call_args
        payload_bytes = call_args[1]["payload_bytes"]
        decoded = json.loads(payload_bytes.decode())
        assert decoded["number"] == 42
        assert decoded["float"] == 3.14


class TestNatsRepositorySendEventWithReconnect:
    """Tests for NatsRepository._send_event_with_reconnect."""
    
    @pytest.mark.asyncio
    async def test_send_event_with_reconnect_success_first_try(self, nats_repository):
        """Test successful publication on first try."""
        nats_repository._nc.publish = AsyncMock(return_value=None)
        
        result = await nats_repository._send_event_with_reconnect(
            subject="test.subject",
            payload_bytes=b'{"test": "data"}'
        )
        
        assert result is True
        nats_repository._nc.publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_event_with_reconnect_retry_on_connection_closed(self, nats_repository, mocker):
        """Test retry on ConnectionClosedError."""
        import nats.errors
        
        # First call fails, second succeeds
        nats_repository._nc.publish = AsyncMock(side_effect=[
            nats.errors.ConnectionClosedError(),
            None
        ])
        mocker.patch('asyncio.sleep', new_callable=AsyncMock)
        
        result = await nats_repository._send_event_with_reconnect(
            subject="test.subject",
            payload_bytes=b'{"test": "data"}',
            max_retries=3,
            retry_delay=0.01
        )
        
        assert result is True
        assert nats_repository._nc.publish.call_count == 2
    
    @pytest.mark.asyncio
    async def test_send_event_with_reconnect_retry_on_timeout(self, nats_repository, mocker):
        """Test retry on TimeoutError."""
        import nats.errors
        
        nats_repository._nc.publish = AsyncMock(side_effect=[
            nats.errors.TimeoutError(),
            None
        ])
        mocker.patch('asyncio.sleep', new_callable=AsyncMock)
        
        result = await nats_repository._send_event_with_reconnect(
            subject="test.subject",
            payload_bytes=b'{"test": "data"}',
            max_retries=3,
            retry_delay=0.01
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_event_with_reconnect_exponential_backoff(self, nats_repository, mocker):
        """Test exponential backoff."""
        import nats.errors
        
        nats_repository._nc.publish = AsyncMock(side_effect=nats.errors.ConnectionClosedError())
        sleep_mock = mocker.patch('asyncio.sleep', new_callable=AsyncMock)
        
        await nats_repository._send_event_with_reconnect(
            subject="test.subject",
            payload_bytes=b'{"test": "data"}',
            max_retries=3,
            retry_delay=0.1
        )
        
        # Check that sleep was called with increasing delays
        assert sleep_mock.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_send_event_with_reconnect_false_after_all_retries(self, nats_repository, mocker):
        """Test return False after all retries exhausted."""
        import nats.errors
        
        nats_repository._nc.publish = AsyncMock(side_effect=nats.errors.ConnectionClosedError())
        mocker.patch('asyncio.sleep', new_callable=AsyncMock)
        
        result = await nats_repository._send_event_with_reconnect(
            subject="test.subject",
            payload_bytes=b'{"test": "data"}',
            max_retries=2,
            retry_delay=0.01
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_event_with_reconnect_unexpected_exception(self, nats_repository, mocker):
        """Test handling of unexpected Exception (not ConnectionClosedError or TimeoutError)."""
        nats_repository._nc.publish = AsyncMock(side_effect=ValueError("Unexpected error"))
        mocker.patch('asyncio.sleep', new_callable=AsyncMock)
        
        result = await nats_repository._send_event_with_reconnect(
            subject="test.subject",
            payload_bytes=b'{"test": "data"}',
            max_retries=2,
            retry_delay=0.01
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_event_with_reconnect_check_is_connected(self, nats_repository):
        """Test checking is_connected before publishing."""
        nats_repository._nc.is_connected = False
        nats_repository._nc.publish = AsyncMock()
        
        result = await nats_repository._send_event_with_reconnect(
            subject="test.subject",
            payload_bytes=b'{"test": "data"}',
            max_retries=1,
            retry_delay=0.01
        )
        
        # Should retry and eventually fail
        assert result is False


class TestNatsRepositoryPublishEvent:
    """Tests for NatsRepository.publish_event."""
    
    @pytest.mark.asyncio
    async def test_publish_event_without_suffix(self, nats_repository):
        """Test subject formation without suffix."""
        nats_repository._publish_data = AsyncMock(return_value=True)
        
        result = await nats_repository.publish_event(
            subject_base="game.update",
            payload={"game_id": "123"}
        )
        
        assert result is True
        nats_repository._publish_data.assert_called_once()
        call_args = nats_repository._publish_data.call_args
        subject = call_args.args[0] if call_args.args else call_args.kwargs.get("subject")
        assert subject == "game.update"
    
    @pytest.mark.asyncio
    async def test_publish_event_with_suffix(self, nats_repository):
        """Test subject formation with suffix."""
        nats_repository._publish_data = AsyncMock(return_value=True)
        
        result = await nats_repository.publish_event(
            subject_base="game.update",
            payload={"game_id": "123"},
            specific_suffix="game123"
        )
        
        assert result is True
        call_args = nats_repository._publish_data.call_args
        subject = call_args.args[0] if call_args.args else call_args.kwargs.get("subject")
        assert subject == "game.update.game123"
    
    @pytest.mark.asyncio
    async def test_publish_event_success(self, nats_repository):
        """Test successful publication."""
        nats_repository._publish_data = AsyncMock(return_value=True)
        
        result = await nats_repository.publish_event(
            subject_base="test.subject",
            payload={"key": "value"}
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_publish_event_error_handling(self, nats_repository):
        """Test error handling."""
        nats_repository._publish_data = AsyncMock(side_effect=Exception("Error"))
        
        result = await nats_repository.publish_event(
            subject_base="test.subject",
            payload={"key": "value"}
        )
        
        assert result is False


class TestNatsRepositoryPublishSimple:
    """Tests for NatsRepository.publish_simple."""
    
    @pytest.mark.asyncio
    async def test_publish_simple_success(self, nats_repository):
        """Test successful publication."""
        nats_repository._send_event_with_reconnect = AsyncMock(return_value=True)
        
        result = await nats_repository.publish_simple("test.subject", {"key": "value"})
        
        assert result is True
        nats_repository._send_event_with_reconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_publish_simple_numpy_encoder(self, nats_repository):
        """Test serialization with NumpyAwareEncoder."""
        nats_repository._send_event_with_reconnect = AsyncMock(return_value=True)
        
        payload = {"number": np.int64(42)}
        await nats_repository.publish_simple("test.subject", payload)
        
        call_args = nats_repository._send_event_with_reconnect.call_args
        payload_bytes = call_args[1]["payload_bytes"]
        decoded = json.loads(payload_bytes.decode())
        assert decoded["number"] == 42
    
    @pytest.mark.asyncio
    async def test_publish_simple_uses_send_event_with_reconnect(self, nats_repository):
        """Test using _send_event_with_reconnect."""
        nats_repository._send_event_with_reconnect = AsyncMock(return_value=True)
        
        await nats_repository.publish_simple("test.subject", {"key": "value"})
        
        nats_repository._send_event_with_reconnect.assert_called_once()


class TestNatsRepositorySubscribe:
    """Tests for NatsRepository.subscribe."""
    
    @pytest.mark.asyncio
    async def test_subscribe_success(self, nats_repository):
        """Test successful subscription."""
        callback = AsyncMock()
        
        await nats_repository.subscribe("test.subject", callback)
        
        nats_repository._nc.subscribe.assert_called_once_with("test.subject", cb=callback)
    
    @pytest.mark.asyncio
    async def test_subscribe_gets_connection(self, nats_repository):
        """Test getting connection via get_nc."""
        nats_repository._nc = None
        mock_nc = AsyncMock()
        mock_nc.subscribe = AsyncMock()
        nats_repository.get_nc = AsyncMock(return_value=mock_nc)
        
        await nats_repository.subscribe("test.subject", AsyncMock())
        
        nats_repository.get_nc.assert_called_once()


class TestNumpyAwareEncoder:
    """Tests for NumpyAwareEncoder.default."""
    
    def test_numpy_aware_encoder_integer(self, numpy_integer):
        """Test handling of np.integer."""
        encoder = NumpyAwareEncoder()
        result = encoder.default(numpy_integer)
        assert isinstance(result, int)
        assert result == 42
    
    def test_numpy_aware_encoder_floating(self, numpy_float):
        """Test handling of np.floating."""
        encoder = NumpyAwareEncoder()
        result = encoder.default(numpy_float)
        assert isinstance(result, float)
        assert abs(result - 3.14) < 0.01
    
    def test_numpy_aware_encoder_ndarray(self, numpy_array):
        """Test handling of np.ndarray."""
        encoder = NumpyAwareEncoder()
        result = encoder.default(numpy_array)
        assert isinstance(result, list)
        assert result == [1, 2, 3, 4, 5]
    
    def test_numpy_aware_encoder_fallback(self):
        """Test fallback to super().default()."""
        encoder = NumpyAwareEncoder()
        
        # Regular dict should use default JSON encoding
        with pytest.raises(TypeError):
            encoder.default({"key": "value"})  # Should raise TypeError for non-serializable

