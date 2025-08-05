"""
Tests for Advanced MCP Streaming Protocols

Tests the advanced streaming functionality including bidirectional communication,
flow control, multiplexing, and real-time streaming capabilities.
"""

import asyncio
import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metamcp.mcp.streaming import (
    BidirectionalStream,
    FlowController,
    StreamChunk,
    StreamConfig,
    StreamManager,
    StreamOperation,
    StreamStatus,
    StreamType,
    StreamingProtocol,
)


class TestStreamChunk:
    """Test StreamChunk functionality."""
    
    def test_stream_chunk_creation(self):
        """Test creating a StreamChunk."""
        chunk = StreamChunk(
            stream_id="test-stream",
            chunk_id="test-chunk",
            data={"test": "data"},
            metadata={"type": "test"},
            is_final=False,
            sequence_number=1
        )
        
        assert chunk.stream_id == "test-stream"
        assert chunk.chunk_id == "test-chunk"
        assert chunk.data == {"test": "data"}
        assert chunk.metadata == {"type": "test"}
        assert chunk.is_final is False
        assert chunk.sequence_number == 1
        assert chunk.timestamp > 0
    
    def test_stream_chunk_final(self):
        """Test creating a final StreamChunk."""
        chunk = StreamChunk(
            stream_id="test-stream",
            chunk_id="test-chunk",
            data={"final": "data"},
            is_final=True
        )
        
        assert chunk.is_final is True


class TestFlowController:
    """Test FlowController functionality."""
    
    @pytest.mark.asyncio
    async def test_flow_controller_initialization(self):
        """Test FlowController initialization."""
        controller = FlowController(window_size=100)
        
        assert controller.window_size == 100
        assert controller.window_available == 100
        assert len(controller.sent_chunks) == 0
        assert len(controller.acknowledged_chunks) == 0
    
    @pytest.mark.asyncio
    async def test_can_send(self):
        """Test can_send functionality."""
        controller = FlowController(window_size=2)
        
        # Should be able to send initially
        assert await controller.can_send() is True
        
        # Mark two chunks as sent
        await controller.mark_sent("chunk1")
        await controller.mark_sent("chunk2")
        
        # Should not be able to send more
        assert await controller.can_send() is False
    
    @pytest.mark.asyncio
    async def test_mark_sent_and_acknowledged(self):
        """Test marking chunks as sent and acknowledged."""
        controller = FlowController(window_size=3)
        
        # Mark chunks as sent
        await controller.mark_sent("chunk1")
        await controller.mark_sent("chunk2")
        
        assert controller.window_available == 1
        assert len(controller.sent_chunks) == 2
        
        # Acknowledge chunks
        await controller.mark_acknowledged("chunk1")
        await controller.mark_acknowledged("chunk2")
        
        assert controller.window_available == 3
        assert len(controller.sent_chunks) == 0
        assert len(controller.acknowledged_chunks) == 2
    
    @pytest.mark.asyncio
    async def test_get_window_status(self):
        """Test getting window status."""
        controller = FlowController(window_size=5)
        
        await controller.mark_sent("chunk1")
        await controller.mark_sent("chunk2")
        await controller.mark_acknowledged("chunk1")
        
        status = await controller.get_window_status()
        
        assert status["window_size"] == 5
        assert status["window_available"] == 4
        assert status["sent_count"] == 1
        assert status["acknowledged_count"] == 1


class TestStreamOperation:
    """Test StreamOperation functionality."""
    
    @pytest.mark.asyncio
    async def test_stream_operation_creation(self):
        """Test creating a StreamOperation."""
        config = StreamConfig()
        operation = StreamOperation(
            stream_id="test-stream",
            stream_type=StreamType.TOOL_EXECUTION,
            operation_id="test-op",
            config=config,
            metadata={"test": "metadata"}
        )
        
        assert operation.stream_id == "test-stream"
        assert operation.stream_type == StreamType.TOOL_EXECUTION
        assert operation.operation_id == "test-op"
        assert operation.status == StreamStatus.INITIALIZING
        assert operation.chunks_sent == 0
        assert operation.chunks_received == 0
        assert operation.is_active is False
    
    @pytest.mark.asyncio
    async def test_send_chunk(self):
        """Test sending chunks."""
        config = StreamConfig()
        operation = StreamOperation(
            stream_id="test-stream",
            stream_type=StreamType.TOOL_EXECUTION,
            operation_id="test-op",
            config=config,
            metadata={}
        )
        
        # Send a chunk
        await operation.send_chunk({"test": "data"}, {"type": "test"})
        
        assert operation.chunks_sent == 1
        assert operation.is_active is False  # Still initializing
    
    @pytest.mark.asyncio
    async def test_send_final_chunk(self):
        """Test sending final chunk."""
        config = StreamConfig()
        operation = StreamOperation(
            stream_id="test-stream",
            stream_type=StreamType.TOOL_EXECUTION,
            operation_id="test-op",
            config=config,
            metadata={}
        )
        
        # Send final chunk
        await operation.send_final_chunk({"final": "data"})
        
        assert operation.chunks_sent == 1
        assert operation.status == StreamStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_receive_chunk(self):
        """Test receiving chunks."""
        config = StreamConfig()
        operation = StreamOperation(
            stream_id="test-stream",
            stream_type=StreamType.TOOL_EXECUTION,
            operation_id="test-op",
            config=config,
            metadata={}
        )
        
        # Add a chunk to receive queue
        chunk = StreamChunk(
            stream_id="test-stream",
            chunk_id="test-chunk",
            data={"received": "data"}
        )
        await operation._receive_queue.put(chunk)
        
        # Receive the chunk
        received_chunk = await operation.receive_chunk()
        
        assert received_chunk is not None
        assert received_chunk.data == {"received": "data"}
        assert operation.chunks_received == 1
    
    @pytest.mark.asyncio
    async def test_receive_all_chunks(self):
        """Test receiving all chunks."""
        config = StreamConfig()
        operation = StreamOperation(
            stream_id="test-stream",
            stream_type=StreamType.TOOL_EXECUTION,
            operation_id="test-op",
            config=config,
            metadata={}
        )
        
        # Add chunks to receive queue
        chunk1 = StreamChunk(
            stream_id="test-stream",
            chunk_id="chunk1",
            data={"chunk": 1}
        )
        chunk2 = StreamChunk(
            stream_id="test-stream",
            chunk_id="chunk2",
            data={"chunk": 2},
            is_final=True
        )
        
        await operation._receive_queue.put(chunk1)
        await operation._receive_queue.put(chunk2)
        
        # Receive all chunks
        chunks = []
        async for chunk in operation.receive_all_chunks():
            chunks.append(chunk)
        
        assert len(chunks) == 2
        assert chunks[0].data == {"chunk": 1}
        assert chunks[1].data == {"chunk": 2}
        assert chunks[1].is_final is True
    
    @pytest.mark.asyncio
    async def test_pause_and_resume(self):
        """Test pausing and resuming streams."""
        config = StreamConfig()
        operation = StreamOperation(
            stream_id="test-stream",
            stream_type=StreamType.TOOL_EXECUTION,
            operation_id="test-op",
            config=config,
            metadata={}
        )
        
        # Set to active
        operation.status = StreamStatus.ACTIVE
        
        # Pause
        await operation.pause()
        assert operation.status == StreamStatus.PAUSED
        
        # Resume
        await operation.resume()
        assert operation.status == StreamStatus.RESUMED
    
    @pytest.mark.asyncio
    async def test_cancel_and_close(self):
        """Test canceling and closing streams."""
        config = StreamConfig()
        operation = StreamOperation(
            stream_id="test-stream",
            stream_type=StreamType.TOOL_EXECUTION,
            operation_id="test-op",
            config=config,
            metadata={}
        )
        
        # Cancel
        await operation.cancel()
        assert operation.status == StreamStatus.CANCELLED
        assert operation._closed is True
        
        # Close
        await operation.close()
        assert operation._closed is True
    
    @pytest.mark.asyncio
    async def test_set_error(self):
        """Test setting errors on streams."""
        config = StreamConfig()
        operation = StreamOperation(
            stream_id="test-stream",
            stream_type=StreamType.TOOL_EXECUTION,
            operation_id="test-op",
            config=config,
            metadata={}
        )
        
        error = Exception("Test error")
        operation.set_error(error)
        
        assert operation.status == StreamStatus.ERROR
        assert operation._error == error
        assert operation.has_error is True


class TestStreamManager:
    """Test StreamManager functionality."""
    
    @pytest.mark.asyncio
    async def test_stream_manager_creation(self):
        """Test creating a StreamManager."""
        config = StreamConfig()
        manager = StreamManager(config)
        
        assert len(manager.active_streams) == 0
        assert len(manager.flow_controllers) == 0
    
    @pytest.mark.asyncio
    async def test_create_stream(self):
        """Test creating a stream."""
        config = StreamConfig()
        manager = StreamManager(config)
        
        stream = await manager.create_stream(
            StreamType.TOOL_EXECUTION,
            "test-operation",
            {"test": "metadata"}
        )
        
        assert stream.stream_id in manager.active_streams
        assert stream.stream_id in manager.flow_controllers
        assert stream.stream_type == StreamType.TOOL_EXECUTION
        assert stream.operation_id == "test-operation"
        assert stream.metadata == {"test": "metadata"}
    
    @pytest.mark.asyncio
    async def test_get_stream(self):
        """Test getting a stream."""
        config = StreamConfig()
        manager = StreamManager(config)
        
        created_stream = await manager.create_stream(
            StreamType.TOOL_EXECUTION,
            "test-operation"
        )
        
        retrieved_stream = await manager.get_stream(created_stream.stream_id)
        
        assert retrieved_stream is not None
        assert retrieved_stream.stream_id == created_stream.stream_id
    
    @pytest.mark.asyncio
    async def test_close_stream(self):
        """Test closing a stream."""
        config = StreamConfig()
        manager = StreamManager(config)
        
        stream = await manager.create_stream(
            StreamType.TOOL_EXECUTION,
            "test-operation"
        )
        
        stream_id = stream.stream_id
        assert stream_id in manager.active_streams
        
        await manager.close_stream(stream_id)
        
        assert stream_id not in manager.active_streams
        assert stream_id not in manager.flow_controllers
    
    @pytest.mark.asyncio
    async def test_get_active_streams(self):
        """Test getting active streams information."""
        config = StreamConfig()
        manager = StreamManager(config)
        
        # Create multiple streams
        await manager.create_stream(StreamType.TOOL_EXECUTION, "op1")
        await manager.create_stream(StreamType.RESOURCE_READING, "op2")
        
        streams_info = await manager.get_active_streams()
        
        assert len(streams_info) == 2
        assert any(s["type"] == "tool_execution" for s in streams_info)
        assert any(s["type"] == "resource_reading" for s in streams_info)
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_streams(self):
        """Test cleaning up expired streams."""
        config = StreamConfig(timeout=0.1)  # Very short timeout
        manager = StreamManager(config)
        
        # Create a stream
        stream = await manager.create_stream(
            StreamType.TOOL_EXECUTION,
            "test-operation"
        )
        
        # Wait for stream to expire
        await asyncio.sleep(0.2)
        
        # Cleanup expired streams
        await manager._cleanup_expired_streams()
        
        # Stream should be removed
        assert stream.stream_id not in manager.active_streams


class TestBidirectionalStream:
    """Test BidirectionalStream functionality."""
    
    @pytest.mark.asyncio
    async def test_bidirectional_stream_creation(self):
        """Test creating a BidirectionalStream."""
        config = StreamConfig()
        manager = StreamManager(config)
        
        stream = await manager.create_stream(
            StreamType.TOOL_EXECUTION,
            "test-operation"
        )
        
        bidirectional = BidirectionalStream(manager, stream.stream_id)
        
        assert bidirectional.stream_id == stream.stream_id
        assert bidirectional.flow_controller is not None
    
    @pytest.mark.asyncio
    async def test_bidirectional_stream_start_stop(self):
        """Test starting and stopping bidirectional streams."""
        config = StreamConfig()
        manager = StreamManager(config)
        
        stream = await manager.create_stream(
            StreamType.TOOL_EXECUTION,
            "test-operation"
        )
        
        bidirectional = BidirectionalStream(manager, stream.stream_id)
        
        # Start the stream
        await bidirectional.start()
        
        assert bidirectional._send_task is not None
        assert bidirectional._receive_task is not None
        
        # Stop the stream
        await bidirectional.stop()
        
        # Tasks should be cancelled
        assert bidirectional._send_task.cancelled()
        assert bidirectional._receive_task.cancelled()


class TestStreamingProtocol:
    """Test StreamingProtocol functionality."""
    
    @pytest.mark.asyncio
    async def test_streaming_protocol_initialization(self):
        """Test initializing StreamingProtocol."""
        config = StreamConfig()
        protocol = StreamingProtocol(config)
        
        await protocol.initialize()
        
        assert protocol.stream_manager is not None
        assert len(protocol.bidirectional_streams) == 0
    
    @pytest.mark.asyncio
    async def test_create_bidirectional_stream(self):
        """Test creating bidirectional streams."""
        config = StreamConfig()
        protocol = StreamingProtocol(config)
        await protocol.initialize()
        
        bidirectional = await protocol.create_bidirectional_stream(
            StreamType.TOOL_EXECUTION,
            "test-operation",
            {"test": "metadata"}
        )
        
        assert bidirectional.stream_id in protocol.bidirectional_streams
        assert bidirectional.stream_id in protocol.stream_manager.active_streams
    
    @pytest.mark.asyncio
    async def test_send_streaming_tool_execution(self):
        """Test streaming tool execution."""
        config = StreamConfig()
        protocol = StreamingProtocol(config)
        await protocol.initialize()
        
        # Mock the stream to avoid actual execution
        with patch.object(protocol.stream_manager, 'create_stream') as mock_create:
            mock_stream = AsyncMock()
            mock_create.return_value = mock_stream
            
            # Mock receive_all_chunks to return some chunks
            mock_chunk = StreamChunk(
                stream_id="test-stream",
                chunk_id="test-chunk",
                data={"result": "test"}
            )
            mock_stream.receive_all_chunks.return_value = [mock_chunk]
            
            chunks = []
            async for chunk in protocol.send_streaming_tool_execution(
                "test_tool",
                {"param": "value"},
                "test-operation"
            ):
                chunks.append(chunk)
            
            assert len(chunks) == 1
            assert chunks[0].data == {"result": "test"}
    
    @pytest.mark.asyncio
    async def test_send_streaming_resource_reading(self):
        """Test streaming resource reading."""
        config = StreamConfig()
        protocol = StreamingProtocol(config)
        await protocol.initialize()
        
        # Mock the stream
        with patch.object(protocol.stream_manager, 'create_stream') as mock_create:
            mock_stream = AsyncMock()
            mock_create.return_value = mock_stream
            
            mock_chunk = StreamChunk(
                stream_id="test-stream",
                chunk_id="test-chunk",
                data={"content": "test content"}
            )
            mock_stream.receive_all_chunks.return_value = [mock_chunk]
            
            chunks = []
            async for chunk in protocol.send_streaming_resource_reading(
                "test://resource",
                "test-operation"
            ):
                chunks.append(chunk)
            
            assert len(chunks) == 1
            assert chunks[0].data == {"content": "test content"}
    
    @pytest.mark.asyncio
    async def test_broadcast_event_stream(self):
        """Test broadcasting event streams."""
        config = StreamConfig()
        protocol = StreamingProtocol(config)
        await protocol.initialize()
        
        # Mock the stream
        with patch.object(protocol.stream_manager, 'create_stream') as mock_create:
            mock_stream = AsyncMock()
            mock_create.return_value = mock_stream
            
            await protocol.broadcast_event_stream(
                "test_event",
                {"data": "test"},
                "test-operation"
            )
            
            # Verify send_chunk and send_final_chunk were called
            mock_stream.send_chunk.assert_called_once()
            mock_stream.send_final_chunk.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_streaming_statistics(self):
        """Test getting streaming statistics."""
        config = StreamConfig()
        protocol = StreamingProtocol(config)
        await protocol.initialize()
        
        # Create some streams
        await protocol.create_bidirectional_stream(
            StreamType.TOOL_EXECUTION,
            "op1"
        )
        await protocol.create_bidirectional_stream(
            StreamType.RESOURCE_READING,
            "op2"
        )
        
        stats = await protocol.get_streaming_statistics()
        
        assert stats["active_streams"] == 2
        assert "tool_execution" in stats["streams_by_type"]
        assert "resource_reading" in stats["streams_by_type"]
        assert stats["streams_by_type"]["tool_execution"] == 1
        assert stats["streams_by_type"]["resource_reading"] == 1
    
    @pytest.mark.asyncio
    async def test_shutdown(self):
        """Test shutting down the streaming protocol."""
        config = StreamConfig()
        protocol = StreamingProtocol(config)
        await protocol.initialize()
        
        # Create a bidirectional stream
        bidirectional = await protocol.create_bidirectional_stream(
            StreamType.TOOL_EXECUTION,
            "test-operation"
        )
        
        # Mock the stop method
        with patch.object(bidirectional, 'stop') as mock_stop:
            await protocol.shutdown()
            
            # Verify stop was called
            mock_stop.assert_called_once()
        
        # Verify all streams are closed
        assert len(protocol.stream_manager.active_streams) == 0


class TestStreamingIntegration:
    """Integration tests for streaming functionality."""
    
    @pytest.mark.asyncio
    async def test_complete_streaming_workflow(self):
        """Test a complete streaming workflow."""
        config = StreamConfig()
        protocol = StreamingProtocol(config)
        await protocol.initialize()
        
        # Create a bidirectional stream
        bidirectional = await protocol.create_bidirectional_stream(
            StreamType.TOOL_EXECUTION,
            "test-workflow",
            {"workflow": "test"}
        )
        
        # Get the underlying stream
        stream = await protocol.stream_manager.get_stream(bidirectional.stream_id)
        
        # Send some chunks
        await stream.send_chunk({"step": 1, "data": "processing"})
        await stream.send_chunk({"step": 2, "data": "more processing"})
        await stream.send_final_chunk({"step": 3, "data": "complete"})
        
        # Receive all chunks
        chunks = []
        async for chunk in stream.receive_all_chunks():
            chunks.append(chunk)
        
        # Verify we got all chunks
        assert len(chunks) == 3
        assert chunks[0].data["step"] == 1
        assert chunks[1].data["step"] == 2
        assert chunks[2].data["step"] == 3
        assert chunks[2].is_final is True
        
        # Cleanup
        await protocol.shutdown()
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_streams(self):
        """Test multiple concurrent streams."""
        config = StreamConfig()
        protocol = StreamingProtocol(config)
        await protocol.initialize()
        
        # Create multiple streams
        streams = []
        for i in range(3):
            stream = await protocol.create_bidirectional_stream(
                StreamType.TOOL_EXECUTION,
                f"operation-{i}"
            )
            streams.append(stream)
        
        # Verify all streams are created
        assert len(protocol.bidirectional_streams) == 3
        assert len(protocol.stream_manager.active_streams) == 3
        
        # Get statistics
        stats = await protocol.get_streaming_statistics()
        assert stats["active_streams"] == 3
        
        # Cleanup
        await protocol.shutdown()
    
    @pytest.mark.asyncio
    async def test_flow_control_integration(self):
        """Test flow control integration."""
        config = StreamConfig()
        manager = StreamManager(config)
        
        # Create a stream
        stream = await manager.create_stream(
            StreamType.TOOL_EXECUTION,
            "test-operation"
        )
        
        # Get the flow controller
        flow_controller = manager.flow_controllers[stream.stream_id]
        
        # Test flow control
        assert await flow_controller.can_send() is True
        
        # Mark chunks as sent until window is full
        for i in range(flow_controller.window_size):
            await flow_controller.mark_sent(f"chunk-{i}")
        
        assert await flow_controller.can_send() is False
        
        # Acknowledge some chunks
        await flow_controller.mark_acknowledged("chunk-0")
        await flow_controller.mark_acknowledged("chunk-1")
        
        assert await flow_controller.can_send() is True
        
        # Cleanup
        await manager.close_stream(stream.stream_id)