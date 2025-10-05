"""
Input Validation and Size Limits for FastAPI
Comprehensive validation system for messages, uploads, and API inputs
"""

import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import magic
from fastapi import HTTPException, Request, UploadFile
from pydantic import BaseModel, Field, validator
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ValidationErrorType(str, Enum):
    """Types of validation errors"""

    SIZE_LIMIT_EXCEEDED = "size_limit_exceeded"
    INVALID_FORMAT = "invalid_format"
    FORBIDDEN_CONTENT = "forbidden_content"
    MISSING_REQUIRED = "missing_required"
    INVALID_FILE_TYPE = "invalid_file_type"
    MALICIOUS_CONTENT = "malicious_content"


@dataclass
class ValidationLimits:
    """Configuration for validation limits"""

    # Message limits
    max_message_length: int = 10000  # 10KB for messages
    max_messages_per_conversation: int = 1000

    # File upload limits
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    max_files_per_request: int = 10
    max_filename_length: int = 255

    # JSON payload limits
    max_json_size: int = 10 * 1024 * 1024  # 10MB
    max_array_length: int = 1000
    max_object_depth: int = 10

    # String field limits
    max_string_length: int = 5000
    max_description_length: int = 2000
    max_name_length: int = 100
    max_url_length: int = 2048

    # Workflow limits
    max_workflow_steps: int = 50
    max_workflow_depth: int = 10

    # Agent limits
    max_agent_capabilities: int = 20
    max_agent_settings_size: int = 5000


class ValidationConfig:
    """Validation configuration based on environment"""

    @staticmethod
    def get_limits() -> ValidationLimits:
        """Get validation limits based on environment"""
        environment = os.getenv("ENVIRONMENT", "development").lower()

        if environment == "production":
            return ValidationLimits(
                max_message_length=8000,  # Stricter in production
                max_file_size=25 * 1024 * 1024,  # 25MB in production
                max_json_size=5 * 1024 * 1024,  # 5MB in production
            )
        elif environment == "staging":
            return ValidationLimits(
                max_message_length=9000,
                max_file_size=40 * 1024 * 1024,  # 40MB in staging
                max_json_size=8 * 1024 * 1024,  # 8MB in staging
            )
        else:
            # Development - more relaxed limits
            return ValidationLimits()

    @staticmethod
    def get_allowed_file_types() -> set[str]:
        """Get allowed file types based on environment"""
        base_types = {
            # Documents
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "text/plain",
            "text/csv",
            "application/json",
            "application/xml",
            "text/xml",
            # Images
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/svg+xml",
            # Archives
            "application/zip",
            "application/x-tar",
            "application/gzip",
            # Code files
            "text/x-python",
            "application/javascript",
            "text/html",
            "text/css",
        }

        environment = os.getenv("ENVIRONMENT", "development").lower()
        if environment == "production":
            # Remove potentially risky types in production
            production_blocked = {
                "application/zip",
                "application/x-tar",
                "application/gzip",
                "text/html",
                "application/javascript",
                "image/svg+xml",
            }
            return base_types - production_blocked

        return base_types

    @staticmethod
    def get_dangerous_extensions() -> set[str]:
        """Get dangerous file extensions to block"""
        return {
            # Executables
            ".exe",
            ".bat",
            ".cmd",
            ".com",
            ".scr",
            ".pif",
            ".msi",
            ".msp",
            ".dll",
            ".so",
            ".dylib",
            # Scripts
            ".vbs",
            ".vba",
            ".js",
            ".jse",
            ".wsf",
            ".wsh",
            ".ps1",
            ".psm1",
            ".psd1",
            ".ps1xml",
            ".psc1",
            ".sh",
            ".bash",
            ".zsh",
            ".fish",
            # Archives that can contain executables
            ".rar",
            ".7z",
            ".cab",
            ".iso",
            ".dmg",
            # Office macros
            ".xlsm",
            ".xlsb",
            ".xltm",
            ".xla",
            ".xlam",
            ".pptm",
            ".potm",
            ".ppam",
            ".docm",
            ".dotm",
        }


class MessageValidator:
    """Validator for chat messages and content"""

    def __init__(self, limits: ValidationLimits):
        self.limits = limits
        self.forbidden_patterns = self._load_forbidden_patterns()

    def _load_forbidden_patterns(self) -> list[re.Pattern]:
        """Load patterns for forbidden content"""
        patterns = [
            # Potential injection attempts
            re.compile(r"<script[^>]*>", re.IGNORECASE),
            re.compile(r"javascript:", re.IGNORECASE),
            re.compile(r"data:.*script", re.IGNORECASE),
            re.compile(r"vbscript:", re.IGNORECASE),
            # SQL injection patterns
            re.compile(
                r"\b(union|select|insert|delete|update|drop|create|alter)\s+", re.IGNORECASE
            ),
            re.compile(r"[\'\"]\s*;\s*\w+", re.IGNORECASE),
            # Command injection
            re.compile(r"[;&|`$(){}]", re.IGNORECASE),
            # Path traversal
            re.compile(r"\.\./|\.\.\\\|%2e%2e%2f|%2e%2e\\", re.IGNORECASE),
        ]
        return patterns

    def validate_message(self, message: str, field_name: str = "message") -> str:
        """Validate a message string"""
        if not message:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "validation_error",
                    "type": ValidationErrorType.MISSING_REQUIRED,
                    "field": field_name,
                    "message": f"{field_name} cannot be empty",
                },
            )

        # Check length
        if len(message) > self.limits.max_message_length:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": "validation_error",
                    "type": ValidationErrorType.SIZE_LIMIT_EXCEEDED,
                    "field": field_name,
                    "message": f"{field_name} exceeds maximum length of {self.limits.max_message_length} characters",
                    "current_length": len(message),
                    "max_length": self.limits.max_message_length,
                },
            )

        # Check for forbidden content
        for pattern in self.forbidden_patterns:
            if pattern.search(message):
                logger.warning(f"Forbidden content detected in {field_name}: {pattern.pattern}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "validation_error",
                        "type": ValidationErrorType.FORBIDDEN_CONTENT,
                        "field": field_name,
                        "message": f"{field_name} contains forbidden content",
                    },
                )

        return message.strip()

    def validate_string_field(
        self, value: str, field_name: str, max_length: int | None = None
    ) -> str:
        """Validate a general string field"""
        if max_length is None:
            max_length = self.limits.max_string_length

        if len(value) > max_length:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": "validation_error",
                    "type": ValidationErrorType.SIZE_LIMIT_EXCEEDED,
                    "field": field_name,
                    "message": f"{field_name} exceeds maximum length of {max_length} characters",
                    "current_length": len(value),
                    "max_length": max_length,
                },
            )

        return value.strip()


class FileValidator:
    """Validator for file uploads"""

    def __init__(self, limits: ValidationLimits):
        self.limits = limits
        self.allowed_types = ValidationConfig.get_allowed_file_types()
        self.dangerous_extensions = ValidationConfig.get_dangerous_extensions()

    async def validate_file(self, file: UploadFile, field_name: str = "file") -> UploadFile:
        """Validate an uploaded file"""
        # Check if file is provided
        if not file or not file.filename:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "validation_error",
                    "type": ValidationErrorType.MISSING_REQUIRED,
                    "field": field_name,
                    "message": "File is required",
                },
            )

        # Validate filename
        self._validate_filename(file.filename, field_name)

        # Read file content for validation
        content = await file.read()
        await file.seek(0)  # Reset file pointer

        # Check file size
        if len(content) > self.limits.max_file_size:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": "validation_error",
                    "type": ValidationErrorType.SIZE_LIMIT_EXCEEDED,
                    "field": field_name,
                    "message": f"File exceeds maximum size of {self.limits.max_file_size} bytes",
                    "current_size": len(content),
                    "max_size": self.limits.max_file_size,
                },
            )

        # Validate file type
        self._validate_file_type(content, file.filename, field_name)

        # Check for malicious content
        self._scan_for_malicious_content(content, file.filename, field_name)

        return file

    def _validate_filename(self, filename: str, field_name: str) -> None:
        """Validate filename"""
        if len(filename) > self.limits.max_filename_length:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "validation_error",
                    "type": ValidationErrorType.SIZE_LIMIT_EXCEEDED,
                    "field": field_name,
                    "message": f"Filename exceeds maximum length of {self.limits.max_filename_length} characters",
                },
            )

        # Check for dangerous extensions
        file_ext = Path(filename).suffix.lower()
        if file_ext in self.dangerous_extensions:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "validation_error",
                    "type": ValidationErrorType.INVALID_FILE_TYPE,
                    "field": field_name,
                    "message": f"File type '{file_ext}' is not allowed",
                },
            )

        # Check for path traversal in filename
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "validation_error",
                    "type": ValidationErrorType.MALICIOUS_CONTENT,
                    "field": field_name,
                    "message": "Filename contains invalid characters",
                },
            )

    def _validate_file_type(self, content: bytes, filename: str, field_name: str) -> None:
        """Validate file type using magic numbers"""
        try:
            # Detect MIME type from content
            mime_type = magic.from_buffer(content, mime=True)

            if mime_type not in self.allowed_types:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "validation_error",
                        "type": ValidationErrorType.INVALID_FILE_TYPE,
                        "field": field_name,
                        "message": f"File type '{mime_type}' is not allowed",
                        "detected_type": mime_type,
                        "allowed_types": list(self.allowed_types),
                    },
                )
        except Exception as e:
            logger.warning(f"Could not detect file type for {filename}: {e}")
            # Fallback to extension-based validation
            file_ext = Path(filename).suffix.lower()
            if file_ext in self.dangerous_extensions:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "validation_error",
                        "type": ValidationErrorType.INVALID_FILE_TYPE,
                        "field": field_name,
                        "message": f"File type '{file_ext}' is not allowed",
                    },
                )

    def _scan_for_malicious_content(self, content: bytes, filename: str, field_name: str) -> None:
        """Basic scan for malicious content"""
        # Check for executable signatures
        executable_signatures = [
            b"MZ",  # PE executable
            b"\x7fELF",  # ELF executable
            b"\xfe\xed\xfa",  # Mach-O executable
            b"PK\x03\x04",  # ZIP (could contain executables)
        ]

        for sig in executable_signatures:
            if content.startswith(sig):
                logger.warning(f"Potential executable detected: {filename}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "validation_error",
                        "type": ValidationErrorType.MALICIOUS_CONTENT,
                        "field": field_name,
                        "message": "File appears to contain executable content",
                    },
                )

        # Check for embedded scripts in text files
        if filename.endswith((".txt", ".csv", ".json", ".xml")):
            content_str = content.decode("utf-8", errors="ignore").lower()
            if any(script in content_str for script in ["<script", "javascript:", "vbscript:"]):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "validation_error",
                        "type": ValidationErrorType.MALICIOUS_CONTENT,
                        "field": field_name,
                        "message": "File contains potentially malicious script content",
                    },
                )


class JSONValidator:
    """Validator for JSON payloads"""

    def __init__(self, limits: ValidationLimits):
        self.limits = limits

    def validate_json_size(self, data: Any, field_name: str = "payload") -> Any:
        """Validate JSON payload size and structure"""
        import json

        # Serialize to check size
        try:
            json_str = json.dumps(data)
            if len(json_str.encode("utf-8")) > self.limits.max_json_size:
                raise HTTPException(
                    status_code=413,
                    detail={
                        "error": "validation_error",
                        "type": ValidationErrorType.SIZE_LIMIT_EXCEEDED,
                        "field": field_name,
                        "message": f"JSON payload exceeds maximum size of {self.limits.max_json_size} bytes",
                    },
                )
        except (TypeError, ValueError) as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "validation_error",
                    "type": ValidationErrorType.INVALID_FORMAT,
                    "field": field_name,
                    "message": f"Invalid JSON data: {str(e)}",
                },
            )

        # Check array lengths and object depth
        self._validate_structure(data, field_name)

        return data

    def _validate_structure(self, data: Any, field_name: str, depth: int = 0) -> None:
        """Recursively validate JSON structure"""
        if depth > self.limits.max_object_depth:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "validation_error",
                    "type": ValidationErrorType.SIZE_LIMIT_EXCEEDED,
                    "field": field_name,
                    "message": f"JSON object depth exceeds maximum of {self.limits.max_object_depth}",
                },
            )

        if isinstance(data, list):
            if len(data) > self.limits.max_array_length:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "validation_error",
                        "type": ValidationErrorType.SIZE_LIMIT_EXCEEDED,
                        "field": field_name,
                        "message": f"Array length exceeds maximum of {self.limits.max_array_length}",
                    },
                )

            for item in data:
                self._validate_structure(item, field_name, depth + 1)

        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(key, str) and len(key) > self.limits.max_string_length:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "validation_error",
                            "type": ValidationErrorType.SIZE_LIMIT_EXCEEDED,
                            "field": field_name,
                            "message": f"JSON key length exceeds maximum of {self.limits.max_string_length}",
                        },
                    )
                self._validate_structure(value, field_name, depth + 1)


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request size"""

    def __init__(self, app, max_size: int = 50 * 1024 * 1024):  # 50MB default
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        # Check Content-Length header
        content_length = request.headers.get("content-length")
        if content_length:
            content_length = int(content_length)
            if content_length > self.max_size:
                return HTTPException(
                    status_code=413,
                    detail={
                        "error": "validation_error",
                        "type": ValidationErrorType.SIZE_LIMIT_EXCEEDED,
                        "message": f"Request body too large: {content_length} bytes, max: {self.max_size} bytes",
                    },
                ).response

        response = await call_next(request)
        return response


# Global validators instance
_limits = ValidationConfig.get_limits()
message_validator = MessageValidator(_limits)
file_validator = FileValidator(_limits)
json_validator = JSONValidator(_limits)


# Validation dependency functions
def validate_message_input(message: str) -> str:
    """Dependency to validate message input"""
    return message_validator.validate_message(message)


def validate_name_input(name: str) -> str:
    """Dependency to validate name input"""
    return message_validator.validate_string_field(name, "name", _limits.max_name_length)


def validate_description_input(description: str) -> str:
    """Dependency to validate description input"""
    return message_validator.validate_string_field(
        description, "description", _limits.max_description_length
    )


async def validate_file_upload(file: UploadFile) -> UploadFile:
    """Dependency to validate file upload"""
    return await file_validator.validate_file(file)


def validate_json_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Dependency to validate JSON payload"""
    return json_validator.validate_json_size(data)


# Enhanced Pydantic models with validation
class ValidatedConversationCreate(BaseModel):
    """Conversation creation with validation"""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=2000)
    agent_id: str = Field(..., min_length=1, max_length=100)
    system_message: str = Field("", max_length=10000)

    @validator("name")
    def validate_name(cls, v):
        return message_validator.validate_string_field(v, "name", _limits.max_name_length)

    @validator("description")
    def validate_description(cls, v):
        if v:
            return message_validator.validate_string_field(
                v, "description", _limits.max_description_length
            )
        return v

    @validator("system_message")
    def validate_system_message(cls, v):
        if v:
            return message_validator.validate_message(v, "system_message")
        return v


class ValidatedMessageCreate(BaseModel):
    """Message creation with validation"""

    content: str = Field(..., min_length=1, max_length=10000)
    conversation_id: str = Field(..., min_length=1, max_length=100)

    @validator("content")
    def validate_content(cls, v):
        return message_validator.validate_message(v, "content")


class ValidatedWorkflowCreate(BaseModel):
    """Workflow creation with validation"""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=2000)
    steps: list[dict[str, Any]] = Field(..., min_items=1, max_items=50)
    parallel_execution: bool = False

    @validator("name")
    def validate_name(cls, v):
        return message_validator.validate_string_field(v, "name", _limits.max_name_length)

    @validator("description")
    def validate_description(cls, v):
        if v:
            return message_validator.validate_string_field(
                v, "description", _limits.max_description_length
            )
        return v

    @validator("steps")
    def validate_steps(cls, v):
        if len(v) > _limits.max_workflow_steps:
            raise ValueError(
                f"Too many workflow steps: {len(v)}, max: {_limits.max_workflow_steps}"
            )
        return json_validator.validate_json_size(v, "steps")


class ValidatedAgentConfig(BaseModel):
    """Agent configuration with validation"""

    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    description: str = Field("", max_length=2000)
    capabilities: list[str] = Field(default_factory=list, max_items=20)
    agent_settings: dict[str, Any] = Field(default_factory=dict)

    @validator("name")
    def validate_name(cls, v):
        return message_validator.validate_string_field(v, "name", _limits.max_name_length)

    @validator("description")
    def validate_description(cls, v):
        if v:
            return message_validator.validate_string_field(
                v, "description", _limits.max_description_length
            )
        return v

    @validator("capabilities")
    def validate_capabilities(cls, v):
        if len(v) > _limits.max_agent_capabilities:
            raise ValueError(
                f"Too many capabilities: {len(v)}, max: {_limits.max_agent_capabilities}"
            )
        for capability in v:
            if len(capability) > 100:
                raise ValueError(f"Capability too long: {len(capability)}, max: 100")
        return v

    @validator("agent_settings")
    def validate_settings(cls, v):
        return json_validator.validate_json_size(v, "agent_settings")


def setup_validation_middleware(app):
    """Setup validation middleware"""
    limits = ValidationConfig.get_limits()

    # Add request size limitation middleware
    app.add_middleware(RequestSizeMiddleware, max_size=limits.max_json_size)

    logger.info("Input validation middleware configured")
    logger.info(f"Max message length: {limits.max_message_length}")
    logger.info(f"Max file size: {limits.max_file_size}")
    logger.info(f"Max JSON size: {limits.max_json_size}")
    logger.info(f"Allowed file types: {len(ValidationConfig.get_allowed_file_types())}")

    return app
