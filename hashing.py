#!/usr/bin/env python3
import bcrypt
import re
from typing import Optional, Tuple, List


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    :param password: The plaintext password to hash.
    :type password: str
    :return: The hashed password as a UTF-8 string.
    :rtype: str
    :raises ValueError: If the password is empty or not a string.
    """
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")
    # bcrypt.gensalt() generates a random salt.
    # The 'rounds' parameter controls the computational cost.
    # Higher rounds mean more security but also more CPU usage.
    # A value of 12 is a common starting point; adjust as needed.
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
    return hashed_password.decode("utf-8")  # Store as a UTF-8 string


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a stored hashed password.

    :param password: The plaintext password to verify.
    :type password: str
    :param hashed_password: The hashed password to compare against.
    :type hashed_password: str
    :return: True if the password matches, False otherwise.
    :rtype: bool
    :raises ValueError: If either argument is not a string or is empty.
    """
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")
    if not isinstance(hashed_password, str) or not hashed_password:
        raise ValueError("Hashed password must be a non-empty string.")
    # bcrypt.checkpw automatically extracts the salt from the hashed password
    # and re-hashes the plaintext password with that salt for comparison.
    hashed_password_bytes = hashed_password.encode("utf-8")
    password_bytes = password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)


# Function to validate email format
def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format using regex.

    :param email: The email address to validate.
    :type email: str
    :return: Tuple of (is_valid, message).
    :rtype: tuple[bool, str]
    """
    if not email or not email.strip():
        return False, "Email is required."

    # Basic email regex pattern
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email.strip()):
        return False, "Please enter a valid email address."

    return True, "Email is valid."


# Function to validate email against allowed list
def validate_email_allowed(
    email: str, allowed_emails: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """
    Validate email against allowed domains/addresses.

    :param email: The email address to validate.
    :type email: str
    :param allowed_emails: List of allowed emails or domains.
    :type allowed_emails: Optional[List[str]]
    :return: Tuple of (is_valid, message).
    :rtype: tuple[bool, str]
    """
    if not email or not email.strip():
        return False, "Email is required."

    # First check basic format
    format_valid, format_msg = validate_email(email)
    if not format_valid:
        return False, format_msg

    email = email.strip().lower()

    # If no allowed list provided, accept any valid email
    if not allowed_emails:
        return True, "Email is valid."

    # Check if exact email is in allowed list
    if email in [allowed.lower() for allowed in allowed_emails if "@" in allowed]:
        return True, "Email is authorized."

    # Check if email domain is in allowed domains
    email_domain = email.split("@")[1] if "@" in email else ""
    allowed_domains = [
        allowed.lower() for allowed in allowed_emails if "@" not in allowed
    ]

    if email_domain in allowed_domains:
        return True, "Email domain is authorized."

    return (
        False,
        f"Email not authorized. Please use an email from: {', '.join(allowed_emails[:3])}{'...' if len(allowed_emails) > 3 else ''}",
    )


# Function to validate username
def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate username requirements.

    :param username: The username to validate.
    :type username: str
    :return: Tuple of (is_valid, message).
    :rtype: tuple[bool, str]
    """
    if not username or not username.strip():
        return False, "Username is required."

    username = username.strip()

    # Check length
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."

    if len(username) > 20:
        return False, "Username must be no more than 20 characters long."

    # Check for valid characters (alphanumeric and underscore only)
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores."

    # Check that it doesn't start with a number
    if username[0].isdigit():
        return False, "Username cannot start with a number."

    return True, "Username is valid."


# Function to validate password complexity
def is_password_complex(password: str) -> Tuple[bool, str]:
    """
    Validate password complexity with updated requirements.

    :param password: The password to validate.
    :type password: str
    :return: Tuple of (is_valid, message).
    :rtype: tuple[bool, str]
    """
    if not password:
        return False, "Password is required."

    errors = []

    # Check length requirement (reduced from 10 to 8 for better UX)
    if len(password) < 8:
        errors.append("at least 8 characters long")

    # Check for uppercase letter
    if not re.search(r"[A-Z]", password):
        errors.append("at least one uppercase letter")

    # Check for lowercase letter
    if not re.search(r"[a-z]", password):
        errors.append("at least one lowercase letter")

    # Check for at least one digit
    if not re.search(r"\d", password):
        errors.append("at least one number")

    # Check for at least one symbol (non-alphanumeric character)
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("at least one special character (!@#$%^&*)")

    # If there are errors, return them
    if errors:
        return False, f"Password must contain: {', '.join(errors)}."

    # If all checks pass
    return True, "Password meets all requirements."


# --- Example Usage ---
if __name__ == "__main__":
    # 1. User provides a plaintext password
    plaintext_password = "mySuperSecretPassword123!"

    print(f"Original password: {plaintext_password}")

    # 2. Hash the password for storage
    # This process includes salt generation automatically
    stored_hash = hash_password(plaintext_password)
    print(f"Stored hash: {stored_hash}")

    # --- Later, when a user tries to log in ---

    # 3. User provides the password again for login
    login_attempt_password = "mySuperSecretPassword123!"

    # 4. Verify the provided password against the stored hash
    if verify_password(login_attempt_password, stored_hash):
        print("\nPassword verification successful! User logged in.")
    else:
        print("\nPassword verification failed. Incorrect password.")

    # Test with a wrong password
    wrong_password_attempt = "wrongPassword"
    if verify_password(wrong_password_attempt, stored_hash):
        print("This should not happen: Wrong password verified!")
    else:
        print(f"'{wrong_password_attempt}' failed verification, as expected.")

    # Demonstrate that different salts produce different hashes for the same password
    another_stored_hash = hash_password(plaintext_password)
    print(
        f"\nAnother hash for the same password (different salt): {another_stored_hash}"
    )
    print(
        f"Are the two hashes identical? {stored_hash == another_stored_hash}"
    )  # Should be False
