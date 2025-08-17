import openai
import os
import asyncio
from dotenv import load_dotenv  # Import load_dotenv


async def sanity_check_openai_key(api_key: str = None) -> tuple[bool, str]:
    """
    Performs a sanity check on an OpenAI API key by attempting to list models
    and then sending a test chat completion request.

    Args:
        api_key: The OpenAI API key to check. If None, it attempts to load from
                 the OPENAI_API_KEY environment variable.

    Returns:
        A tuple containing:
        - bool: True if the key is valid and can make a request, False otherwise.
        - str: A message indicating the result (success or error details,
               including the test response if successful).
    """
    # Load environment variables from .env file
    load_dotenv()

    # If api_key is not provided, try to get it from the environment variable
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return (
            False,
            "API key is empty or not found in environment variables. Please provide a valid OpenAI API key or set OPENAI_API_KEY in your .env file. ❌",
        )

    client = openai.AsyncOpenAI(api_key=api_key)

    try:
        # Step 1: Attempt a low-cost API call, like listing models
        # This verifies basic authentication and connectivity.
        await client.models.list()

        # Step 2: Send a simple chat completion request
        # This verifies the key works for actual content generation.
        test_message = "Say 'Hello!' in a friendly tone."
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",  # Using a common, cost-effective model for the test
            messages=[{"role": "user", "content": test_message}],
            max_tokens=10,  # Keep the response short for efficiency
        )

        # Extract the response content
        if (
            response.choices
            and response.choices[0].message
            and response.choices[0].message.content
        ):
            test_response_content = response.choices[0].message.content.strip()
            return (
                True,
                f"OpenAI API key is valid and authenticated successfully! ✅\nTest request successful. Model responded: '{test_response_content}'",
            )
        else:
            return (
                False,
                "OpenAI API key is valid, but test chat completion returned an unexpected empty response. ⚠️",
            )

    except openai.AuthenticationError:
        return False, "OpenAI API key is invalid or expired. Please check your key. ❌"
    except openai.APIConnectionError as e:
        return (
            False,
            f"Could not connect to OpenAI API: {e}. Check your internet connection or proxy settings. ⚠️",
        )
    except openai.RateLimitError:
        return False, "OpenAI API rate limit exceeded. Please wait and try again. ⏳"
    except openai.APITimeoutError:
        return (
            False,
            "OpenAI API request timed out. The server took too long to respond. ⏰",
        )
    except openai.OpenAIError as e:
        # Catch any other specific OpenAI API errors
        return (
            False,
            f"An OpenAI API error occurred: {e}. This might indicate issues with permissions or model access. ⚠️",
        )
    except Exception as e:
        # Catch any other unexpected errors
        return False, f"An unexpected error occurred: {e}. 🐛"


async def main():
    # --- Example Usage ---

    # When calling sanity_check_openai_key() without an argument, it will
    # automatically try to load OPENAI_API_KEY from your .env file.
    print("--- Testing with key loaded from .env (or environment) ---")
    is_valid, message = await sanity_check_openai_key()
    print(f"Result: {is_valid}\nMessage: {message}\n")


if __name__ == "__main__":
    asyncio.run(main())
