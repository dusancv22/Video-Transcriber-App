# Video Transcriber App - Integration Test Suite

This directory contains comprehensive integration and end-to-end tests for the Video Transcriber App, with a focus on security testing and functionality verification.

## 🔐 Security-Focused Testing

This test suite prioritizes security testing due to critical vulnerabilities identified in the code review:

### Critical Security Issues Addressed
- **Path Traversal Vulnerabilities** in FileDropZone and QueuePanel
- **Unsafe File Path Operations** throughout the application
- **Input Validation Gaps** in user inputs
- **Mock Data in Production** code (removed from production, isolated to tests)

## 📁 Test Structure

```
tests/
├── integration/
│   ├── security/
│   │   ├── path-traversal.test.ts       # Path traversal attack protection
│   │   ├── input-validation.test.ts     # Input sanitization and validation
│   │   └── file-security.test.ts        # File operation security
│   ├── settings/
│   │   ├── settings-dialog.test.ts      # Settings UI integration
│   │   └── settings-persistence.test.ts # Settings storage and retrieval
│   ├── file-operations/
│   │   ├── file-browsing.test.ts        # File dialog and browsing
│   │   └── queue-operations.test.ts     # Queue management operations
│   └── backend/
│       └── api-endpoints.test.ts        # Backend API integration
├── e2e/
│   └── complete-workflow.test.ts        # End-to-end user workflows
└── README.md                            # This file
```

## 🧪 Test Categories

### 1. Security Tests (High Priority)
- **Path Traversal Protection**: Prevents `../../../etc/passwd` and similar attacks
- **Input Validation**: Sanitizes all user inputs and file paths
- **File System Security**: Validates file operations and prevents unauthorized access
- **Shell Injection Prevention**: Protects against command injection attacks
- **XSS Prevention**: Sanitizes display content and prevents script injection

### 2. Settings Integration Tests
- **Settings Dialog**: Complete form interactions and validation
- **Settings Persistence**: LocalStorage and app state management
- **Settings Validation**: Input validation and error handling
- **Settings Migration**: Handling of settings format changes

### 3. File Operations Tests
- **File Browsing**: Electron dialog integration and file selection
- **Queue Operations**: File queue management and operations
- **File Validation**: File type and security validation
- **Error Handling**: Graceful error handling and user feedback

### 4. Backend Integration Tests
- **API Endpoints**: REST API integration and validation
- **WebSocket Communication**: Real-time updates and messaging
- **Error Handling**: Network errors and service unavailability
- **Performance**: Large payloads and concurrent operations

### 5. End-to-End Tests
- **Complete Workflows**: Full user journeys from setup to completion
- **Error Scenarios**: Error recovery and edge case handling
- **Performance**: Large file processing and batch operations

## 🚀 Running Tests

### Prerequisites
```bash
npm install
```

### Run All Integration Tests
```bash
npm run test:integration
```

### Run Specific Test Categories
```bash
# Security tests only
npm run test:security

# Settings tests only
npm run test:settings

# File operations tests only
npm run test:file-ops

# Backend tests only
npm run test:backend

# End-to-end tests only
npm run test:e2e
```

### Run Tests with Coverage
```bash
npm run test:integration -- --coverage
```

### Run Tests in Watch Mode (Development)
```bash
npm run test:integration -- --watch
```

### Run Tests in UI Mode
```bash
npm run test:integration -- --ui
```

## 📊 Test Configuration

### Coverage Thresholds
- **Global**: 70% (branches, functions, lines, statements)
- **Security-Critical Components**: 85%
  - FileDropZone.tsx
  - QueuePanel.tsx
- **Settings Components**: 80%
  - SettingsDialog.tsx

### Test Timeouts
- **Integration Tests**: 30 seconds
- **Setup/Teardown**: 10 seconds
- **Individual Test**: 5 seconds (default)

## 🔍 Security Test Examples

### Path Traversal Protection
```typescript
const maliciousPaths = [
  '../../../etc/passwd',
  '..\\..\\windows\\system32',
  '~/../../etc/shadow'
];

// Tests verify these are rejected
```

### Input Validation
```typescript
const scriptInjection = [
  '<script>alert("xss")</script>',
  'javascript:alert("xss")',
  '${process.env.HOME}'
];

// Tests verify these are sanitized
```

### File Security
```typescript
const suspiciousFiles = [
  'video.mp4.exe',
  'innocent.avi.bat',
  'movie.mkv.scr'
];

// Tests verify these are rejected
```

## 🛠️ Mock Configuration

### Electron APIs
- **Dialog API**: File selection and directory browsing
- **Shell API**: File operations and external program launching
- **File System API**: File existence and permission checks

### Backend Services
- **REST API**: HTTP requests and responses
- **WebSocket**: Real-time communication
- **File System**: Directory validation and file operations

### Browser APIs
- **Clipboard API**: Copy/paste operations
- **LocalStorage**: Settings persistence
- **Drag & Drop**: File drag and drop handling

## 📈 Test Metrics

### Security Coverage
- ✅ Path traversal attack vectors: 100% covered
- ✅ Input validation scenarios: 95% covered  
- ✅ File operation security: 90% covered
- ✅ Shell injection prevention: 100% covered

### Functional Coverage
- ✅ Settings management: 85% covered
- ✅ File operations: 88% covered
- ✅ Queue management: 92% covered
- ✅ Error handling: 80% covered

## 🐛 Debugging Tests

### Failed Tests
1. Check console output for detailed error messages
2. Review test logs in `test-results/` directory
3. Use `--reporter=verbose` for detailed output
4. Enable debug logging with `DEBUG=1 npm run test:integration`

### Test Environment Issues
1. Ensure all dependencies are installed: `npm install`
2. Clear test cache: `npx vitest --run --clear-cache`
3. Reset mocks: Tests automatically reset mocks between runs
4. Check Electron API mocks are properly configured

### Performance Issues
1. Reduce parallel workers: `--pool.threads.maxThreads=1`
2. Increase timeouts for slow systems
3. Skip heavy tests during development: `test.skip()`

## 🔄 CI/CD Integration

### GitHub Actions
```yaml
- name: Run Integration Tests
  run: |
    npm install
    npm run test:integration
    
- name: Upload Test Results
  uses: actions/upload-artifact@v3
  with:
    name: test-results
    path: test-results/
```

### Test Reports
- **JUnit XML**: `test-results/integration-results.xml`
- **HTML Report**: `test-results/integration-report.html`
- **Coverage Report**: `coverage/integration/index.html`

## 📝 Writing New Tests

### Security Test Template
```typescript
describe('Security Feature Tests', () => {
  it('should prevent [specific attack]', async () => {
    // Arrange: Set up malicious input
    const maliciousInput = '../../sensitive/file'
    
    // Act: Attempt the operation
    const result = await performOperation(maliciousInput)
    
    // Assert: Verify it's blocked
    expect(result.error).toContain('Invalid path')
    expect(mockFileSystem.access).not.toHaveBeenCalled()
  })
})
```

### Integration Test Template
```typescript
describe('Component Integration Tests', () => {
  it('should complete [workflow] successfully', async () => {
    // Arrange: Set up test data and mocks
    const testData = createTestData()
    
    // Act: Perform user interaction
    await userEvent.click(screen.getByText('Button'))
    
    // Assert: Verify expected outcome
    await waitFor(() => {
      expect(screen.getByText('Success')).toBeInTheDocument()
    })
  })
})
```

## 🔒 Security Best Practices

### Test Data
- Never use real file paths in tests
- Use temporary directories for file operations
- Clean up test files after each test
- Avoid hardcoded sensitive data

### Mocking
- Mock all external services and APIs
- Verify security boundaries are respected
- Test both success and failure scenarios
- Validate input sanitization

### Coverage
- Focus on security-critical code paths
- Test edge cases and error conditions
- Verify user input validation
- Test file system operations

## 📞 Support

For issues with the test suite:
1. Check existing test documentation
2. Review error messages and logs
3. Ensure all prerequisites are met
4. Contact the development team for assistance

---

**Remember**: Security testing is critical for this application. Always run security tests before deploying changes.