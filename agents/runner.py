"""
ADK Runner Bridge for Streamlit

Provides a synchronous interface over the async ADK Runner.
"""
import asyncio
import inspect
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.orchestrator import root_agent


class InsightForgeRunner:
    """Synchronous wrapper around ADK Runner for Streamlit."""

    def __init__(self, session_id: str = "streamlit_user_001"):
        self.session_id = session_id
        self.user_id = "streamlit_user"
        self.app_name = "insightforge"
        self._session_service = InMemorySessionService()
        self._runner = Runner(
            agent=root_agent,
            app_name=self.app_name,
            session_service=self._session_service,
        )

    async def _ensure_session(self):
        """Create ADK session if it does not already exist."""
        try:
            result = self._session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=self.session_id,
                state={},
            )
            if inspect.isawaitable(result):
                await result
        except Exception as e:
            error_str = str(e).lower()
            if "already exists" not in error_str and "duplicate" not in error_str:
                print(f"Warning: Session creation issue: {e}")

    def run(self, prompt: str) -> str:
        """Execute multi-agent pipeline and return final text."""
        try:
            async def _arun():
                await self._ensure_session()

                content = types.Content(
                    role="user",
                    parts=[types.Part(text=prompt)]
                )

                responses = []
                async for event in self._runner.run_async(
                    user_id=self.user_id,
                    session_id=self.session_id,
                    new_message=content,
                ):
                    if event.is_final_response():
                        if event.content and event.content.parts:
                            for part in event.content.parts:
                                if part.text:
                                    responses.append(part.text)
                return responses

            responses = asyncio.run(_arun())
            return "\n".join(responses) if responses else "I could not generate a response. Please try again."

        except Exception as e:
            return f"Error processing request: {str(e)}"