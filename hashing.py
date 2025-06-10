import bcrypt

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
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

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

