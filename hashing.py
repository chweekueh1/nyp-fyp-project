import bcrypt
import re

def hash_password(password):
    """
    Hashes a plaintext password using bcrypt.
    Generates a new salt for each hash and embeds it in the returned hash.
    """
    # bcrypt.gensalt() generates a random salt.
    # The 'rounds' parameter controls the computational cost.
    # Higher rounds mean more security but also more CPU usage.
    # A value of 12 is a common starting point; adjust as needed.
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
    return hashed_password.decode('utf-8') # Store as a UTF-8 string

def verify_password(password, hashed_password):
    """
    Verifies a plaintext password against a stored hashed password.
    """
    # bcrypt.checkpw automatically extracts the salt from the hashed password
    # and re-hashes the plaintext password with that salt for comparison.
    hashed_password = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
    password = password.encode('utf-8') if isinstance(password, str) else password
    print(f"Against stored hash: {hashed_password.decode('utf-8') if isinstance(hashed_password, bytes) else hashed_password}")
    return bcrypt.checkpw(password, hashed_password)

# Function to validate password complexity
def is_password_complex(password):
    # Check length requirement
    if len(password) < 10:
        return False, "Password must be at least 10 characters long."
    
    # Check for at least one letter
    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least one letter."
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit."
    
    # Check for at least one symbol (non-alphanumeric character)
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one symbol (!@#$%^&*(),.?\":{}|<>)."
    
    # If all checks pass
    return True, "Password is valid."

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
    print(f"\nAnother hash for the same password (different salt): {another_stored_hash}")
    print(f"Are the two hashes identical? {stored_hash == another_stored_hash}") # Should be False

