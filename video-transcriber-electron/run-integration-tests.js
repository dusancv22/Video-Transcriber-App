#!/usr/bin/env node

/**
 * Integration Test Runner
 * 
 * Comprehensive test runner for the Settings→Processing workflow integration tests.
 * Runs all test suites and generates detailed reports.
 */

const { spawn } = require('child_process')
const fs = require('fs')
const path = require('path')

// ANSI color codes for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m'
}

// Test suite configurations
const testSuites = [
  {
    name: 'Settings → Processing Flow',
    command: 'test:settings-flow',
    file: 'settings-processing-flow.test.ts',
    description: 'Tests complete workflow from Start button to processing execution',
    critical: true
  },
  {
    name: 'Settings Validation',
    command: 'test:settings-validation', 
    file: 'settings-validation.test.ts',
    description: 'Comprehensive validation tests for all settings form fields',
    critical: true
  },
  {
    name: 'First-Run Experience',
    command: 'test:first-run',
    file: 'first-run-flow.test.ts', 
    description: 'Tests first-run detection, welcome dialog, and setup flow',
    critical: false
  },
  {
    name: 'UI Components Integration',
    command: 'test:ui-components',
    file: 'ui-components.test.ts',
    description: 'Tests component integration and communication',
    critical: false
  }
]

// CLI options
const args = process.argv.slice(2)
const options = {
  coverage: args.includes('--coverage'),
  watch: args.includes('--watch'),
  ui: args.includes('--ui'),
  verbose: args.includes('--verbose'),
  suite: args.find(arg => arg.startsWith('--suite='))?.split('=')[1],
  help: args.includes('--help') || args.includes('-h')
}

function printHelp() {
  console.log(`
${colors.bright}Integration Test Runner${colors.reset}
${colors.cyan}Tests the complete Settings→Processing workflow integration${colors.reset}

${colors.bright}Usage:${colors.reset}
  node run-integration-tests.js [options]

${colors.bright}Options:${colors.reset}
  --coverage          Run tests with coverage reporting
  --watch            Run tests in watch mode
  --ui               Run tests with Vitest UI
  --verbose          Show detailed test output
  --suite=<name>     Run specific test suite only
  --help, -h         Show this help message

${colors.bright}Test Suites:${colors.reset}
${testSuites.map(suite => `  ${colors.green}${suite.name}${colors.reset}
    File: ${suite.file}
    Description: ${suite.description}
    Critical: ${suite.critical ? colors.red + 'Yes' + colors.reset : colors.yellow + 'No' + colors.reset}
  `).join('\n')}

${colors.bright}Examples:${colors.reset}
  ${colors.cyan}node run-integration-tests.js${colors.reset}
    Run all test suites

  ${colors.cyan}node run-integration-tests.js --coverage${colors.reset}
    Run all tests with coverage reporting

  ${colors.cyan}node run-integration-tests.js --suite="Settings Validation"${colors.reset}
    Run only the Settings Validation test suite

  ${colors.cyan}node run-integration-tests.js --ui --watch${colors.reset}
    Run tests with UI in watch mode
`)
}

function log(message, color = colors.reset) {
  console.log(color + message + colors.reset)
}

function logSection(title) {
  console.log('\n' + colors.bright + colors.cyan + '='.repeat(60) + colors.reset)
  console.log(colors.bright + colors.cyan + title + colors.reset)
  console.log(colors.bright + colors.cyan + '='.repeat(60) + colors.reset + '\n')
}

function runCommand(command, args = []) {
  return new Promise((resolve, reject) => {
    const child = spawn('npm', ['run', command, ...args], {
      stdio: options.verbose ? 'inherit' : 'pipe',
      shell: true
    })

    let stdout = ''
    let stderr = ''

    if (!options.verbose) {
      child.stdout?.on('data', (data) => {
        stdout += data.toString()
      })

      child.stderr?.on('data', (data) => {
        stderr += data.toString()
      })
    }

    child.on('close', (code) => {
      if (code === 0) {
        resolve({ stdout, stderr, code })
      } else {
        reject({ stdout, stderr, code })
      }
    })

    child.on('error', (error) => {
      reject({ error, code: -1 })
    })
  })
}

async function runTestSuite(suite) {
  log(`\n${colors.bright}Running: ${suite.name}${colors.reset}`)
  log(`${colors.cyan}Description: ${suite.description}${colors.reset}`)
  log(`${colors.yellow}File: tests/integration/${suite.file}${colors.reset}`)
  
  const startTime = Date.now()
  
  try {
    const commandArgs = []
    if (options.coverage) commandArgs.push('--coverage')
    if (options.watch) commandArgs.push('--watch')
    if (options.ui) commandArgs.push('--ui')
    
    const result = await runCommand(suite.command, commandArgs)
    const duration = Date.now() - startTime
    
    log(`${colors.green}✅ PASSED${colors.reset} (${duration}ms)`, colors.green)
    
    return {
      name: suite.name,
      status: 'passed',
      duration,
      critical: suite.critical,
      output: result.stdout
    }
  } catch (error) {
    const duration = Date.now() - startTime
    
    log(`${colors.red}❌ FAILED${colors.reset} (${duration}ms)`, colors.red)
    
    if (!options.verbose && error.stdout) {
      log('\nTest Output:', colors.yellow)
      console.log(error.stdout)
    }
    
    if (!options.verbose && error.stderr) {
      log('\nError Output:', colors.red)
      console.log(error.stderr)
    }
    
    return {
      name: suite.name,
      status: 'failed',
      duration,
      critical: suite.critical,
      error: error.stderr || error.error?.message || 'Unknown error',
      output: error.stdout
    }
  }
}

async function generateReport(results) {
  logSection('TEST RESULTS SUMMARY')
  
  const passed = results.filter(r => r.status === 'passed')
  const failed = results.filter(r => r.status === 'failed')
  const criticalFailed = failed.filter(r => r.critical)
  
  // Summary statistics
  log(`Total Test Suites: ${results.length}`)
  log(`${colors.green}Passed: ${passed.length}${colors.reset}`)
  log(`${colors.red}Failed: ${failed.length}${colors.reset}`)
  log(`${colors.red}Critical Failed: ${criticalFailed.length}${colors.reset}`)
  
  const totalDuration = results.reduce((sum, r) => sum + r.duration, 0)
  log(`Total Duration: ${totalDuration}ms`)
  
  // Detailed results
  console.log('\n' + colors.bright + 'Detailed Results:' + colors.reset)
  results.forEach(result => {
    const status = result.status === 'passed' 
      ? colors.green + '✅ PASSED' + colors.reset
      : colors.red + '❌ FAILED' + colors.reset
    
    const critical = result.critical 
      ? colors.red + ' [CRITICAL]' + colors.reset
      : colors.yellow + ' [NON-CRITICAL]' + colors.reset
    
    console.log(`  ${result.name}: ${status}${critical} (${result.duration}ms)`)
    
    if (result.status === 'failed' && result.error) {
      console.log(`    ${colors.red}Error: ${result.error}${colors.reset}`)
    }
  })
  
  // Integration workflow status
  console.log('\n' + colors.bright + 'Integration Workflow Status:' + colors.reset)
  
  if (criticalFailed.length === 0) {
    log('🎉 Settings→Processing workflow integration: ' + colors.green + 'WORKING' + colors.reset)
    log('✅ All critical integration points are functioning correctly')
    
    if (failed.length > 0) {
      log(`⚠️  ${failed.length} non-critical test(s) failed - these should be addressed but don't block the workflow`)
    }
  } else {
    log('🚨 Settings→Processing workflow integration: ' + colors.red + 'BROKEN' + colors.reset)
    log('❌ Critical integration failures detected:')
    
    criticalFailed.forEach(result => {
      log(`   - ${result.name}: ${result.error}`, colors.red)
    })
    
    log('\n💡 Recommended actions:')
    log('   1. Fix critical test failures first')
    log('   2. Verify settings dialog opens from Start button')
    log('   3. Check API integration and settings persistence')
    log('   4. Test validation error handling')
  }
  
  // Save report to file
  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      total: results.length,
      passed: passed.length,
      failed: failed.length,
      criticalFailed: criticalFailed.length,
      duration: totalDuration
    },
    results,
    workflowStatus: criticalFailed.length === 0 ? 'working' : 'broken'
  }
  
  const reportPath = path.join(__dirname, 'test-results', 'integration-report.json')
  
  // Ensure test-results directory exists
  const testResultsDir = path.join(__dirname, 'test-results')
  if (!fs.existsSync(testResultsDir)) {
    fs.mkdirSync(testResultsDir, { recursive: true })
  }
  
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2))
  log(`\n📊 Report saved to: ${reportPath}`)
  
  return criticalFailed.length === 0
}

async function main() {
  if (options.help) {
    printHelp()
    return
  }
  
  logSection('Settings→Processing Integration Test Runner')
  
  log('🧪 Testing comprehensive settings→processing workflow integration')
  log('📋 Verifying all fixes are working correctly together')
  
  if (options.coverage) log('📊 Coverage reporting enabled')
  if (options.watch) log('👀 Watch mode enabled')
  if (options.ui) log('🎨 UI mode enabled')
  if (options.verbose) log('📝 Verbose output enabled')
  
  // Determine which suites to run
  let suitesToRun = testSuites
  if (options.suite) {
    const requestedSuite = testSuites.find(s => s.name === options.suite)
    if (!requestedSuite) {
      log(`❌ Unknown test suite: ${options.suite}`, colors.red)
      log('Available suites:', colors.yellow)
      testSuites.forEach(s => log(`  - ${s.name}`))
      process.exit(1)
    }
    suitesToRun = [requestedSuite]
    log(`🎯 Running single suite: ${options.suite}`)
  }
  
  // Run test suites
  const results = []
  
  for (const suite of suitesToRun) {
    const result = await runTestSuite(suite)
    results.push(result)
    
    // Stop on critical failure unless in watch/ui mode
    if (result.status === 'failed' && result.critical && !options.watch && !options.ui) {
      log('\n🛑 Critical test suite failed. Stopping execution.', colors.red)
      log('💡 Fix critical issues before continuing with other tests.', colors.yellow)
      break
    }
  }
  
  // Generate final report
  const success = await generateReport(results)
  
  // Exit with appropriate code
  process.exit(success ? 0 : 1)
}

// Handle uncaught errors
process.on('uncaughtException', (error) => {
  log('💥 Uncaught Exception:', colors.red)
  console.error(error)
  process.exit(1)
})

process.on('unhandledRejection', (reason, promise) => {
  log('💥 Unhandled Rejection:', colors.red)
  console.error('At:', promise, 'reason:', reason)
  process.exit(1)
})

// Run the main function
main().catch((error) => {
  log('💥 Test runner failed:', colors.red)
  console.error(error)
  process.exit(1)
})