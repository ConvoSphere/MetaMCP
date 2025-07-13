# MetaMCP CLI Tests

This directory contains comprehensive tests for the MetaMCP CLI tool, covering unit tests, integration tests, and performance tests.

## Test Structure

```
tests/
├── unit/
│   ├── test_cli.py              # Main CLI unit tests
│   ├── test_cli_utils.py        # CLI utilities unit tests
│   └── performance/
│       └── test_cli_performance.py  # Performance tests
├── integration/
│   └── test_cli_integration.py  # Integration tests
├── run_cli_tests.py             # Test runner script
└── README_CLI_TESTS.md         # This file
```

## Test Categories

### 1. Unit Tests (`tests/unit/`)

**test_cli.py**
- Tests the main CLI class (`MetaMCPCLI`)
- Command parsing and argument handling
- Error handling and exception management
- Mock-based testing of CLI functionality

**test_cli_utils.py**
- Tests utility modules (DockerUtils, TestUtils, DocsUtils)
- Environment validation functions
- File operations and command execution
- Mock-based testing of utility functions

### 2. Integration Tests (`tests/integration/`)

**test_cli_integration.py**
- Real file operations with temporary project structures
- End-to-end command execution testing
- Environment file handling
- Error scenarios with invalid configurations

### 3. Performance Tests (`tests/unit/performance/`)

**test_cli_performance.py**
- Execution time measurements
- Memory usage monitoring
- Resource consumption analysis
- Memory leak detection
- CPU and disk I/O performance

## Running Tests

### Prerequisites

Install required test dependencies:

```bash
pip install pytest psutil pytest-json-report
```

### Running All Tests

Use the test runner script:

```bash
python tests/run_cli_tests.py
```

This will:
- Check for required dependencies
- Run all test suites
- Generate a comprehensive report
- Save detailed results to JSON files

### Running Individual Test Suites

**Unit Tests:**
```bash
pytest tests/unit/test_cli.py -v
pytest tests/unit/test_cli_utils.py -v
```

**Integration Tests:**
```bash
pytest tests/integration/test_cli_integration.py -v
```

**Performance Tests:**
```bash
pytest tests/unit/performance/test_cli_performance.py -v
```

### Running Specific Test Categories

**Only Unit Tests:**
```bash
pytest tests/unit/ -v
```

**Only Integration Tests:**
```bash
pytest tests/integration/ -v
```

**Only Performance Tests:**
```bash
pytest tests/unit/performance/ -v
```

## Test Configuration

### Environment Setup

Tests use temporary directories to avoid affecting the actual project:

- Each test creates its own temporary project structure
- Environment files are created with test data
- Docker operations are mocked to avoid system dependencies
- File operations are isolated in temporary directories

### Mocking Strategy

**Subprocess Operations:**
- Docker commands are mocked to return controlled responses
- File system operations use temporary directories
- Network operations are mocked to avoid external dependencies

**External Dependencies:**
- Database connections are mocked
- API calls are intercepted
- System calls are controlled

### Performance Benchmarks

The performance tests establish baseline metrics:

- **Initialization Time:** < 1.0 seconds
- **Memory Usage:** < 50MB for initialization
- **Command Execution:** < 0.1 seconds for simple commands
- **File Operations:** < 2.0 seconds for 50 operations
- **Memory Leaks:** < 20MB increase after 100 operations

## Test Reports

### Console Output

The test runner provides:
- Real-time progress updates
- Execution time for each test suite
- Success/failure status
- Error details for failed tests

### JSON Reports

Detailed results are saved to:
```
tests/cli_test_results_YYYYMMDD_HHMMSS.json
```

Report includes:
- Test type and description
- Execution time
- Return codes
- Standard output and error streams
- Success/failure status

## Test Coverage

### CLI Functionality Covered

**Core CLI Operations:**
- [x] Command parsing and argument handling
- [x] Environment validation
- [x] Docker operations (status, logs, build, etc.)
- [x] Development setup and dependency management
- [x] Testing operations (unit, integration, etc.)
- [x] Quality checks (linting, formatting)
- [x] Documentation operations
- [x] Update and reset functionality

**Utility Functions:**
- [x] Docker utilities (container management, health checks)
- [x] Test utilities (test execution, coverage analysis)
- [x] Documentation utilities (build, serve, deploy)
- [x] Environment validation and file operations

**Error Handling:**
- [x] Invalid command handling
- [x] Missing file scenarios
- [x] Network timeout handling
- [x] Permission error handling
- [x] Resource exhaustion scenarios

### Performance Metrics

**Resource Usage:**
- [x] Memory consumption monitoring
- [x] CPU usage analysis
- [x] Disk I/O performance
- [x] Memory leak detection

**Execution Time:**
- [x] CLI initialization performance
- [x] Command execution speed
- [x] File operation efficiency
- [x] Large file handling

## Troubleshooting

### Common Issues

**Missing Dependencies:**
```bash
pip install pytest psutil pytest-json-report
```

**Permission Errors:**
- Ensure write permissions in the tests directory
- Run with appropriate user privileges

**Timeout Issues:**
- Performance tests may timeout on slow systems
- Increase timeout values in test configuration

**Memory Issues:**
- Performance tests monitor memory usage
- Large memory increases indicate potential leaks

### Debug Mode

Run tests with verbose output:

```bash
pytest -v -s --tb=long
```

### Isolated Testing

Run a single test:

```bash
pytest tests/unit/test_cli.py::TestMetaMCPCLI::test_cli_initialization -v
```

## Contributing

### Adding New Tests

1. **Unit Tests:** Add to appropriate `test_*.py` file
2. **Integration Tests:** Create new test class in integration directory
3. **Performance Tests:** Add to performance test file

### Test Guidelines

- Use descriptive test names
- Include docstrings explaining test purpose
- Mock external dependencies
- Use temporary directories for file operations
- Clean up resources after tests
- Follow existing naming conventions

### Test Data

- Use realistic but minimal test data
- Avoid hardcoded paths
- Use temporary files for testing
- Mock system calls appropriately

## Continuous Integration

The test suite is designed to run in CI environments:

- No external dependencies required
- Deterministic test results
- Comprehensive error reporting
- Performance regression detection

## Performance Monitoring

Regular performance testing helps identify:

- Memory leaks in CLI operations
- Performance regressions
- Resource usage patterns
- Optimization opportunities

Run performance tests regularly:

```bash
python tests/run_cli_tests.py
```

Check the generated reports for performance trends and anomalies. 