# Integration Tests: Settings → Processing Workflow

This directory contains comprehensive integration tests that verify the complete settings→processing workflow is working correctly after implementing the recent fixes to the Video Transcriber App.

## Test Suites Overview

### 🔄 **Settings → Processing Flow** (`settings-processing-flow.test.ts`)
**Purpose:** Verifies the complete workflow from opening the Start button to processing execution.

**Key Test Areas:**
- **Start Button Workflow:** Verifies Start button opens Settings Dialog
- **Settings Persistence:** Confirms settings are saved to localStorage and persist across sessions
- **API Integration:** Tests that `startProcessing()` is called with correct ProcessingOptions
- **Error Handling:** Validates error scenarios and recovery mechanisms
- **Loading States:** Ensures proper UI feedback during operations

**Critical Success Criteria:**
- ✅ Start button correctly opens Settings Dialog
- ✅ Settings are properly validated and saved
- ✅ API calls include correct ProcessingOptions payload
- ✅ Settings persist between app sessions
- ✅ Error handling works for invalid configurations

---

### ✅ **Settings Validation** (`settings-validation.test.ts`)
**Purpose:** Comprehensive validation tests for all settings form fields and scenarios.

**Key Test Areas:**
- **Output Directory Validation:** Tests path format, required fields, and accessibility
- **Settings Form Validation:** Validates all form fields and their interactions
- **Real-time Feedback:** Tests immediate validation feedback as users type
- **Error Recovery:** Ensures validation errors clear properly
- **Accessibility:** Confirms screen reader support and keyboard navigation

**Critical Success Criteria:**
- ✅ All required fields are properly validated
- ✅ Invalid input shows clear error messages
- ✅ Validation errors clear when input becomes valid
- ✅ Form maintains state during validation
- ✅ Accessibility standards are met

---

### 🚀 **First-Run Experience** (`first-run-flow.test.ts`)
**Purpose:** Tests the complete first-run experience workflow and system integration.

**Key Test Areas:**
- **First-Run Detection:** Tests detection when no settings exist
- **Welcome Dialog Flow:** Validates welcome experience and user guidance
- **Default Settings:** Tests system capability detection and appropriate defaults
- **Settings Configuration:** Ensures smooth transition from welcome to settings
- **Completion:** Verifies first-run completion and normal app state transition

**Critical Success Criteria:**
- ✅ First-run is properly detected and handled
- ✅ Welcome dialog guides users appropriately
- ✅ System capabilities influence default settings
- ✅ First-run completes successfully
- ✅ App transitions to normal state after setup

---

### 🎨 **UI Components Integration** (`ui-components.test.ts`)
**Purpose:** Tests integration between UI components and their interactions.

**Key Test Areas:**
- **SettingsStatusPanel:** Tests current settings display and real-time updates
- **Enhanced Settings Dialog:** Tests all form fields, validation, and help text
- **Component Communication:** Verifies data flow between components
- **Responsive Design:** Tests behavior across different screen sizes
- **Theming:** Ensures consistent theme application

**Critical Success Criteria:**
- ✅ SettingsStatusPanel displays current settings accurately
- ✅ Settings Dialog shows validation feedback clearly
- ✅ Components communicate properly through the store
- ✅ UI adapts to different screen sizes
- ✅ Consistent theming across all components

## Running the Tests

### Individual Test Suites
```bash
# Run specific test suite
npm run test:settings-flow      # Settings → Processing Flow
npm run test:settings-validation # Settings Validation  
npm run test:first-run         # First-Run Experience
npm run test:ui-components     # UI Components Integration

# Run all settings-related tests together
npm run test:settings-suite
```

### Integration Test Options
```bash
# Run all integration tests
npm run test:integration

# Run with UI for debugging
npm run test:integration:ui

# Run with coverage reporting
npm run test:integration:coverage

# Run specific test file patterns
npx vitest tests/integration/settings-*.test.ts
```

### Debugging Tests
```bash
# Run tests in watch mode
npm run test:settings-flow -- --watch

# Run tests with verbose output
npm run test:integration -- --reporter=verbose

# Run single test case
npx vitest -t "should open Settings Dialog when Start button is clicked"
```

## Mock Setup and Requirements

### Electron API Mocks
The tests mock all Electron APIs to avoid requiring a full Electron environment:

```typescript
// Mock Electron APIs
window.electronAPI = {
  dialog: {
    showOpenDialog: vi.fn().mockResolvedValue({
      canceled: false,
      filePaths: ['/mock/path/to/directory']
    })
  },
  path: {
    getDefaultOutputDirectory: vi.fn().mockResolvedValue('/mock/documents/VideoTranscriber'),
    getUserDocumentsPath: vi.fn().mockResolvedValue('/mock/documents')
  }
}
```

### API Service Mocks
Backend API calls are mocked to test frontend integration:

```typescript
// Mock VideoTranscriberAPI
jest.mock('../src/services/api', () => ({
  VideoTranscriberAPI: {
    startProcessing: vi.fn().mockResolvedValue({ success: true }),
    getStatus: vi.fn().mockResolvedValue({ status: 'ready' })
  }
}))
```

### Store Mocking
Zustand store is mocked to control test scenarios:

```typescript
// Mock app store
vi.mock('../src/store/appStore')
const mockUseAppStore = vi.mocked(useAppStore)

mockUseAppStore.mockReturnValue({
  processingOptions: mockSettings,
  setProcessingOptions: vi.fn(),
  startProcessing: vi.fn()
  // ... other store methods
})
```

## Integration Points Tested

### Settings Dialog ↔ App Store ↔ API Service ↔ Backend
- Settings changes flow through store to API
- API responses update store state
- Store changes reflect in UI components
- Error states propagate correctly

### MainWindow ↔ SettingsStatusPanel ↔ Settings Dialog
- Start button opens Settings Dialog
- Settings status panel shows current configuration
- Dialog changes update status panel display
- Component state synchronization

### FirstRunWelcome ↔ Settings Dialog ↔ Processing Flow
- Welcome flow guides to settings
- Settings configured during first-run
- First-run completion enables processing
- Smooth transition to normal app state

### Electron APIs ↔ Path Resolution ↔ Settings Storage
- Directory browsing integration
- Default path resolution
- Settings persistence to localStorage
- Cross-platform path handling

## Expected Integration Test Results

### Success Criteria Summary
When all tests pass, this confirms:

1. **Complete Workflow Integration**: Start button → Settings Dialog → API calls → Processing
2. **Settings Persistence**: Configuration survives app restarts and handles corruption
3. **Validation System**: All settings fields validated with clear user feedback
4. **First-Run Experience**: New users are guided through setup appropriately
5. **Component Communication**: UI components properly sync through the store
6. **Error Handling**: Graceful handling of API failures and validation errors
7. **Responsive Design**: UI works across different screen sizes
8. **Accessibility**: Keyboard navigation and screen reader support

### Coverage Targets
- **Settings Flow**: 85%+ coverage on critical path components
- **Validation**: 90%+ coverage on form validation logic
- **First-Run**: 80%+ coverage on setup and detection logic
- **UI Components**: 80%+ coverage on component integration

## Troubleshooting

### Common Issues

**Test fails with "Cannot read properties of undefined":**
- Check that all required store methods are mocked
- Verify Electron APIs are properly mocked
- Ensure component props are provided

**Settings Dialog not opening:**
- Verify `setSettingsOpen` mock is called with `true`
- Check that button click events are properly triggered
- Ensure store state includes `settingsOpen: false` initially

**Validation not working:**
- Check that form blur events are fired after input changes
- Verify validation functions are called with correct parameters
- Ensure error messages are properly rendered in DOM

**API calls not being made:**
- Verify API service mocks are properly configured
- Check that processing options are passed correctly
- Ensure async operations are properly awaited in tests

### Debug Tips

1. **Use `screen.debug()`** to see current DOM state
2. **Add `console.log` statements** in mock functions to trace calls
3. **Use `waitFor()` for async operations** that update the DOM
4. **Check mock call counts** with `expect(mockFn).toHaveBeenCalledTimes(n)`
5. **Verify mock call arguments** with `expect(mockFn).toHaveBeenCalledWith(expectedArgs)`

## Contributing

When adding new integration tests:

1. **Follow naming conventions**: `feature-name.test.ts`
2. **Group related tests** with `describe()` blocks
3. **Use descriptive test names** that explain the scenario
4. **Mock external dependencies** consistently
5. **Test both success and error paths**
6. **Include accessibility testing** where relevant
7. **Add appropriate timeouts** for async operations
8. **Document complex test scenarios** with comments

These integration tests ensure the complete settings→processing workflow functions as expected and provide confidence that the recent fixes are working correctly together.