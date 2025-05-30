import asyncio
import logging
from typing import Dict
import os
import httpx

logger = logging.getLogger(__name__)


class BaseModelAdapter:
    async def ainvoke(self, prompt: str, **kwargs):  # noqa: D401
        raise NotImplementedError


class DummyModel(BaseModelAdapter):
    async def ainvoke(self, prompt: str, **kwargs):  # noqa: D401
        await asyncio.sleep(0.1)
        logger.info("Dummy model received prompt: %s", prompt)
        return "yes"


try:
    from llama_cpp import Llama  # noqa: WPS433

    class LlamaCppModel(BaseModelAdapter):
        """Adapter that lazy-loads a GGUF model from Hugging Face Hub using
        the built-in *from_pretrained* helper so we don't have to download
        files manually in the install script.

        Parameters
        ----------
        repo_id: str
            HF repository slug (``owner/repo``) containing the GGUF file.
        filename: str
            Name of the GGUF file inside the repo.
        """

        def __init__(
            self,
            repo_id: str | None = None,
            filename: str | None = None,
            n_threads: int = 4,
        ) -> None:
            repo_id_env = os.getenv("LLM_REPO_ID")
            filename_env = os.getenv("LLM_FILENAME")

            candidate_repos = [
                repo_id_env,
                repo_id,
                "unsloth/Llama-3-8B-Instruct-GGUF"
            ]

            filename_default = (
                filename_env
                or filename
                or "llama-3-8b-instruct.Q4_K_M.gguf"
            )

            last_exc: Exception | None = None
            for rid in filter(None, candidate_repos):
                try:
                    logger.info(
                        "Attempting to load %s/%s",
                        rid,
                        filename_default,
                    )
                    self._llm = Llama.from_pretrained(
                        repo_id=rid,
                        filename=filename_default,
                        n_threads=n_threads,
                    )
                    break
                except Exception as exc:  # noqa: WPS420
                    logger.warning("Could not load %s: %s", rid, exc)
                    last_exc = exc
                    continue
            else:
                raise RuntimeError(
                    "Failed to fetch any GGUF model; "
                    "set LLM_REPO_ID / LLM_FILENAME",
                ) from last_exc

        async def ainvoke(self, prompt: str, **kwargs):  # noqa: D401
            # llama-cpp is sync; offload to thread pool
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, self._llm, prompt)
            return response["choices"][0]["text"].strip()

except ImportError:  # noqa: WPS440
    LlamaCppModel = None  # type: ignore


class OllamaModel(BaseModelAdapter):
    """Adapter that talks to a local Ollama server via HTTP."""

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("OLLAMA_MODEL", "phi4-mini")
        self.base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

    async def ainvoke(self, prompt: str, **kwargs):  # noqa: D401
        url = f"{self.base_url}/api/generate"
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")


# fallback detection
try:
    _test = os.getenv("DISABLE_OLLAMA")  # to optionally skip
    _OLLAMA_AVAILABLE = True if _test is None else False
except Exception:
    _OLLAMA_AVAILABLE = False


_MODEL_CACHE: Dict[str, BaseModelAdapter] = {}


def get_model(name: str = "local") -> BaseModelAdapter:
    if name in _MODEL_CACHE:
        return _MODEL_CACHE[name]

    if name == "local":
        try:
            if _OLLAMA_AVAILABLE:
                model = OllamaModel()
            elif LlamaCppModel is not None:
                model = LlamaCppModel()
            else:
                raise RuntimeError("No local LLM backend available")
        except Exception as exc:  # noqa: WPS420
            logger.error("Local model init failed: %s; using Dummy", exc)
            model = DummyModel()
    else:
        # For unknown models we return DummyModel; extend as needed.
        model = DummyModel()

    _MODEL_CACHE[name] = model
    return model 