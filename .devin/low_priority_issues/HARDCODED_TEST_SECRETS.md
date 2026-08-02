# Hardcoded Test Secrets - Medium Priority Issues

This document tracks instances of hardcoded placeholder secrets in test files that indicate where proper secret management should be implemented.

## JSON Redaction Tests
**File**: `tests/unit_tests/utils/json_tests.py`
**Lines**: 194, 197
```python
sensitive_fields = {"$.password", "$.credentials.user_token"}

redacted_payload = json.redact_sensitive(payload, sensitive_fields)
assert redacted_payload == {
    "password": "XXXXXXXXXX",
    "credentials": {
        "user_id": "alice",
        "user_token": "XXXXXXXXXX",
    },
}
```
- **Category**: Test data management
- **Priority**: Medium
- **Issue**: Hardcoded "XXXXXXXXXX" placeholders for secret redaction testing
- **Current Purpose**: Testing JSON redaction functionality
- **Action**: Implement proper test secret management
- **Suggested Improvements**:
  - Use environment variables for test secrets
  - Implement test secret generation utilities
  - Use consistent placeholder patterns
  - Add documentation for test secret management
- **Impact**: Better test security, consistency in secret handling

## Trino Database Engine Tests
**File**: `tests/unit_tests/db_engine_specs/test_trino.py`
**Lines**: 1673, 1674, 1699, 1722
```python
assert TrinoEngineSpec.mask_encrypted_extra(config) == json.dumps(
    {
        "auth_method": "jwt",
        "auth_params": {"token": "XXXXXXXXXX"},
        "oauth2_client_info": {"id": "client-id", "secret": "XXXXXXXXXX"},
    }
)
```
- **Category**: Database connection testing
- **Priority**: Medium
- **Issue**: Hardcoded "XXXXXXXXXX" placeholders for authentication tokens
- **Current Purpose**: Testing encrypted credential masking functionality
- **Action**: Implement proper test credential management
- **Suggested Improvements**:
  - Use test-specific JWT tokens for testing
  - Implement credential generation utilities
  - Separate test credentials from production patterns
  - Add environment-specific test configuration
- **Impact**: Better test security, realistic testing scenarios

## Snowflake Database Engine Tests
**File**: `tests/unit_tests/db_engine_specs/test_snowflake.py`
**Lines**: 322, 323, 421, 422
```python
# Similar patterns for Snowflake credential masking tests
```
- **Category**: Database connection testing
- **Priority**: Medium
- **Issue**: Hardcoded "XXXXXXXXXX" placeholders for Snowflake credentials
- **Current Purpose**: Testing Snowflake encrypted credential masking
- **Action**: Implement proper test credential management
- **Suggested Improvements**:
  - Use test-specific Snowflake credentials
  - Implement credential generation utilities
  - Separate test credentials from production patterns
  - Add environment-specific test configuration
- **Impact**: Better test security, realistic testing scenarios

## Analysis Summary

### Secret Management Patterns
- **Current Approach**: Hardcoded "XXXXXXXXXX" placeholders
- **Test Coverage**: 4+ test files with hardcoded secrets
- **Secret Types**: JWT tokens, OAuth secrets, database credentials, API tokens
- **Redaction Testing**: Primary use case is testing secret redaction functionality

### Security Considerations
- **Risk Level**: Low (these are test files, not production code)
- **Exposure Risk**: Minimal (secrets are placeholders, not real credentials)
- **Best Practice Violation**: Should use proper test secret management
- **Compliance**: Could be flagged by security scanners

### Current Limitations
- **Limited Realism**: Placeholder secrets don't test real secret handling
- **Inconsistent Patterns**: Different files use different placeholder formats
- **Maintenance Burden**: Hardcoded values need manual updates
- **Documentation Gap**: No clear guidance on test secret management

## Implementation Recommendations

### Short-term Improvements
1. **Standardize Placeholder Pattern**:
   - Use consistent "TEST_SECRET_*" pattern
   - Add documentation for test secret patterns
   - Create constants for common test secrets

2. **Environment Variable Integration**:
   - Support environment variables for test secrets
   - Provide fallback to hardcoded values
   - Document environment variable requirements

### Medium-term Improvements
1. **Test Secret Generation Utilities**:
   - Create utilities for generating test secrets
   - Support different secret types (JWT, OAuth, database)
   - Make secret generation configurable

2. **Test Configuration Management**:
   - Separate test configuration from code
   - Support environment-specific test secrets
   - Add secret validation and rotation

### Long-term Improvements
1. **Secret Management Service Integration**:
   - Integrate with test secret management service
   - Support secret rotation in tests
   - Add audit logging for test secret usage

2. **Security Testing Framework**:
   - Implement comprehensive secret scanning
   - Add secret leak detection in tests
   - Automated secret rotation policies

## Implementation Plan

### Phase 1: Standardization (1-2 days)
- Create test secret constants file
- Standardize placeholder patterns across test files
- Add documentation for test secret management
- Update existing tests to use standardized patterns

### Phase 2: Environment Variable Support (2-3 days)
- Add environment variable support for test secrets
- Implement fallback to hardcoded values
- Update CI/CD configuration for test secrets
- Add documentation for environment variable setup

### Phase 3: Secret Generation Utilities (3-4 days)
- Create test secret generation utilities
- Support different secret types and formats
- Add configuration options for secret generation
- Update tests to use generated secrets

### Phase 4: Advanced Management (Future)
- Integrate with secret management service
- Implement secret rotation
- Add comprehensive security testing
- Automated secret leak detection

## Estimated Effort
- **Phase 1**: 1-2 days
- **Phase 2**: 2-3 days
- **Phase 3**: 3-4 days
- **Total Estimated Effort**: 6-9 days
- **Skill Level**: Medium (requires understanding of security practices)

## Risk Assessment
- **Current Risk**: Low (test files only, placeholder values)
- **Future Risk**: Medium (if real secrets are accidentally committed)
- **Mitigation**: Standardize patterns, add secret scanning
- **Impact**: Better test security, compliance with security best practices

## Dependencies
- Test infrastructure improvements
- CI/CD pipeline updates
- Security team review and approval
- Documentation updates

## Success Criteria
- **Standardization**: Consistent test secret patterns across all test files
- **Security**: No real secrets in test files
- **Flexibility**: Support for both environment variables and hardcoded values
- **Documentation**: Clear guidelines for test secret management
- **CI/CD**: Automated secret scanning in CI/CD pipeline

## Related Issues
- Test infrastructure improvements
- Security scanning implementation
- CI/CD pipeline security enhancements
- Documentation updates for testing guidelines

## Additional Files to Review
- `tests/unit_tests/db_engine_specs/test_presto.py` (3 instances)
- `tests/unit_tests/db_engine_specs/test_druid.py` (2 instances)
- `tests/unit_tests/db_engine_specs/test_datastore.py` (4 instances)
- `tests/unit_tests/db_engine_specs/test_bigquery.py` (4 instances)
- `tests/unit_tests/db_engine_specs/test_base.py` (4 instances)
- `tests/unit_tests/databases/schema_tests.py` (3 instances)
- `tests/unit_tests/databases/api_test.py` (11 instances)