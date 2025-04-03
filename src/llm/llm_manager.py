from pyexpat import model
from typing import List, Union
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, AIMessage
from langchain_openai import ChatOpenAI
from loguru import logger


load_dotenv()

# class AnsweringMode(Enum):
#     NORMAL = "normal"  # Mode where answers are expected to be truthful
#     STRATEGIC = "strategic"  # Mode where answers are optimized to avoid knockout questions

class AIAdapter:
    """
    Adapter to interact with the LLM via the TensorZero gateway's
    OpenAI-compatible endpoint.
    """
    def __init__(self, config: dict, api_key: str):
        
        tensorzero_gateway_url = "http://localhost:3000/openai/v1"
        logger.info(f"Initializing AIAdapter with ChatOpenAI pointing to TensorZero gateway: {tensorzero_gateway_url}")
        self.model = ChatOpenAI(
            base_url=tensorzero_gateway_url,
            temperature=0.4,
            model="tensorzero::function_name::generate_haiku"
        )
        logger.info(f"ChatOpenAI model initialized for TensorZero gateway.")


    def invoke(self, prompt: Union[str, List[BaseMessage]]) -> BaseMessage:
        """Invokes the TensorZero gateway via ChatOpenAI."""
        logger.debug(f"Invoking TensorZero gateway with prompt type: {type(prompt)}")
        try:
            response = self.model.invoke(prompt)
            logger.debug(f"Received response from TensorZero gateway.")
            return response
        except Exception as e:
            logger.error(f"Error invoking TensorZero gateway: {e}")
            # Depending on desired behavior, re-raise or return an error indicator
            raise # Re-raise the exception for now


class TensorZeroChatModelWrapper:
    """
    A simplified wrapper around the ChatOpenAI model configured for TensorZero.
    Removes custom retry and logging logic, assuming TensorZero handles it.
    """
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        logger.debug(f"TensorZeroChatModelWrapper initialized with LLM: {llm}")

    def __call__(self, messages: List[BaseMessage]) -> BaseMessage:
        """Invokes the underlying ChatOpenAI model."""
        logger.debug(f"Wrapper invoking LLM with {messages} messages.")
        try:
            # Directly invoke the model, Langchain/TensorZero handles retries etc.
            reply = self.llm.invoke(messages)

            # Basic check for expected return type
            if not isinstance(reply, AIMessage):
                 logger.warning(f"Unexpected reply type from LLM: {type(reply)}. Expected AIMessage.")
                 # Attempt basic conversion if possible, otherwise raise error
                 if isinstance(reply, str):
                     return AIMessage(content=reply)
                 else:
                     # Cannot reliably proceed
                     raise TypeError(f"Cannot handle LLM reply type: {type(reply)}")

            return reply

        except Exception as e:
            logger.error(f"Error during LLM invocation within wrapper: {str(e)}")
            # Re-raise the exception to be handled by the caller
            raise

