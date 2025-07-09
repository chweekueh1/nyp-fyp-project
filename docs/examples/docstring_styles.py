#!/usr/bin/env python3
"""
Example module demonstrating both Google and Sphinx style docstrings.

This module shows how to use both Google-style and Sphinx-style docstrings
in the same codebase, and how doc comments are processed.
"""

from typing import Dict


def google_style_function(param1: str, param2: int = 10) -> Dict[str, str]:
    """
    Example function using Google-style docstring.

    This function demonstrates the Google-style docstring format with
    proper parameter and return type documentation.

    Args:
        param1: A string parameter that describes something important.
        param2: An integer parameter with a default value of 10.
            This parameter controls some behavior.

    Returns:
        A dictionary containing the results of the operation.
        The dictionary has string keys and string values.

    Raises:
        ValueError: If param1 is empty or param2 is negative.
        TypeError: If param1 is not a string.

    Example:
        >>> result = google_style_function("test", 5)
        >>> print(result)
        {'status': 'success', 'message': 'test processed with value 5'}

    Note:
        This function is just an example and doesn't do anything useful.

    See Also:
        sphinx_style_function: The Sphinx-style equivalent.
    """
    if not isinstance(param1, str):
        raise TypeError("param1 must be a string")

    if not param1:
        raise ValueError("param1 cannot be empty")

    if param2 < 0:
        raise ValueError("param2 cannot be negative")

    return {"status": "success", "message": f"{param1} processed with value {param2}"}


def sphinx_style_function(param1: str, param2: int = 10) -> Dict[str, str]:
    """
    Example function using Sphinx-style docstring.

    This function demonstrates the Sphinx-style docstring format with
    proper parameter and return type documentation.

    :param param1: A string parameter that describes something important.
    :type param1: str
    :param param2: An integer parameter with a default value of 10.
                   This parameter controls some behavior.
    :type param2: int
    :return: A dictionary containing the results of the operation.
             The dictionary has string keys and string values.
    :rtype: Dict[str, str]
    :raises ValueError: If param1 is empty or param2 is negative.
    :raises TypeError: If param1 is not a string.

    :Example:
        >>> result = sphinx_style_function("test", 5)
        >>> print(result)
        {'status': 'success', 'message': 'test processed with value 5'}

    :Note:
        This function is just an example and doesn't do anything useful.

    :See Also:
        google_style_function: The Google-style equivalent.
    """
    if not isinstance(param1, str):
        raise TypeError("param1 must be a string")

    if not param1:
        raise ValueError("param1 cannot be empty")

    if param2 < 0:
        raise ValueError("param2 cannot be negative")

    return {"status": "success", "message": f"{param1} processed with value {param2}"}


def function_with_doc_comments(param1: str, param2: int = 10) -> Dict[str, str]:
    """
    Example function with doc comments in the docstring.

    This function shows how doc comments (lines starting with #) are
    processed and integrated into the documentation.

    # This is a doc comment that should be processed
    # It provides additional context about the function
    # Multiple lines of comments are supported

    Args:
        param1: A string parameter.
        param2: An integer parameter.

    Returns:
        A dictionary with results.

    # Another doc comment for additional notes
    # These comments will be included in the documentation
    """
    # This is a regular code comment (not a doc comment)
    # It won't be included in the documentation

    return {
        "status": "success",
        "message": f"{param1} processed with value {param2}",
        "doc_comments_processed": True,
    }


class ExampleClass:
    """
    Example class demonstrating both docstring styles.

    This class shows how to use both Google and Sphinx style docstrings
    for class documentation, methods, and properties.

    Args:
        name: The name for this instance.
        value: Initial value for this instance.

    Attributes:
        name (str): The name of the instance.
        value (int): A numeric value associated with the instance.
        config (Dict[str, Any]): Configuration dictionary.
    """

    def __init__(self, name: str, value: int = 0):
        self.name = name
        self.value = value
        self.config = {}

    def google_style_method(self, param: str) -> str:
        """
        Example method using Google-style docstring.

        Args:
            param: A string parameter for the method.

        Returns:
            A string result from the method.

        Raises:
            ValueError: If param is empty.
        """
        if not param:
            raise ValueError("param cannot be empty")

        return f"{self.name}: {param}"

    def sphinx_style_method(self, param: str) -> str:
        """
        Example method using Sphinx-style docstring.

        :param param: A string parameter for the method.
        :type param: str
        :return: A string result from the method.
        :rtype: str
        :raises ValueError: If param is empty.
        """
        if not param:
            raise ValueError("param cannot be empty")

        return f"{self.name}: {param}"

    @property
    def computed_value(self) -> int:
        """
        Example property with docstring.

        Returns:
            The computed value based on the instance's value.
        """
        return self.value * 2

    def method_with_doc_comments(self, param: str) -> str:
        """
        Example method with doc comments.

        # This method demonstrates doc comment processing
        # Multiple lines of doc comments are supported
        # They will be included in the documentation

        Args:
            param: A string parameter.

        Returns:
            A processed string result.

        # Additional notes about the method behavior
        # These comments will be processed and included
        """
        return f"{self.name}: {param} (with doc comments)"


def numpy_style_function(param1: str, param2: int = 10) -> Dict[str, str]:
    """
    Example function using NumPy-style docstring.

    Parameters
    ----------
    param1 : str
        A string parameter that describes something important.
    param2 : int, optional
        An integer parameter with a default value of 10.
        This parameter controls some behavior.

    Returns
    -------
    Dict[str, str]
        A dictionary containing the results of the operation.
        The dictionary has string keys and string values.

    Raises
    ------
    ValueError
        If param1 is empty or param2 is negative.
    TypeError
        If param1 is not a string.

    Examples
    --------
    >>> result = numpy_style_function("test", 5)
    >>> print(result)
    {'status': 'success', 'message': 'test processed with value 5'}

    Notes
    -----
    This function is just an example and doesn't do anything useful.

    See Also
    --------
    google_style_function : The Google-style equivalent.
    sphinx_style_function : The Sphinx-style equivalent.
    """
    if not isinstance(param1, str):
        raise TypeError("param1 must be a string")

    if not param1:
        raise ValueError("param1 cannot be empty")

    if param2 < 0:
        raise ValueError("param2 cannot be negative")

    return {"status": "success", "message": f"{param1} processed with value {param2}"}
