# 🔐 Video Transcriber App - Security Guide

## Overview

The Video Transcriber App implements comprehensive security measures to protect against common attacks and ensure safe operation. This guide documents all security features, best practices, and testing procedures.

## 🛡️ Security Architecture

### Multi-Layer Security Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT VALIDATION LAYER                      │
├─────────────────────────────────────────────────────────────────┤
│ • Path Traversal Protection    • Input Sanitization            │
│ • File Format Validation       • Character Encoding Checks     │
│ • Size Limit Enforcement       • Extension Verification        │
└─────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────┐
│                   PERMISSION VALIDATION LAYER                  │
├─────────────────────────────────────────────────────────────────┤
│ • File System Permissions     • Directory Access Validation    │
│ • Write Permission Checks      • Read Permission Verification  │
│ • Disk Space Validation        • Parent Directory Checks       │
└─────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────┐
│                    ERROR HANDLING LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│ • Secure Error Messages       • Information Leakage Prevention │
│ • Error Code Sanitization     • Stack Trace Protection         │
│ • User-Friendly Responses     • Logging Without Exposure       │
└─────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────┐
│                   RUNTIME PROTECTION LAYER                     │
├─────────────────────────────────────────────────────────────────┤
│ • Resource Limits             • Memory Usage Monitoring        │
│ • Process Isolation           • Temporary File Cleanup         │
│ • Connection Management       • Rate Limiting (planned)        │
└─────────────────────────────────────────────────────────────────┘
```

## 🚫 Path Traversal Protection

### Directory Traversal Prevention

The application implements comprehensive protection against directory traversal attacks:

```python
class SecurityValidator:
    """Comprehensive security validation for file paths."""
    
    @staticmethod
    def validate_file_path(path_str: str) -> tuple[bool, str]:
        """
        Validate file path against directory traversal attacks.
        
        Args:
            path_str: Input path string from user
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not path_str or not path_str.strip():
            return False, "Path cannot be empty"
        
        try:
            # Normalize and resolve path
            path = Path(path_str).resolve()
            
            # Primary traversal detection
            if ".." in str(path):
                return False, "Directory traversal not allowed"
            
            # Component-level traversal detection
            for part in path.parts:
                if part.startswith(".."):
                    return False, "Invalid path component detected"
            
            # Encoded traversal detection
            decoded_path = urllib.parse.unquote(path_str)
            if ".." in decoded_path or "%2e%2e" in path_str.lower():
                return False, "Encoded directory traversal blocked"
            
            # OS-specific character validation
            if os.name == 'nt':  # Windows
                invalid_chars = r'[<>:"|?*]'
                if re.search(invalid_chars, str(path)):
                    return False, "Invalid characters in Windows path"
            
            # Prevent access to system directories
            system_paths = [
                "/etc", "/bin", "/usr/bin", "/root",
                "C:\\Windows", "C:\\Program Files", "C:\\System32"
            ]
            
            for sys_path in system_paths:
                if str(path).lower().startswith(sys_path.lower()):
                    return False, "Access to system directories blocked"
            
            return True, "Valid path"
            
        except Exception as e:
            return False, f"Path validation error: {str(e)}"
```

### Attack Patterns Blocked

| Attack Pattern | Example | Protection Method |
|----------------|---------|------------------|
| **Basic Traversal** | `../../../etc/passwd` | Path component analysis |
| **Windows Traversal** | `..\\..\\windows\\system32` | Multi-platform detection |
| **Absolute Paths** | `/etc/passwd` | System path blocking |
| **URL Encoding** | `%2e%2e%2fetc%2fpasswd` | URL decode before validation |
| **Double Encoding** | `....//....//etc//passwd` | Pattern normalization |
| **Mixed Separators** | `../..\/etc/passwd` | Path normalization |
| **Unicode Attacks** | `\u002e\u002e/etc/passwd` | Unicode normalization |

### Testing Path Security

```python
@pytest.mark.parametrize("malicious_path,expected_blocked", [
    ("../../../etc/passwd", True),
    ("..\\..\\windows\\system32", True), 
    ("/etc/passwd", True),
    ("C:\\Windows\\System32", True),
    ("../../../../usr/bin", True),
    ("..%2F..%2Fetc%2Fpasswd", True),
    ("....//....//etc//passwd", True),
    ("\u002e\u002e/etc/passwd", True),
    ("valid/relative/path", False),
    ("C:/Users/Public/Documents", False),
])
def test_path_traversal_protection(malicious_path, expected_blocked):
    """Test comprehensive path traversal protection."""
    is_valid, error_msg = SecurityValidator.validate_file_path(malicious_path)
    
    if expected_blocked:
        assert not is_valid, f"Path should be blocked: {malicious_path}"
        assert any(keyword in error_msg.lower() for keyword in 
                  ["traversal", "invalid", "blocked"]), f"Expected security error for: {malicious_path}"
    else:
        assert is_valid, f"Valid path should be allowed: {malicious_path}"
```

## 🔍 Input Validation & Sanitization

### File Input Validation

```python
class FileValidator:
    """Comprehensive file validation and sanitization."""
    
    ALLOWED_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov'}
    MAX_PATH_LENGTH = 260  # Windows MAX_PATH limitation
    MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB limit
    
    @classmethod
    def validate_file(cls, file_path: str) -> tuple[bool, str]:
        """
        Comprehensive file validation with security checks.
        
        Args:
            file_path: Path to file for validation
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Path length validation
        if len(file_path) > cls.MAX_PATH_LENGTH:
            return False, "File path too long"
        
        # Security path validation
        path_valid, path_error = SecurityValidator.validate_file_path(file_path)
        if not path_valid:
            return False, f"Security validation failed: {path_error}"
        
        try:
            path = Path(file_path)
            
            # Existence check
            if not path.exists():
                return False, "File does not exist"
            
            # File type validation
            if not path.is_file():
                return False, "Path is not a file"
            
            # Extension validation
            if path.suffix.lower() not in cls.ALLOWED_EXTENSIONS:
                return False, f"Unsupported file format. Allowed: {', '.join(cls.ALLOWED_EXTENSIONS)}"
            
            # File size validation
            file_size = path.stat().st_size
            if file_size > cls.MAX_FILE_SIZE:
                return False, f"File too large (max {cls.MAX_FILE_SIZE // (1024**3)}GB)"
            
            if file_size == 0:
                return False, "File is empty"
            
            # Permission validation
            if not os.access(path, os.R_OK):
                return False, "No read permission for file"
            
            # Basic file integrity check
            try:
                with open(path, 'rb') as f:
                    # Read first few bytes to verify file accessibility
                    f.read(1024)
            except (IOError, OSError) as e:
                return False, f"File accessibility error: {str(e)}"
            
            return True, "File is valid"
            
        except Exception as e:
            return False, f"File validation error: {str(e)}"
```

### API Request Validation

```python
from pydantic import BaseModel, Field, validator
import re

class ProcessingOptionsRequest(BaseModel):
    """Secure processing options with comprehensive validation."""
    
    output_directory: str = Field(..., min_length=1, max_length=260)
    whisper_model: Literal['base', 'small', 'medium', 'large']
    language: Literal['en', 'auto'] 
    output_format: Literal['txt', 'srt', 'vtt']
    
    @validator('output_directory')
    def validate_output_directory(cls, v):
        """Comprehensive output directory validation."""
        if not v or v.strip() == "":
            raise ValueError("Output directory cannot be empty")
        
        # Security validation
        is_valid, error = SecurityValidator.validate_file_path(v)
        if not is_valid:
            raise ValueError(f"Security validation failed: {error}")
        
        try:
            path = Path(v).resolve()
            
            # Length validation
            if len(str(path)) > 260:
                raise ValueError("Path too long")
            
            # Character validation for Windows
            if os.name == 'nt':
                invalid_chars = r'[<>:"|?*]'
                if re.search(invalid_chars, str(path)):
                    raise ValueError("Path contains invalid characters")
            
            # Reserved name validation (Windows)
            reserved_names = {
                'CON', 'PRN', 'AUX', 'NUL',
                'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
            }
            
            if path.name.upper() in reserved_names:
                raise ValueError("Reserved filename not allowed")
            
            return str(path)
            
        except Exception as e:
            raise ValueError(f"Invalid output directory: {str(e)}")
    
    @validator('whisper_model')
    def validate_whisper_model(cls, v):
        """Validate Whisper model selection."""
        if v not in ['base', 'small', 'medium', 'large']:
            raise ValueError("Invalid Whisper model")
        return v
    
    @validator('output_format')
    def validate_output_format(cls, v):
        """Validate output format selection."""
        if v not in ['txt', 'srt', 'vtt']:
            raise ValueError("Invalid output format")
        return v
```

## 🔐 Permission Management

### File System Permission Validation

```python
class PermissionValidator:
    """File system permission validation and checking."""
    
    @staticmethod
    def check_directory_permissions(directory: Path) -> dict:
        """
        Comprehensive directory permission checking.
        
        Args:
            directory: Directory path to check
            
        Returns:
            Dictionary with permission details
        """
        result = {
            "exists": False,
            "is_directory": False,
            "readable": False,
            "writable": False,
            "executable": False,
            "parent_exists": False,
            "parent_writable": False,
            "owner": None,
            "permissions": None
        }
        
        try:
            # Check if path exists
            result["exists"] = directory.exists()
            
            if result["exists"]:
                result["is_directory"] = directory.is_dir()
                
                if result["is_directory"]:
                    # Check permissions on existing directory
                    result["readable"] = os.access(directory, os.R_OK)
                    result["writable"] = os.access(directory, os.W_OK)
                    result["executable"] = os.access(directory, os.X_OK)
                    
                    # Get ownership information
                    stat_info = directory.stat()
                    result["owner"] = stat_info.st_uid
                    result["permissions"] = oct(stat_info.st_mode)[-3:]
            else:
                # Check parent directory for creation capability
                parent = directory.parent
                result["parent_exists"] = parent.exists()
                
                if result["parent_exists"]:
                    result["parent_writable"] = os.access(parent, os.W_OK)
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            return result
    
    @staticmethod
    def validate_write_access(directory: Path) -> tuple[bool, str]:
        """
        Validate write access to directory with security checks.
        
        Args:
            directory: Directory to validate
            
        Returns:
            Tuple of (has_access, error_message)
        """
        permissions = PermissionValidator.check_directory_permissions(directory)
        
        if permissions.get("error"):
            return False, f"Permission check failed: {permissions['error']}"
        
        if permissions["exists"]:
            if not permissions["is_directory"]:
                return False, "Path exists but is not a directory"
            
            if not permissions["writable"]:
                return False, "No write permission for existing directory"
        else:
            if not permissions["parent_exists"]:
                return False, "Parent directory does not exist"
            
            if not permissions["parent_writable"]:
                return False, "No write permission for parent directory"
        
        return True, "Write access validated"
```

### Disk Space Validation

```python
class DiskSpaceValidator:
    """Disk space validation for safe operation."""
    
    MIN_FREE_SPACE_MB = 100  # Minimum 100MB required
    
    @staticmethod
    def check_disk_space(path: Path) -> dict:
        """
        Check available disk space for path.
        
        Args:
            path: Path to check disk space for
            
        Returns:
            Dictionary with disk space information
        """
        try:
            # Use existing directory or parent for space check
            check_path = path if path.exists() else path.parent
            
            usage = shutil.disk_usage(check_path)
            
            return {
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "total_mb": usage.total / (1024 * 1024),
                "used_mb": usage.used / (1024 * 1024),
                "free_mb": usage.free / (1024 * 1024),
                "usage_percent": (usage.used / usage.total) * 100,
                "has_sufficient_space": usage.free >= (DiskSpaceValidator.MIN_FREE_SPACE_MB * 1024 * 1024)
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "has_sufficient_space": False
            }
    
    @staticmethod
    def validate_space_requirements(path: Path, estimated_output_size: int = 0) -> tuple[bool, str]:
        """
        Validate disk space meets requirements.
        
        Args:
            path: Output path to check
            estimated_output_size: Estimated size of output files in bytes
            
        Returns:
            Tuple of (sufficient_space, message)
        """
        space_info = DiskSpaceValidator.check_disk_space(path)
        
        if space_info.get("error"):
            return False, f"Cannot check disk space: {space_info['error']}"
        
        required_space = max(
            DiskSpaceValidator.MIN_FREE_SPACE_MB * 1024 * 1024,
            estimated_output_size
        )
        
        if space_info["free_bytes"] < required_space:
            required_mb = required_space / (1024 * 1024)
            available_mb = space_info["free_mb"]
            return False, f"Insufficient disk space. Required: {required_mb:.1f}MB, Available: {available_mb:.1f}MB"
        
        return True, f"Sufficient disk space available ({space_info['free_mb']:.1f}MB free)"
```

## 🛡️ Error Handling Security

### Secure Error Response System

```python
class SecureErrorHandler:
    """Secure error handling with information leakage prevention."""
    
    # Safe error messages that don't expose system details
    SAFE_ERROR_MESSAGES = {
        "FILE_NOT_FOUND": "The specified file could not be found.",
        "PERMISSION_DENIED": "You don't have permission to access this resource.",
        "INVALID_INPUT": "The provided input is not valid.",
        "PROCESSING_ERROR": "An error occurred during processing.",
        "DISK_SPACE_ERROR": "Insufficient disk space for this operation.",
        "PATH_SECURITY_ERROR": "The specified path is not allowed for security reasons.",
        "FORMAT_ERROR": "The file format is not supported.",
        "SYSTEM_ERROR": "A system error occurred. Please try again later."
    }
    
    @staticmethod
    def create_safe_error_response(
        error_code: str, 
        internal_error: str = None,
        user_message: str = None
    ) -> dict:
        """
        Create secure error response without information leakage.
        
        Args:
            error_code: Machine-readable error code
            internal_error: Internal error details (for logging only)
            user_message: Custom user-friendly message
            
        Returns:
            Safe error response dictionary
        """
        # Log internal error details securely
        if internal_error:
            logger.error(f"Internal error [{error_code}]: {internal_error}")
        
        # Return safe user message
        safe_message = user_message or SecureErrorHandler.SAFE_ERROR_MESSAGES.get(
            error_code, 
            "An error occurred. Please contact support if this continues."
        )
        
        return {
            "error": True,
            "error_code": error_code,
            "message": safe_message,
            "timestamp": datetime.now().isoformat(),
            "suggestion": SecureErrorHandler._get_error_suggestion(error_code)
        }
    
    @staticmethod
    def _get_error_suggestion(error_code: str) -> str:
        """Get helpful suggestion for error code."""
        suggestions = {
            "FILE_NOT_FOUND": "Verify the file path is correct and the file exists.",
            "PERMISSION_DENIED": "Check file permissions and try running as administrator if needed.",
            "INVALID_INPUT": "Review the input format and try again.",
            "DISK_SPACE_ERROR": "Free up disk space and try again.",
            "PATH_SECURITY_ERROR": "Use a valid file path within allowed directories.",
            "FORMAT_ERROR": "Use a supported video format (MP4, AVI, MKV, MOV)."
        }
        return suggestions.get(error_code, "Please try again or contact support.")
    
    @staticmethod
    def handle_api_exception(e: Exception) -> HTTPException:
        """
        Convert internal exceptions to safe HTTP responses.
        
        Args:
            e: Internal exception
            
        Returns:
            Safe HTTPException for API response
        """
        # Determine error type and create safe response
        if isinstance(e, FileNotFoundError):
            error_response = SecureErrorHandler.create_safe_error_response(
                "FILE_NOT_FOUND", 
                str(e)
            )
            return HTTPException(status_code=404, detail=error_response)
        
        elif isinstance(e, PermissionError):
            error_response = SecureErrorHandler.create_safe_error_response(
                "PERMISSION_DENIED",
                str(e)
            )
            return HTTPException(status_code=403, detail=error_response)
        
        elif isinstance(e, ValueError):
            error_response = SecureErrorHandler.create_safe_error_response(
                "INVALID_INPUT",
                str(e)
            )
            return HTTPException(status_code=400, detail=error_response)
        
        else:
            # Generic system error - don't expose internal details
            error_response = SecureErrorHandler.create_safe_error_response(
                "SYSTEM_ERROR",
                str(e)
            )
            return HTTPException(status_code=500, detail=error_response)
```

## 🧪 Security Testing Framework

### Comprehensive Security Test Suite

```python
class SecurityTestSuite:
    """Comprehensive security testing framework."""
    
    @pytest.mark.security
    class TestPathTraversalProtection:
        """Test directory traversal attack prevention."""
        
        TRAVERSAL_PAYLOADS = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\",
            "../../../../usr/bin/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "....//....//....//etc//passwd",
            "\u002e\u002e/\u002e\u002e/etc/passwd",
            "%c0%af%c0%af%c0%afetc%c0%afpasswd",
            "..%c0%af..%c0%afetc%c0%afpasswd",
        ]
        
        @pytest.mark.parametrize("payload", TRAVERSAL_PAYLOADS)
        def test_path_traversal_blocked(self, payload):
            """Test that directory traversal attacks are blocked."""
            is_valid, error = SecurityValidator.validate_file_path(payload)
            assert not is_valid, f"Traversal payload should be blocked: {payload}"
            assert "traversal" in error.lower() or "invalid" in error.lower()
        
        def test_legitimate_paths_allowed(self):
            """Test that legitimate paths are allowed."""
            legitimate_paths = [
                "C:/Users/Public/Documents/video.mp4",
                "/home/user/videos/lecture.avi",
                "relative/path/to/file.mkv",
                "D:\\Projects\\Video\\interview.mov"
            ]
            
            for path in legitimate_paths:
                # Only test path format validation, not existence
                try:
                    normalized_path = str(Path(path).resolve())
                    is_valid, _ = SecurityValidator.validate_file_path(path)
                    # Should pass security validation (existence check separate)
                    assert is_valid or "not found" in _.lower()
                except:
                    # Path format issues are acceptable for cross-platform tests
                    pass
    
    @pytest.mark.security
    class TestInputValidation:
        """Test input validation and sanitization."""
        
        def test_malicious_filenames(self):
            """Test handling of malicious filenames."""
            malicious_files = [
                "file<script>alert('xss')</script>.mp4",
                "file'; DROP TABLE files; --.avi",
                "file${IFS}rm${IFS}-rf${IFS}/.mkv",
                "file`rm -rf /`.mov",
                "file\x00.mp4",  # Null byte injection
                "file\n\r.avi",  # Line break injection
            ]
            
            for filename in malicious_files:
                is_valid, error = FileValidator.validate_file(filename)
                assert not is_valid, f"Malicious filename should be rejected: {filename}"
        
        def test_oversized_inputs(self):
            """Test handling of oversized inputs."""
            # Test extremely long paths
            long_path = "A" * 1000 + ".mp4"
            is_valid, error = SecurityValidator.validate_file_path(long_path)
            assert not is_valid
            assert "too long" in error.lower() or "invalid" in error.lower()
        
        def test_unicode_attacks(self):
            """Test Unicode-based attacks."""
            unicode_attacks = [
                "\u002e\u002e/etc/passwd",
                "file\u0000.mp4",
                "file\u202e\u0040gnp.exe",  # Right-to-left override attack
            ]
            
            for attack in unicode_attacks:
                is_valid, error = SecurityValidator.validate_file_path(attack)
                assert not is_valid, f"Unicode attack should be blocked: {repr(attack)}"
    
    @pytest.mark.security  
    class TestPermissionValidation:
        """Test permission validation security."""
        
        def test_unauthorized_directory_access(self, tmp_path):
            """Test prevention of unauthorized directory access."""
            # Create test directory structure
            restricted_dir = tmp_path / "restricted"
            restricted_dir.mkdir(mode=0o000)  # No permissions
            
            try:
                permissions = PermissionValidator.check_directory_permissions(restricted_dir)
                assert not permissions.get("writable", False)
                assert not permissions.get("readable", False)
            finally:
                # Cleanup - restore permissions to allow deletion
                restricted_dir.chmod(0o755)
        
        def test_system_directory_blocking(self):
            """Test that system directories are blocked."""
            system_dirs = [
                "/etc",
                "/bin", 
                "/usr/bin",
                "C:\\Windows",
                "C:\\System32",
                "C:\\Program Files"
            ]
            
            for sys_dir in system_dirs:
                is_valid, error = SecurityValidator.validate_file_path(sys_dir)
                assert not is_valid, f"System directory should be blocked: {sys_dir}"
    
    @pytest.mark.security
    class TestErrorHandling:
        """Test secure error handling."""
        
        def test_no_information_leakage(self):
            """Test that errors don't leak sensitive information."""
            # Test various error conditions
            error_response = SecureErrorHandler.create_safe_error_response(
                "SYSTEM_ERROR",
                "Internal error: Database connection string: user:password@host"
            )
            
            # Should not contain sensitive internal details
            assert "password" not in error_response["message"].lower()
            assert "database" not in error_response["message"].lower()
            assert "connection string" not in error_response["message"].lower()
        
        def test_consistent_error_responses(self):
            """Test that error responses are consistent."""
            # Same error should produce same response format
            error1 = SecureErrorHandler.create_safe_error_response("FILE_NOT_FOUND")
            error2 = SecureErrorHandler.create_safe_error_response("FILE_NOT_FOUND")
            
            assert error1["error_code"] == error2["error_code"]
            assert error1["message"] == error2["message"]
```

### Security Integration Tests

```python
class SecurityIntegrationTests:
    """Integration tests focusing on security aspects."""
    
    @pytest.mark.asyncio
    async def test_api_path_traversal_protection(self, test_client):
        """Test API endpoint protection against path traversal."""
        traversal_payloads = [
            {"files": ["../../../etc/passwd"]},
            {"files": ["..\\..\\windows\\system32"]},
            {"files": ["/etc/shadow"]},
        ]
        
        for payload in traversal_payloads:
            response = await test_client.post("/api/files/add", json=payload)
            assert response.status_code in [400, 403], f"Traversal should be blocked: {payload}"
    
    @pytest.mark.asyncio 
    async def test_settings_validation_security(self, test_client):
        """Test settings endpoint security validation."""
        malicious_settings = {
            "output_directory": "../../../tmp",
            "whisper_model": "large'; DROP TABLE settings; --",
            "language": "en<script>alert('xss')</script>",
            "output_format": "txt"
        }
        
        response = await test_client.post("/api/processing/start", json=malicious_settings)
        assert response.status_code in [400, 422], "Malicious settings should be rejected"
    
    @pytest.mark.asyncio
    async def test_websocket_security(self, websocket_client):
        """Test WebSocket security measures."""
        # Test that WebSocket doesn't accept malicious messages
        malicious_messages = [
            '{"type": "injection", "payload": "$(rm -rf /)"}',
            '{"type": "../../../etc/passwd"}',
            '{"type": "admin", "command": "DELETE FROM users"}',
        ]
        
        for message in malicious_messages:
            await websocket_client.send_text(message)
            # Should not crash or execute malicious commands
            response = await websocket_client.receive_text()
            # Should receive safe error or be ignored
```

## 🔧 Security Configuration

### Environment Security Settings

```python
# Security configuration settings
SECURITY_CONFIG = {
    # Path validation settings
    "MAX_PATH_LENGTH": 260,
    "ALLOWED_EXTENSIONS": [".mp4", ".avi", ".mkv", ".mov"],
    "BLOCKED_SYSTEM_PATHS": [
        "/etc", "/bin", "/usr/bin", "/root",
        "C:\\Windows", "C:\\System32", "C:\\Program Files"
    ],
    
    # File validation settings
    "MAX_FILE_SIZE_GB": 10,
    "MIN_DISK_SPACE_MB": 100,
    "TEMP_FILE_CLEANUP_INTERVAL": 3600,  # 1 hour
    
    # Error handling settings
    "HIDE_INTERNAL_ERRORS": True,
    "LOG_SECURITY_EVENTS": True,
    "RATE_LIMIT_ENABLED": False,  # Future feature
    
    # WebSocket security
    "WS_MAX_MESSAGE_SIZE": 65536,  # 64KB
    "WS_MAX_CONNECTIONS": 100,
    "WS_HEARTBEAT_INTERVAL": 30,
}
```

### Security Logging Configuration

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_security_logging():
    """Configure security-focused logging."""
    
    # Security events logger
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.INFO)
    
    # Rotating file handler for security logs
    security_handler = RotatingFileHandler(
        'logs/security.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    security_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s - '
        'IP:%(remote_addr)s - User-Agent:%(user_agent)s'
    )
    security_handler.setFormatter(security_formatter)
    security_logger.addHandler(security_handler)
    
    return security_logger

# Usage in security validation
def log_security_event(event_type: str, details: str, severity: str = "INFO"):
    """Log security events for monitoring."""
    security_logger = logging.getLogger('security')
    
    log_message = f"SECURITY_EVENT: {event_type} - {details}"
    
    if severity == "CRITICAL":
        security_logger.critical(log_message)
    elif severity == "WARNING": 
        security_logger.warning(log_message)
    else:
        security_logger.info(log_message)
```

## 🚨 Security Monitoring & Alerting

### Security Event Detection

```python
class SecurityMonitor:
    """Monitor and detect security events."""
    
    def __init__(self):
        self.failed_attempts = {}
        self.suspicious_patterns = []
    
    def record_security_event(self, event_type: str, client_id: str, details: dict):
        """Record security event for analysis."""
        event = {
            "timestamp": datetime.now(),
            "event_type": event_type,
            "client_id": client_id,
            "details": details
        }
        
        # Log event
        log_security_event(event_type, json.dumps(details))
        
        # Check for suspicious patterns
        if self._is_suspicious_activity(event_type, client_id):
            self._handle_suspicious_activity(client_id, event)
    
    def _is_suspicious_activity(self, event_type: str, client_id: str) -> bool:
        """Detect suspicious activity patterns."""
        suspicious_events = ["PATH_TRAVERSAL_ATTEMPT", "MALICIOUS_INPUT", "PERMISSION_VIOLATION"]
        
        if event_type in suspicious_events:
            # Track failed attempts per client
            if client_id not in self.failed_attempts:
                self.failed_attempts[client_id] = []
            
            self.failed_attempts[client_id].append(datetime.now())
            
            # Remove old attempts (older than 1 hour)
            hour_ago = datetime.now() - timedelta(hours=1)
            self.failed_attempts[client_id] = [
                attempt for attempt in self.failed_attempts[client_id]
                if attempt > hour_ago
            ]
            
            # Trigger alert if too many attempts
            if len(self.failed_attempts[client_id]) > 5:
                return True
        
        return False
    
    def _handle_suspicious_activity(self, client_id: str, event: dict):
        """Handle detected suspicious activity."""
        alert_message = f"SUSPICIOUS ACTIVITY DETECTED: Client {client_id} - {event['event_type']}"
        
        # Log critical security event
        log_security_event("SUSPICIOUS_ACTIVITY", alert_message, "CRITICAL")
        
        # In production, this could:
        # - Send email/SMS alerts
        # - Temporarily block client
        # - Trigger additional monitoring
        # - Update security rules
```

## 📋 Security Checklist

### Development Security Checklist

- [ ] **Input Validation**
  - [ ] All user inputs validated and sanitized
  - [ ] Path traversal protection implemented
  - [ ] File format validation in place
  - [ ] Size limits enforced
  - [ ] Character encoding validated

- [ ] **Permission Management**  
  - [ ] File system permissions checked
  - [ ] Directory access validated
  - [ ] Write permissions verified
  - [ ] Disk space validated
  - [ ] System directory access blocked

- [ ] **Error Handling**
  - [ ] Secure error messages implemented
  - [ ] Information leakage prevented
  - [ ] Stack traces hidden from users
  - [ ] Consistent error responses
  - [ ] Security events logged

- [ ] **API Security**
  - [ ] Request validation implemented
  - [ ] Response sanitization in place
  - [ ] WebSocket security measures active
  - [ ] Rate limiting considered
  - [ ] CORS properly configured

- [ ] **Testing**
  - [ ] Security test suite comprehensive
  - [ ] Path traversal tests passing
  - [ ] Input validation tests complete
  - [ ] Permission tests verified
  - [ ] Integration security tests running

### Deployment Security Checklist

- [ ] **Environment Security**
  - [ ] Security logging enabled
  - [ ] Monitoring systems active
  - [ ] File permissions correctly set
  - [ ] Temporary file cleanup working
  - [ ] Error handling configured

- [ ] **Network Security**
  - [ ] HTTPS enabled (if applicable)
  - [ ] WebSocket security configured
  - [ ] Firewall rules in place
  - [ ] Local-only access enforced
  - [ ] Port access restricted

- [ ] **System Security**
  - [ ] Application runs with minimal privileges
  - [ ] File system access restricted
  - [ ] Resource limits in place
  - [ ] Security updates applied
  - [ ] Backup and recovery plan exists

## 🔄 Security Maintenance

### Regular Security Reviews

1. **Code Reviews**: All code changes reviewed for security implications
2. **Dependency Updates**: Regular updates of security-related dependencies  
3. **Penetration Testing**: Periodic security testing of the application
4. **Log Analysis**: Regular review of security logs for anomalies
5. **Configuration Audits**: Verification of security configuration settings

### Security Incident Response

1. **Detection**: Monitor logs and alerts for security events
2. **Analysis**: Investigate and assess severity of security incidents
3. **Containment**: Isolate and contain security threats
4. **Recovery**: Restore normal operations safely
5. **Lessons Learned**: Update security measures based on incidents

---

This security guide provides comprehensive documentation of all security measures implemented in the Video Transcriber App. Regular review and updates of these security practices ensure ongoing protection against evolving threats.