import re

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
    #return True, "Password is valid."

