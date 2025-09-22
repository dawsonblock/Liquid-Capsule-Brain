"""Enhanced input validation and sanitization."""

import html
import re
from typing import Any

from fastapi import HTTPException, status


class InputValidator:
    """Enhanced input validation and sanitization."""

    # Common dangerous patterns
    DANGEROUS_PATTERNS = [
        r"<script[^>]*>.*?</script>",  # Script tags
        r"javascript:",  # JavaScript URLs
        r"on\w+\s*=",  # Event handlers
        r"<iframe[^>]*>",  # Iframe tags
        r"<object[^>]*>",  # Object tags
        r"<embed[^>]*>",  # Embed tags
        r"<link[^>]*>",  # Link tags
        r"<meta[^>]*>",  # Meta tags
        r"<style[^>]*>.*?</style>",  # Style tags
        r"expression\s*\(",  # CSS expressions
        r"url\s*\(",  # CSS URLs
        r"@import",  # CSS imports
    ]

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+\w+\s*=\s*\w+)",
        r"(\b(OR|AND)\s+\'\s*=\s*\')",
        r'(\b(OR|AND)\s+"\s*=\s*")',
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+\s*--)",
        r"(\b(OR|AND)\s+\w+\s*=\s*\w+\s*--)",
        r"(\b(OR|AND)\s+\'\s*=\s*\'\s*--)",
        r'(\b(OR|AND)\s+"\s*=\s*"\s*--)',
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+\s*#)",
        r"(\b(OR|AND)\s+\w+\s*=\s*\w+\s*#)",
        r"(\b(OR|AND)\s+\'\s*=\s*\'\s*#)",
        r'(\b(OR|AND)\s+"\s*=\s*"\s*#)',
    ]

    @classmethod
    def sanitize_string(cls, value: str, max_length: int | None = None) -> str:
        """Sanitize a string input.

        Args:
            value: Input string to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string

        Raises:
            HTTPException: If input is invalid
        """
        if not isinstance(value, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input type"
            )

        # Check length
        if max_length and len(value) > max_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Input too long. Maximum length: {max_length}",
            )

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Input contains potentially dangerous content",
                )

        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Input contains potentially malicious SQL patterns",
                )

        # HTML escape the content
        sanitized = html.escape(value)

        # Remove any remaining HTML tags
        sanitized = re.sub(r"<[^>]+>", "", sanitized)

        return sanitized.strip()

    @classmethod
    def validate_filename(cls, filename: str) -> str:
        """Validate and sanitize filename.

        Args:
            filename: Filename to validate

        Returns:
            Sanitized filename

        Raises:
            HTTPException: If filename is invalid
        """
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Filename cannot be empty"
            )

        # Remove path traversal attempts
        filename = filename.replace("..", "").replace("/", "").replace("\\", "")

        # Check for dangerous characters
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*"]
        for char in dangerous_chars:
            if char in filename:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Filename contains invalid character: {char}",
                )

        # Check length
        if len(filename) > 255:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename too long")

        return filename

    @classmethod
    def validate_question(cls, question: str) -> str:
        """Validate and sanitize question input.

        Args:
            question: Question to validate

        Returns:
            Sanitized question

        Raises:
            HTTPException: If question is invalid
        """
        if not question or not question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Question cannot be empty"
            )

        # Sanitize the question
        sanitized = cls.sanitize_string(question, max_length=1000)

        # Check minimum length
        if len(sanitized) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Question too short"
            )

        return sanitized

    @classmethod
    def validate_json_input(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Validate JSON input data.

        Args:
            data: JSON data to validate

        Returns:
            Sanitized JSON data

        Raises:
            HTTPException: If data is invalid
        """
        if not isinstance(data, dict):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON data")

        # Check for excessive nesting
        def check_depth(obj: Any, depth: int = 0) -> None:
            if depth > 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="JSON data too deeply nested"
                )
            if isinstance(obj, dict):
                for value in obj.values():
                    check_depth(value, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    check_depth(item, depth + 1)

        check_depth(data)

        # Sanitize string values
        def sanitize_value(value: Any) -> Any:
            if isinstance(value, str):
                return cls.sanitize_string(value)
            elif isinstance(value, dict):
                return {k: sanitize_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [sanitize_value(item) for item in value]
            else:
                return value

        return sanitize_value(data)
