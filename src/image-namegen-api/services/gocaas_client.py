"""
A module to call LLM endpoints asynchronously.
"""
import logging
import os
import sys
import httpx
from typing import Any, Dict, List

sys.path.append(os.getcwd())

from authentications.jwt_token_client import get_jwt_token
from common.utils import configure_logging, get_caas_url, get_environment, read_yaml_file_to_dict
from services.prompts import ROLE_ASSIGNER
from services.prompts import PROMPTS
import base64
logger = configure_logging("LLM CALLER")
HTTPX_LOGGER = logging.getLogger("httpx")
HTTPX_LOGGER.setLevel(logging.WARNING)

PATH_TO_CONFIG = "./config.yaml"
CONFIG = read_yaml_file_to_dict(PATH_TO_CONFIG).get("CAAS")

RETRY_COUNT = 2

ENV = os.getenv("aws_env", "local")


class GoCaaS:
    """
    A class to call GoCaaS endpoints asynchronously.
    """
    
        
    def __init__(self, model_name: str, token: str, image_path: str = None, config: Dict[str, Any] = CONFIG):
        self.model_name = model_name
        self.config = config
        self.token = token
        self.header = {}
        self.data = {}
        self.image = self._encode_image(image_path) if image_path else None
        self._config_builder()
        self._authentication_header()
    
    def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
        
    def _authentication_header(self) -> None:
        """
        Builds the authentication header for the request.
        """
        self.header = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"sso-jwt {self.token}",
        }

    def _config_builder(self) -> None:
        """
        Builds the configuration dictionary for the model.
        """
        model_config = self.config.get(self.model_name)
        messages = [
            {
                "role": "system",
                "content": model_config.get("role_assigner", ROLE_ASSIGNER),
            }
        ]
        
        # Add image message if image exists
        if self.image:
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{self.image}"
                        }
                    }
                ]
            })
        self.data = {
            "provider": model_config.get("provider"),
            "providerOptions": {
                "max_tokens": model_config.get("max_tokens"),
                "temperature": model_config.get("temperature"),
                "top_p": model_config.get("top_p"),
                "frequency_penalty": model_config.get("frequency_penalty"),
                "presence_penalty": model_config.get("presence_penalty"),
                "model": model_config.get("model"),
                "messages": messages
            }
        }
        

    async def call(self, query: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        self._authentication_header()
        retry_count = self.config.get(self.model_name).get("retry_count", RETRY_COUNT)
        
        # Update messages with conversation history
        if conversation_history:
            self.data["providerOptions"]["messages"].extend(conversation_history)
        
        # Add the current query
        self.data["providerOptions"]["messages"].append({
            "role": "user",
            "content": query
        })
        
        data = {
            "prompt": query,
            **self.data,
        }
        print(data)
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(retry_count):
                try:
                    response = await client.post(
                        get_caas_url(get_environment()), json=data, headers=self.header
                    )
                    if response.status_code in [200, 201]:
                        result = response.json()
                        return result
                except Exception as e:
                    if attempt == retry_count - 1:
                        logger.error(f"Failed to call GoCaaS endpoint: {e}")
                        return {}
                    logger.warning(f"Retrying GoCaaS call. Attempt {attempt + 1}")
                    await asyncio.sleep(2 ** attempt)

    async def health_check(self) -> bool:
        """
        Check the health of the GoCaaS service asynchronously.

        Returns:
            True if the service is healthy, False otherwise.
        """
        self._authentication_header()
        data = {
            "prompt": "Hi how are you?",
            **self.data,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                get_caas_url(get_environment()), json=data, headers=self.header
            )

            if response.status_code in [200, 201]:
                return True

            raise ValueError(
                f"Invalid status code: {response.status_code}. Message: {response.text or 'Unable to parse error message'}"
            )


if __name__ == "__main__":
    import asyncio

    
   # prompt = PROMPTS["001"]["prompt"]


    async def main():
        llm = GoCaaS("gpt-4o-mini", token=get_jwt_token().token)
        try:
            test = """
Ask 3 interesting questions, one question at a time, with 4 options a, b, c, d, to guess what domain names that users may interested.  

The questions are designed to build to discover user's profile to help us make domain recommendations. You may want to discover how they will use domain names (for self-introduction,  
for business purposes, for leisure, or something else?).
 
You should be funny and provide some senarios, try to avoid asking directly. 
The response should be in json format with key question and options like {"question": "...", "options": "{...}" }
                  
After the final question, you need to give 20 domain suggetions and the reason why you think they may interested in these domains. Return a list of json object like [{"guess": "pizza.com", "reason": "because you are a developer", "price": 20.9}, ...]. 

Please ONLY ask one question at a time. 

You should only provide the domain suggestions after the user answering the three questions.
"""
            caas_response = await llm.call(test, [])
            print(caas_response["data"]["value"])
        except ValueError as e:
            logger.error(e)

    asyncio.run(main())
