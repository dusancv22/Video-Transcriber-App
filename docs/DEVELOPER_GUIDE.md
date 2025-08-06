# 🔧 Video Transcriber App - Developer Guide

## Overview

This guide provides comprehensive technical documentation for developers working on the Video Transcriber App. The application features a modern dual-interface architecture with both PyQt6 desktop and Electron web interfaces, sharing a common FastAPI backend.

## 🏗️ Architecture Deep Dive

### System Architecture

The application follows a modular, multi-layered architecture designed for maintainability, security, and scalability:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐         ┌─────────────────────────────────┐   │
│  │   PyQt6 GUI     │         │      Electron Frontend         │   │
│  │                 │         │                                 │   │
│  │ • Native Widgets│         │ • React 18 + TypeScript        │   │
│  │ • Modern Theme  │         │ • Material-UI Components       │   │
│  │ • Drag & Drop   │         │ • Real-time WebSocket Updates  │   │
│  │ • Queue Display │         │ • Settings Dialog with         │   │
│  │ • Progress Bars │         │   Validation                    │   │
│  │                 │         │ • Professional UX/UI Design    │   │
│  └─────────────────┘         └─────────────────────────────────┘   │
│           │                            │                           │
└───────────┼────────────────────────────┼───────────────────────────┘
            │                            │
            │    ┌─────────────────────┐ │
            │    │   FastAPI Backend   │ │
            └────┤                     ├─┘
                 │ • REST API Endpoints│
                 │ • WebSocket Server  │
                 │ • Request Validation│
                 │ • Security Layer    │
                 │ • Settings Manager  │
                 │ • Error Handling    │
                 └─────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────────────┐
│                      BUSINESS LOGIC LAYER                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                Core Processing Engine                       │   │
│  │                                                             │   │
│  │  • TranscriptionPipeline    • SecurityValidator           │   │
│  │  • QueueManager            • SettingsManager              │   │
│  │  • WhisperManager          • ErrorHandler                 │   │
│  │  • ProgressTracker         • FileValidator                │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
            │
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA PROCESSING LAYER                           │
├─────────────────────────────────────────────────────────────────────┤
│  • AudioConverter - FFmpeg integration for video processing        │
│  • AudioSplitter - Intelligent file segmentation (>25MB)          │
│  • TextProcessor - Post-processing and formatting                  │
│  • MultiFormatExporter - TXT/SRT/VTT output generation            │
│  • ProgressCalculator - Real-time progress and ETA calculations   │
└─────────────────────────────────────────────────────────────────────┘
            │
┌─────────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                             │
├─────────────────────────────────────────────────────────────────────┤
│  • Security System - Path traversal protection & input validation  │
│  • Logging System - Structured logging with configurable levels    │
│  • File Management - Temporary file handling and cleanup           │
│  • Thread Management - Safe concurrent operations                  │
│  • WebSocket Manager - Real-time bi-directional communication     │
│  • Error Recovery - Graceful error handling and user feedback     │
└─────────────────────────────────────────────────────────────────────┘
```

## 🚀 Development Environment Setup

### Prerequisites

**Core Requirements:**
- Python 3.8+ (3.10+ recommended)
- Node.js 16+ and npm
- Git for version control
- FFmpeg system dependency

**Optional but Recommended:**
- CUDA toolkit for GPU acceleration
- Docker for containerized development
- VS Code or PyCharm for development

### Installation Steps

1. **Clone Repository:**
```bash
git clone <repository-url>
cd video-transcriber-app
```

2. **Python Environment Setup:**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install Python dependencies
pip install -r requirements.txt
pip install -e .
```

3. **Node.js Environment Setup:**
```bash
cd video-transcriber-electron
npm install
npm run build:dev
```

4. **Verify Installation:**
```bash
# Test Python backend
python -c "import torch; print('PyTorch:', torch.__version__)"
python -c "from faster_whisper import WhisperModel; print('Whisper: OK')"

# Test Node.js frontend
cd video-transcriber-electron
npm run test:env
```

## 🔨 Development Workflow

### Starting Development Environment

**Automated Development Setup:**
```bash
# Windows - Use development batch file
video-transcriber-electron/dev-start.bat

# Linux/Mac - Use shell script
./scripts/dev-start.sh
```

**Manual Development Setup:**
```bash
# Terminal 1 - Backend with auto-reload
cd video-transcriber-electron/backend
python main.py --reload --log-level debug

# Terminal 2 - Frontend with hot reload
cd video-transcriber-electron
npm run dev

# Optional Terminal 3 - PyQt6 desktop version
python run.py
```

### Code Style and Standards

**Python Code Style:**
- Follow PEP 8 with Black formatter
- Use type hints for all function parameters and returns
- Docstrings required for all public methods
- Maximum line length: 100 characters

```python
# Example function with proper style
def process_audio_file(
    file_path: Path, 
    output_dir: Path, 
    whisper_model: str = "large"
) -> ProcessingResult:
    """
    Process a single audio file using Whisper AI.
    
    Args:
        file_path: Path to the audio file to process
        output_dir: Directory where transcript will be saved
        whisper_model: Whisper model size (base, small, medium, large)
        
    Returns:
        ProcessingResult object with transcription details
        
    Raises:
        ProcessingError: If file processing fails
        ValidationError: If input parameters are invalid
    """
    # Implementation here
    pass
```

**TypeScript/React Code Style:**
- Use TypeScript strict mode
- Follow React hooks patterns
- Functional components preferred over class components
- Proper interface definitions for all props

```typescript
// Example React component with proper TypeScript
interface SettingsDialogProps {
  open: boolean;
  onClose: () => void;
  initialSettings: ProcessingOptions;
}

export const SettingsDialog: React.FC<SettingsDialogProps> = ({
  open,
  onClose,
  initialSettings
}) => {
  // Implementation here
};
```

## 🧪 Testing Framework

### Testing Architecture

The testing suite includes comprehensive coverage across all layers:

```
tests/
├── unit/                          # Unit tests
│   ├── test_audio_processing/     # Audio converter tests
│   ├── test_transcription/        # Whisper integration tests
│   ├── test_queue_management/     # Queue operations tests
│   └── test_utils/               # Utility function tests
├── integration/                   # Integration tests
│   ├── test_api_endpoints/        # API endpoint testing
│   ├── test_websocket/           # WebSocket communication tests
│   ├── test_file_operations/     # File handling tests
│   └── test_processing_pipeline/  # End-to-end processing tests
├── security/                      # Security-focused tests
│   ├── test_path_traversal/       # Directory traversal protection
│   ├── test_input_validation/     # Input sanitization tests
│   └── test_permission_checks/    # File permission validation
├── frontend/                      # Frontend-specific tests
│   ├── components/               # React component tests
│   ├── integration/              # Frontend integration tests
│   └── e2e/                     # End-to-end user flow tests
└── performance/                   # Performance and load tests
    ├── test_large_files/         # Large file handling
    ├── test_memory_usage/        # Memory consumption tests
    └── test_concurrent_processing/ # Concurrent operation tests
```

### Running Tests

**Python Backend Tests:**
```bash
# Run all tests with coverage
python -m pytest tests/ -v --cov=src --cov-report=html

# Run specific test categories
python -m pytest tests/unit/ -v                    # Unit tests only
python -m pytest tests/integration/ -v             # Integration tests
python -m pytest tests/security/ -v                # Security tests

# Run with specific markers
python -m pytest -m "not slow" -v                  # Skip slow tests
python -m pytest -m "security" -v                  # Security tests only
```

**Frontend Tests:**
```bash
cd video-transcriber-electron

# Run all frontend tests
npm test

# Run tests with coverage
npm run test:coverage

# Run integration tests
npm run test:integration

# Run end-to-end tests
npm run test:e2e
```

**Security Testing:**
```bash
# Comprehensive security audit
npm run test:security

# Specific security test categories
python -m pytest tests/security/test_path_traversal.py -v
python -m pytest tests/security/test_input_validation.py -v
```

### Writing Tests

**Python Test Example:**
```python
import pytest
from pathlib import Path
from src.transcription.whisper_manager import WhisperManager
from src.utils.error_handler import ProcessingError

class TestWhisperManager:
    """Test suite for WhisperManager functionality."""
    
    @pytest.fixture
    def whisper_manager(self):
        """Create WhisperManager instance for testing."""
        return WhisperManager(model_size="base")
    
    @pytest.fixture
    def sample_audio_file(self, tmp_path: Path) -> Path:
        """Create sample audio file for testing."""
        audio_file = tmp_path / "test_audio.wav"
        # Create test audio file
        return audio_file
    
    def test_model_loading_success(self, whisper_manager):
        """Test successful Whisper model loading."""
        result = whisper_manager.load_model()
        assert result is True
        assert whisper_manager.is_model_loaded()
    
    def test_transcription_with_valid_audio(self, whisper_manager, sample_audio_file):
        """Test transcription with valid audio file."""
        result = whisper_manager.transcribe_audio(sample_audio_file)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_transcription_with_invalid_file(self, whisper_manager):
        """Test transcription error handling with invalid file."""
        with pytest.raises(ProcessingError):
            whisper_manager.transcribe_audio(Path("nonexistent.wav"))
    
    @pytest.mark.slow
    def test_large_file_processing(self, whisper_manager, large_audio_file):
        """Test processing of large audio files."""
        # This test may be slow, marked appropriately
        result = whisper_manager.transcribe_audio(large_audio_file)
        assert result is not None
```

**React Component Test Example:**
```typescript
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SettingsDialog } from '../SettingsDialog';
import { ProcessingOptions } from '../../types/api';

const mockSettings: ProcessingOptions = {
  output_directory: '/test/output',
  whisper_model: 'large',
  language: 'en',
  output_format: 'txt'
};

describe('SettingsDialog', () => {
  it('renders settings form correctly', () => {
    render(
      <SettingsDialog
        open={true}
        onClose={() => {}}
        initialSettings={mockSettings}
      />
    );
    
    expect(screen.getByText('Processing Settings')).toBeInTheDocument();
    expect(screen.getByDisplayValue('/test/output')).toBeInTheDocument();
  });

  it('validates output directory path', async () => {
    const onClose = jest.fn();
    render(
      <SettingsDialog
        open={true}
        onClose={onClose}
        initialSettings={mockSettings}
      />
    );
    
    const directoryInput = screen.getByDisplayValue('/test/output');
    fireEvent.change(directoryInput, { target: { value: '' } });
    
    await waitFor(() => {
      expect(screen.getByText('Output directory is required')).toBeInTheDocument();
    });
  });
});
```

## 🔐 Security Implementation

### Security Architecture

The application implements multiple layers of security protection:

**Input Validation Layer:**
```python
class SecurityValidator:
    """Comprehensive input validation and sanitization."""
    
    @staticmethod
    def validate_file_path(path_str: str) -> tuple[bool, str]:
        """
        Validate file path for security issues.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(path_str).resolve()
            
            # Check for directory traversal
            if ".." in str(path):
                return False, "Directory traversal not allowed"
            
            # Validate path components
            for part in path.parts:
                if part.startswith(".."):
                    return False, "Invalid path component"
            
            # OS-specific validation
            if os.name == 'nt':  # Windows
                invalid_chars = r'[<>:"|?*]'
                if re.search(invalid_chars, str(path)):
                    return False, "Invalid characters in path"
            
            return True, "Valid path"
            
        except Exception as e:
            return False, f"Path validation error: {str(e)}"
```

**Permission Checking:**
```python
class PermissionValidator:
    """File system permission validation."""
    
    @staticmethod
    def check_directory_access(directory: Path) -> dict:
        """
        Check directory access permissions.
        
        Returns:
            Dictionary with permission details
        """
        result = {
            "exists": directory.exists(),
            "is_directory": directory.is_dir() if directory.exists() else False,
            "readable": False,
            "writable": False,
            "parent_writable": False
        }
        
        if directory.exists() and directory.is_dir():
            result["readable"] = os.access(directory, os.R_OK)
            result["writable"] = os.access(directory, os.W_OK)
        elif directory.parent.exists():
            result["parent_writable"] = os.access(directory.parent, os.W_OK)
        
        return result
```

### Security Testing

**Path Traversal Protection Tests:**
```python
class TestPathTraversalProtection:
    """Test security against path traversal attacks."""
    
    @pytest.mark.parametrize("malicious_path", [
        "../../../etc/passwd",
        "..\\..\\windows\\system32",
        "/etc/passwd",
        "C:\\Windows\\System32",
        "../../../../usr/bin",
        "..%2F..%2Fetc%2Fpasswd",  # URL encoded
        "....//....//etc//passwd",  # Double encoding
    ])
    def test_path_traversal_prevention(self, malicious_path):
        """Test prevention of directory traversal attacks."""
        is_valid, error_msg = SecurityValidator.validate_file_path(malicious_path)
        assert not is_valid, f"Path should be rejected: {malicious_path}"
        assert "traversal" in error_msg.lower() or "invalid" in error_msg.lower()
```

## 📡 API Development

### FastAPI Backend Structure

```
backend/
├── main.py                    # Application entry point
├── api/
│   ├── __init__.py
│   ├── endpoints/             # API endpoint definitions
│   │   ├── files.py          # File operations endpoints
│   │   ├── processing.py     # Processing control endpoints
│   │   ├── settings.py       # Configuration endpoints
│   │   └── websocket.py      # WebSocket handlers
│   ├── models/               # Pydantic data models
│   │   ├── requests.py       # Request models
│   │   ├── responses.py      # Response models
│   │   └── settings.py       # Settings models
│   └── middleware/           # Custom middleware
│       ├── security.py       # Security middleware
│       ├── logging.py        # Request logging
│       └── cors.py          # CORS handling
├── services/                 # Business logic services
│   ├── transcription.py     # Transcription service
│   ├── file_handler.py      # File handling service
│   ├── queue_manager.py     # Queue management service
│   └── settings_manager.py  # Settings persistence service
└── websocket/               # WebSocket implementation
    ├── __init__.py
    ├── manager.py           # Connection management
    └── handlers.py          # Message handlers
```

### API Endpoint Examples

**File Upload Endpoint:**
```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List

router = APIRouter(prefix="/api/files", tags=["files"])

class FileUploadRequest(BaseModel):
    files: List[str] = Field(..., description="List of file paths to add to queue")

class FileUploadResponse(BaseModel):
    success: bool
    added_count: int
    skipped_count: int
    errors: List[dict]

@router.post("/add", response_model=FileUploadResponse)
async def add_files_to_queue(
    request: FileUploadRequest,
    background_tasks: BackgroundTasks
) -> FileUploadResponse:
    """
    Add files to the processing queue with validation.
    
    This endpoint validates file formats, checks accessibility,
    and adds valid files to the transcription queue.
    """
    try:
        # Validate input
        if not request.files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Process files through service layer
        result = await file_service.add_files(request.files)
        
        # Broadcast updates via WebSocket
        background_tasks.add_task(
            websocket_manager.broadcast_queue_update,
            {"action": "files_added", "result": result}
        )
        
        return FileUploadResponse(**result)
        
    except Exception as e:
        logger.error(f"Error adding files: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Settings Management Endpoint:**
```python
@router.post("/settings", response_model=SettingsResponse)
async def update_settings(
    settings: ProcessingOptionsRequest
) -> SettingsResponse:
    """
    Update processing settings with comprehensive validation.
    
    Validates all settings including path security, model availability,
    and disk space requirements before saving.
    """
    try:
        # Security validation
        path_valid, path_error = SecurityValidator.validate_file_path(
            settings.output_directory
        )
        if not path_valid:
            raise HTTPException(status_code=400, detail=f"Invalid path: {path_error}")
        
        # Permission validation
        permissions = PermissionValidator.check_directory_access(
            Path(settings.output_directory)
        )
        if not permissions.get("writable") and not permissions.get("parent_writable"):
            raise HTTPException(
                status_code=403, 
                detail="No write permission for output directory"
            )
        
        # Save settings
        result = await settings_service.save_settings(settings)
        
        return SettingsResponse(success=True, settings=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### WebSocket Implementation

```python
class WebSocketManager:
    """Manage WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove disconnected WebSocket."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_progress_update(self, file_id: str, progress: dict):
        """Send progress update for specific file."""
        message = {
            "type": "progress_update",
            "file_id": file_id,
            "timestamp": datetime.now().isoformat(),
            **progress
        }
        await self.broadcast(message)
```

## 🎨 Frontend Development

### React + TypeScript Architecture

```
src/
├── components/               # Reusable React components
│   ├── common/              # Generic UI components
│   │   ├── Button.tsx
│   │   ├── Dialog.tsx
│   │   └── ProgressBar.tsx
│   ├── FileDropZone.tsx     # File upload interface
│   ├── MainWindow.tsx       # Main application window
│   ├── ProgressSection.tsx  # Progress monitoring
│   ├── QueuePanel.tsx       # File queue management
│   ├── SettingsDialog.tsx   # Configuration interface
│   └── StatusBar.tsx        # Status information
├── services/                # API and business logic
│   ├── api.ts              # REST API client
│   ├── websocket.ts        # WebSocket client
│   └── validation.ts       # Input validation
├── store/                   # State management
│   ├── appStore.ts         # Main application state
│   ├── settingsStore.ts    # Settings state
│   └── queueStore.ts       # Queue state
├── types/                   # TypeScript definitions
│   ├── api.ts              # API response types
│   ├── app.ts              # Application types
│   └── electron.d.ts       # Electron type definitions
├── utils/                   # Utility functions
│   ├── formatting.ts       # Data formatting
│   ├── validation.ts       # Input validation
│   └── constants.ts        # Application constants
└── theme/                   # Material-UI theme
    ├── theme.ts            # Theme configuration
    └── components.ts       # Component overrides
```

### State Management with Zustand

```typescript
// Application state management
interface AppState {
  // Connection status
  isConnected: boolean;
  connectionError: string | null;
  
  // Processing state
  isProcessing: boolean;
  isPaused: boolean;
  currentFile: QueueItem | null;
  
  // Queue management
  queue: QueueItem[];
  queueStats: QueueStats;
  
  // Settings
  processingOptions: ProcessingOptions;
  
  // Actions
  setConnectionStatus: (connected: boolean, error?: string) => void;
  updateQueue: (queue: QueueItem[]) => void;
  updateQueueItem: (itemId: string, updates: Partial<QueueItem>) => void;
  setProcessingOptions: (options: ProcessingOptions) => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  isConnected: false,
  connectionError: null,
  isProcessing: false,
  isPaused: false,
  currentFile: null,
  queue: [],
  queueStats: { total: 0, queued: 0, processing: 0, completed: 0, failed: 0 },
  processingOptions: DEFAULT_PROCESSING_OPTIONS,
  
  // Actions
  setConnectionStatus: (connected, error) => set({
    isConnected: connected,
    connectionError: error || null
  }),
  
  updateQueue: (queue) => {
    const stats = calculateQueueStats(queue);
    set({ queue, queueStats: stats });
  },
  
  updateQueueItem: (itemId, updates) => set((state) => ({
    queue: state.queue.map(item => 
      item.id === itemId ? { ...item, ...updates } : item
    )
  })),
  
  setProcessingOptions: (options) => {
    // Validate options before setting
    const validatedOptions = validateProcessingOptions(options);
    set({ processingOptions: validatedOptions });
    
    // Persist to localStorage
    localStorage.setItem('processingOptions', JSON.stringify(validatedOptions));
  }
}));
```

### Component Development Guidelines

**Component Structure:**
```typescript
interface ComponentProps {
  // Props interface with comprehensive typing
  title: string;
  onAction: (data: ActionData) => void;
  optional?: boolean;
}

export const ExampleComponent: React.FC<ComponentProps> = ({
  title,
  onAction,
  optional = false
}) => {
  // Local state management
  const [localState, setLocalState] = useState<LocalStateType>(initialState);
  
  // Global state access
  const { globalData, updateGlobalData } = useAppStore();
  
  // Effect hooks
  useEffect(() => {
    // Component lifecycle logic
  }, [dependencies]);
  
  // Event handlers
  const handleUserAction = useCallback((event: React.MouseEvent) => {
    // Handle user interactions
    onAction(processedData);
  }, [onAction]);
  
  // Render with proper accessibility
  return (
    <Paper elevation={2} sx={{ p: 3 }}>
      <Typography variant="h6" component="h2">
        {title}
      </Typography>
      {/* Component content */}
    </Paper>
  );
};
```

## 🚀 Deployment and Distribution

### Building for Production

**Electron Application:**
```bash
cd video-transcriber-electron

# Build frontend for production
npm run build

# Package Electron app
npm run package

# Create installers
npm run make
```

**PyQt6 Desktop Application:**
```bash
# Create standalone executable
pyinstaller --onefile --windowed run.py

# With custom icon and additional files
pyinstaller video-transcriber.spec
```

### Docker Development Environment

```dockerfile
# Dockerfile for development environment
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy Node.js requirements and install
COPY video-transcriber-electron/package*.json ./video-transcriber-electron/
WORKDIR /app/video-transcriber-electron
RUN npm install

# Copy application code
WORKDIR /app
COPY . .

# Expose ports
EXPOSE 8000 5173

# Start development environment
CMD ["./scripts/dev-start.sh"]
```

### Continuous Integration

```yaml
# GitHub Actions workflow
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run security tests
      run: |
        python -m pytest tests/security/ -v
    
    - name: Run unit tests
      run: |
        python -m pytest tests/unit/ -v --cov=src
    
    - name: Run integration tests
      run: |
        python -m pytest tests/integration/ -v

  frontend-test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: video-transcriber-electron/package-lock.json
    
    - name: Install dependencies
      run: |
        cd video-transcriber-electron
        npm ci
    
    - name: Run tests
      run: |
        cd video-transcriber-electron
        npm test
    
    - name: Run security audit
      run: |
        cd video-transcriber-electron
        npm audit
```

## 📝 Contributing Guidelines

### Code Review Process

1. **Create Feature Branch**: Branch from `develop` for new features
2. **Implement Changes**: Follow coding standards and write tests
3. **Security Review**: Ensure all security tests pass
4. **Create Pull Request**: Provide detailed description and testing steps
5. **Code Review**: Address feedback from maintainers
6. **Merge**: After approval and all checks pass

### Commit Message Format

```
type(scope): brief description

Detailed description if necessary

- List specific changes
- Include any breaking changes
- Reference issues if applicable

Closes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Maintenance tasks

### Documentation Requirements

**All new features must include:**
- Code documentation (docstrings/comments)
- Unit tests with >80% coverage
- Integration tests for user-facing features
- Security tests for any input handling
- User documentation updates
- API documentation updates (if applicable)

## 🔍 Debugging and Troubleshooting

### Debug Mode Setup

**Backend Debug Mode:**
```bash
cd video-transcriber-electron/backend
python main.py --debug --log-level debug
```

**Frontend Debug Mode:**
```bash
cd video-transcriber-electron
npm run dev:debug
```

### Common Development Issues

**Backend Issues:**
```bash
# Import errors - check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Port conflicts - change backend port
python main.py --port 8001

# Model loading issues - clear cache
rm -rf ~/.cache/huggingface/transformers/
```

**Frontend Issues:**
```bash
# Node modules issues
rm -rf node_modules package-lock.json
npm install

# Port conflicts
npm run dev -- --port 5174

# Build cache issues
npm run clean && npm run build
```

### Performance Profiling

**Python Profiling:**
```bash
# Profile main application
python -m cProfile -o profile.stats run.py

# Analyze profile
python -m pstats profile.stats
```

**Frontend Profiling:**
```bash
# Bundle analysis
cd video-transcriber-electron
npm run build:analyze

# Performance monitoring
npm run dev:perf
```

This developer guide provides comprehensive technical documentation for contributing to and extending the Video Transcriber App. For specific implementation details, refer to the inline code documentation and additional technical specifications in the repository.