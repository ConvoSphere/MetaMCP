"""
Advanced MCP Streaming Protocols

This module provides advanced bidirectional streaming protocols for MCP,
including chunked transfer, flow control, multiplexing, and real-time
communication capabilities.
"""

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Set

from ..utils.logging import get_logger

logger = get_logger(__name__)


class StreamType(Enum):
    """Types of streaming operations."""
    TOOL_EXECUTION = "tool_execution"
    RESOURCE_READING = "resource_reading"
    PROMPT_STREAMING = "prompt_streaming"
    EVENT_STREAMING = "event_streaming"
    LOG_STREAMING = "log_streaming"
    PROGRESS_STREAMING = "progress_streaming"


class StreamStatus(Enum):
    """Stream status enumeration."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    RESUMED = "resumed"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class StreamChunk:
    """Represents a chunk of streaming data."""
    stream_id: str
    chunk_id: str
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    is_final: bool = False
    sequence_number: int = 0


@dataclass
class StreamConfig:
    """Configuration for streaming operations."""
    chunk_size: int = 1024
    buffer_size: int = 8192
    timeout: float = 30.0
    retry_attempts: int = 3
    flow_control_enabled: bool = True
    compression_enabled: bool = False
    multiplexing_enabled: bool = True


class FlowController:
    """Manages flow control for streaming operations."""
    
    def __init__(self, window_size: int = 1000):
        """Initialize flow controller."""
        self.window_size = window_size
        self.sent_chunks: Set[str] = set()
        self.acknowledged_chunks: Set[str] = set()
        self.window_available = window_size
        self._lock = asyncio.Lock()
    
    async def can_send(self) -> bool:
        """Check if we can send more chunks."""
        async with self._lock:
            return self.window_available > 0
    
    async def mark_sent(self, chunk_id: str) -> None:
        """Mark a chunk as sent."""
        async with self._lock:
            self.sent_chunks.add(chunk_id)
            self.window_available -= 1
    
    async def mark_acknowledged(self, chunk_id: str) -> None:
        """Mark a chunk as acknowledged."""
        async with self._lock:
            if chunk_id in self.sent_chunks:
                self.sent_chunks.remove(chunk_id)
                self.acknowledged_chunks.add(chunk_id)
                self.window_available += 1
    
    async def get_window_status(self) -> Dict[str, Any]:
        """Get current window status."""
        async with self._lock:
            return {
                "window_size": self.window_size,
                "window_available": self.window_available,
                "sent_count": len(self.sent_chunks),
                "acknowledged_count": len(self.acknowledged_chunks),
            }


class StreamManager:
    """Manages multiple streaming operations with multiplexing."""
    
    def __init__(self, config: StreamConfig):
        """Initialize stream manager."""
        self.config = config
        self.active_streams: Dict[str, 'StreamOperation'] = {}
        self.flow_controllers: Dict[str, FlowController] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def create_stream(
        self, 
        stream_type: StreamType, 
        operation_id: str,
        metadata: Dict[str, Any] = None
    ) -> 'StreamOperation':
        """Create a new streaming operation."""
        stream_id = str(uuid.uuid4())
        
        async with self._lock:
            stream = StreamOperation(
                stream_id=stream_id,
                stream_type=stream_type,
                operation_id=operation_id,
                config=self.config,
                metadata=metadata or {}
            )
            
            self.active_streams[stream_id] = stream
            self.flow_controllers[stream_id] = FlowController()
            
            logger.info(f"Created stream {stream_id} for {stream_type.value}")
            return stream
    
    async def get_stream(self, stream_id: str) -> Optional['StreamOperation']:
        """Get a stream by ID."""
        async with self._lock:
            return self.active_streams.get(stream_id)
    
    async def close_stream(self, stream_id: str) -> None:
        """Close a stream."""
        async with self._lock:
            if stream_id in self.active_streams:
                stream = self.active_streams[stream_id]
                await stream.close()
                del self.active_streams[stream_id]
                del self.flow_controllers[stream_id]
                logger.info(f"Closed stream {stream_id}")
    
    async def get_active_streams(self) -> List[Dict[str, Any]]:
        """Get information about all active streams."""
        async with self._lock:
            streams_info = []
            for stream_id, stream in self.active_streams.items():
                streams_info.append({
                    "stream_id": stream_id,
                    "type": stream.stream_type.value,
                    "operation_id": stream.operation_id,
                    "status": stream.status.value,
                    "chunks_sent": stream.chunks_sent,
                    "chunks_received": stream.chunks_received,
                    "created_at": stream.created_at,
                })
            return streams_info
    
    async def start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(60)  # Cleanup every minute
                await self._cleanup_expired_streams()
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
    
    async def _cleanup_expired_streams(self) -> None:
        """Clean up expired streams."""
        current_time = time.time()
        expired_streams = []
        
        async with self._lock:
            for stream_id, stream in self.active_streams.items():
                if current_time - stream.created_at > self.config.timeout:
                    expired_streams.append(stream_id)
        
        for stream_id in expired_streams:
            await self.close_stream(stream_id)


class StreamOperation:
    """Represents a single streaming operation."""
    
    def __init__(
        self,
        stream_id: str,
        stream_type: StreamType,
        operation_id: str,
        config: StreamConfig,
        metadata: Dict[str, Any]
    ):
        """Initialize stream operation."""
        self.stream_id = stream_id
        self.stream_type = stream_type
        self.operation_id = operation_id
        self.config = config
        self.metadata = metadata
        
        self.status = StreamStatus.INITIALIZING
        self.chunks_sent = 0
        self.chunks_received = 0
        self.created_at = time.time()
        self.last_activity = time.time()
        
        self._send_queue: asyncio.Queue = asyncio.Queue(maxsize=config.buffer_size)
        self._receive_queue: asyncio.Queue = asyncio.Queue(maxsize=config.buffer_size)
        self._error: Optional[Exception] = None
        self._closed = False
    
    async def send_chunk(self, data: Any, metadata: Dict[str, Any] = None) -> None:
        """Send a chunk of data."""
        if self._closed:
            raise RuntimeError("Stream is closed")
        
        chunk = StreamChunk(
            stream_id=self.stream_id,
            chunk_id=str(uuid.uuid4()),
            data=data,
            metadata=metadata or {},
            sequence_number=self.chunks_sent,
            is_final=False
        )
        
        await self._send_queue.put(chunk)
        self.chunks_sent += 1
        self.last_activity = time.time()
        
        logger.debug(f"Sent chunk {chunk.chunk_id} on stream {self.stream_id}")
    
    async def send_final_chunk(self, data: Any = None, metadata: Dict[str, Any] = None) -> None:
        """Send final chunk and close stream."""
        chunk = StreamChunk(
            stream_id=self.stream_id,
            chunk_id=str(uuid.uuid4()),
            data=data,
            metadata=metadata or {},
            sequence_number=self.chunks_sent,
            is_final=True
        )
        
        await self._send_queue.put(chunk)
        self.chunks_sent += 1
        self.status = StreamStatus.COMPLETED
        self.last_activity = time.time()
        
        logger.info(f"Sent final chunk on stream {self.stream_id}")
    
    async def receive_chunk(self) -> Optional[StreamChunk]:
        """Receive a chunk of data."""
        if self._closed:
            return None
        
        try:
            chunk = await asyncio.wait_for(
                self._receive_queue.get(), 
                timeout=self.config.timeout
            )
            self.chunks_received += 1
            self.last_activity = time.time()
            return chunk
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for chunk on stream {self.stream_id}")
            return None
    
    async def receive_all_chunks(self) -> AsyncGenerator[StreamChunk, None]:
        """Receive all chunks until stream is closed."""
        while not self._closed:
            chunk = await self.receive_chunk()
            if chunk is None:
                break
            yield chunk
            if chunk.is_final:
                break
    
    async def pause(self) -> None:
        """Pause the stream."""
        if self.status == StreamStatus.ACTIVE:
            self.status = StreamStatus.PAUSED
            logger.info(f"Paused stream {self.stream_id}")
    
    async def resume(self) -> None:
        """Resume the stream."""
        if self.status == StreamStatus.PAUSED:
            self.status = StreamStatus.RESUMED
            logger.info(f"Resumed stream {self.stream_id}")
    
    async def cancel(self) -> None:
        """Cancel the stream."""
        self.status = StreamStatus.CANCELLED
        self._closed = True
        logger.info(f"Cancelled stream {self.stream_id}")
    
    async def close(self) -> None:
        """Close the stream."""
        self._closed = True
        logger.info(f"Closed stream {self.stream_id}")
    
    def set_error(self, error: Exception) -> None:
        """Set an error on the stream."""
        self._error = error
        self.status = StreamStatus.ERROR
        logger.error(f"Stream {self.stream_id} error: {error}")
    
    @property
    def is_active(self) -> bool:
        """Check if stream is active."""
        return (
            not self._closed and 
            self.status in [StreamStatus.ACTIVE, StreamStatus.RESUMED]
        )
    
    @property
    def has_error(self) -> bool:
        """Check if stream has an error."""
        return self._error is not None


class BidirectionalStream:
    """Bidirectional streaming channel with flow control."""
    
    def __init__(self, stream_manager: StreamManager, stream_id: str):
        """Initialize bidirectional stream."""
        self.stream_manager = stream_manager
        self.stream_id = stream_id
        self.flow_controller = stream_manager.flow_controllers[stream_id]
        self._send_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the bidirectional stream."""
        self._send_task = asyncio.create_task(self._send_loop())
        self._receive_task = asyncio.create_task(self._receive_loop())
    
    async def _send_loop(self) -> None:
        """Send loop with flow control."""
        stream = await self.stream_manager.get_stream(self.stream_id)
        if not stream:
            return
        
        while stream.is_active:
            try:
                # Check flow control
                if not await self.flow_controller.can_send():
                    await asyncio.sleep(0.01)  # Wait for window space
                    continue
                
                # Get chunk from send queue
                chunk = await asyncio.wait_for(
                    stream._send_queue.get(), 
                    timeout=1.0
                )
                
                # Send chunk (this would be implemented by the transport layer)
                await self._send_chunk_to_transport(chunk)
                
                # Mark as sent for flow control
                await self.flow_controller.mark_sent(chunk.chunk_id)
                
                if chunk.is_final:
                    break
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                stream.set_error(e)
                break
    
    async def _receive_loop(self) -> None:
        """Receive loop."""
        stream = await self.stream_manager.get_stream(self.stream_id)
        if not stream:
            return
        
        while stream.is_active:
            try:
                # Receive chunk from transport
                chunk = await self._receive_chunk_from_transport()
                if chunk:
                    await stream._receive_queue.put(chunk)
                    
                    # Send acknowledgment
                    await self._send_acknowledgment(chunk.chunk_id)
                    
                    if chunk.is_final:
                        break
                        
            except Exception as e:
                stream.set_error(e)
                break
    
    async def _send_chunk_to_transport(self, chunk: StreamChunk) -> None:
        """Send chunk to transport layer (to be implemented)."""
        # This would be implemented by the specific transport layer
        # For now, we'll just log it
        logger.debug(f"Sending chunk {chunk.chunk_id} via transport")
    
    async def _receive_chunk_from_transport(self) -> Optional[StreamChunk]:
        """Receive chunk from transport layer (to be implemented)."""
        # This would be implemented by the specific transport layer
        # For now, we'll return None
        return None
    
    async def _send_acknowledgment(self, chunk_id: str) -> None:
        """Send acknowledgment for received chunk."""
        # This would be implemented by the specific transport layer
        logger.debug(f"Sending acknowledgment for chunk {chunk_id}")
    
    async def stop(self) -> None:
        """Stop the bidirectional stream."""
        if self._send_task:
            self._send_task.cancel()
        if self._receive_task:
            self._receive_task.cancel()
        
        try:
            await self._send_task
        except asyncio.CancelledError:
            pass
        
        try:
            await self._receive_task
        except asyncio.CancelledError:
            pass


class StreamingProtocol:
    """Advanced streaming protocol implementation."""
    
    def __init__(self, config: StreamConfig = None):
        """Initialize streaming protocol."""
        self.config = config or StreamConfig()
        self.stream_manager = StreamManager(self.config)
        self.bidirectional_streams: Dict[str, BidirectionalStream] = {}
    
    async def initialize(self) -> None:
        """Initialize the streaming protocol."""
        await self.stream_manager.start_cleanup_task()
        logger.info("Streaming protocol initialized")
    
    async def create_bidirectional_stream(
        self,
        stream_type: StreamType,
        operation_id: str,
        metadata: Dict[str, Any] = None
    ) -> BidirectionalStream:
        """Create a bidirectional streaming channel."""
        stream = await self.stream_manager.create_stream(
            stream_type, operation_id, metadata
        )
        
        bidirectional = BidirectionalStream(self.stream_manager, stream.stream_id)
        self.bidirectional_streams[stream.stream_id] = bidirectional
        
        await bidirectional.start()
        return bidirectional
    
    async def send_streaming_tool_execution(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        operation_id: str
    ) -> AsyncGenerator[StreamChunk, None]:
        """Send streaming tool execution."""
        stream = await self.stream_manager.create_stream(
            StreamType.TOOL_EXECUTION,
            operation_id,
            {"tool_name": tool_name, "arguments": arguments}
        )
        
        # Send initial chunk
        await stream.send_chunk({
            "type": "tool_execution_start",
            "tool_name": tool_name,
            "arguments": arguments
        })
        
        # Yield chunks as they come in
        async for chunk in stream.receive_all_chunks():
            yield chunk
    
    async def send_streaming_resource_reading(
        self,
        uri: str,
        operation_id: str
    ) -> AsyncGenerator[StreamChunk, None]:
        """Send streaming resource reading."""
        stream = await self.stream_manager.create_stream(
            StreamType.RESOURCE_READING,
            operation_id,
            {"uri": uri}
        )
        
        # Send initial chunk
        await stream.send_chunk({
            "type": "resource_reading_start",
            "uri": uri
        })
        
        # Yield chunks as they come in
        async for chunk in stream.receive_all_chunks():
            yield chunk
    
    async def broadcast_event_stream(
        self,
        event_type: str,
        data: Dict[str, Any],
        operation_id: str
    ) -> None:
        """Broadcast event stream to all connected clients."""
        stream = await self.stream_manager.create_stream(
            StreamType.EVENT_STREAMING,
            operation_id,
            {"event_type": event_type, "data": data}
        )
        
        await stream.send_chunk({
            "type": "event_broadcast",
            "event_type": event_type,
            "data": data,
            "timestamp": time.time()
        })
        
        await stream.send_final_chunk()
    
    async def get_streaming_statistics(self) -> Dict[str, Any]:
        """Get streaming statistics."""
        active_streams = await self.stream_manager.get_active_streams()
        
        return {
            "active_streams": len(active_streams),
            "total_chunks_sent": sum(s["chunks_sent"] for s in active_streams),
            "total_chunks_received": sum(s["chunks_received"] for s in active_streams),
            "streams_by_type": self._group_streams_by_type(active_streams),
            "flow_control_status": await self._get_flow_control_status()
        }
    
    def _group_streams_by_type(self, streams: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group streams by type."""
        grouped = {}
        for stream in streams:
            stream_type = stream["type"]
            grouped[stream_type] = grouped.get(stream_type, 0) + 1
        return grouped
    
    async def _get_flow_control_status(self) -> Dict[str, Any]:
        """Get flow control status for all streams."""
        status = {}
        for stream_id, controller in self.stream_manager.flow_controllers.items():
            status[stream_id] = await controller.get_window_status()
        return status
    
    async def shutdown(self) -> None:
        """Shutdown the streaming protocol."""
        # Close all bidirectional streams
        for stream_id, bidirectional in self.bidirectional_streams.items():
            await bidirectional.stop()
        
        # Close all streams
        stream_ids = list(self.stream_manager.active_streams.keys())
        for stream_id in stream_ids:
            await self.stream_manager.close_stream(stream_id)
        
        logger.info("Streaming protocol shutdown complete")