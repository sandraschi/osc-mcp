"""LLM discovery API - probe local Ollama instance."""

import asyncio
import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["llm"], prefix="/llm")


@router.get("/discover")
async def discover_llm():
    """Probe localhost:11434 for a running Ollama instance."""
    provider_status = {"ollama": {"status": "not_detected", "base_url": "http://localhost:11434"}}
    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", 11434)
        writer.write(b"GET /api/tags HTTP/1.0\r\nHost: localhost\r\n\r\n")
        await writer.drain()
        response = await asyncio.wait_for(reader.read(4096), timeout=3.0)
        writer.close()
        await writer.wait_closed()
        if b"200 OK" in response.split(b"\r\n")[0]:
            provider_status["ollama"]["status"] = "detected"
            provider_status["ollama"]["version"] = "ollama"
        else:
            provider_status["ollama"]["status"] = "unexpected_response"
    except (ConnectionRefusedError, OSError):
        provider_status["ollama"]["status"] = "not_detected"
    except TimeoutError:
        provider_status["ollama"]["status"] = "timeout"
    except Exception as e:
        logger.warning("Ollama probe error: %s", e, exc_info=True)
        provider_status["ollama"]["status"] = "error"
        provider_status["ollama"]["error"] = str(e)

    return {"providers": provider_status}
