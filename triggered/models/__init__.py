import asyncio
import logging
from typing import Dict

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
        def __init__(self, model_path: str):
            self._llm = Llama(model_path=model_path, n_threads=4)

        async def ainvoke(self, prompt: str, **kwargs):  # noqa: D401
            # llama-cpp is sync; offload to thread pool
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, self._llm, prompt)
            return response["choices"][0]["text"].strip()

except ImportError:  # noqa: WPS440
    LlamaCppModel = None  # type: ignore


_MODEL_CACHE: Dict[str, BaseModelAdapter] = {}


def get_model(name: str = "local") -> BaseModelAdapter:
    if name in _MODEL_CACHE:
        return _MODEL_CACHE[name]

    if name == "local":
        if LlamaCppModel is None:
            logger.warning(
                "llama-cpp-python not installed, falling back to DummyModel",
            )
            model = DummyModel()
        else:
            # For demo, attempt to load a placeholder gguf path,
            # in production the model path should be configurable.
            model = LlamaCppModel(model_path="phi-4-mini.gguf")
    else:
        # For unknown models we return DummyModel; extend as needed.
        model = DummyModel()

    _MODEL_CACHE[name] = model
    return model 