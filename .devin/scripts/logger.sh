#!/bin/bash
###############################################################################
# Devin Auto-Fix Logger
# 
# Provides structured, observable logging for the Devin automation process.
# Outputs JSON-formatted logs for technical monitoring and analysis.
###############################################################################

set -e

# Configuration
LOG_DIR=".devin/logs"
LOG_FILE="$LOG_DIR/devin-autofix-$(date +%Y%m%d-%H%M%S).log"
JSON_LOG_FILE="$LOG_DIR/devin-autofix-$(date +%Y%m%d-%H%M%S).json"

# Create log directory
mkdir -p "$LOG_DIR"

# JSON logging function
log_json() {
    local level=$1
    local message=$2
    local data=$3
    
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local log_entry="{\"timestamp\":\"$timestamp\",\"level\":\"$level\",\"message\":\"$message\""
    
    if [ -n "$data" ]; then
        log_entry="$log_entry,\"data\":$data"
    fi
    
    log_entry="$log_entry}"
    
    echo "$log_entry" >> "$JSON_LOG_FILE"
    
    # Also output to stdout for immediate visibility
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message"
}

# Step logging with progress tracking
log_step() {
    local step_name=$1
    local status=$2
    local details=$3
    
    local step_data="{\"step\":\"$step_name\",\"status\":\"$status\""
    
    if [ -n "$details" ]; then
        step_data="$step_data,\"details\":$details"
    fi
    
    step_data="$step_data}"
    
    log_json "STEP" "$step_name" "$step_data"
}

# File operation logging
log_file_operation() {
    local operation=$1
    local file_path=$2
    local success=$3
    
    local file_data="{\"operation\":\"$operation\",\"file\":\"$file_path\",\"success\":$success}"
    log_json "FILE_OP" "$operation on $file_path" "$file_data"
}

# Test result logging
log_test_result() {
    local test_name=$1
    local passed=$2
    local duration=$3
    
    local test_data="{\"test\":\"$test_name\",\"passed\":$passed,\"duration_ms\":$duration}"
    log_json "TEST" "$test_name" "$test_data"
}

# Command execution logging
log_command() {
    local command=$1
    local exit_code=$2
    local duration=$3
    
    local cmd_data="{\"command\":\"$command\",\"exit_code\":$exit_code,\"duration_ms\":$duration}"
    log_json "COMMAND" "Executed: $command" "$cmd_data"
}

# Error logging with context
log_error_context() {
    local error_message=$1
    local context=$2
    local file=$3
    local line=$4
    
    local error_data="{\"error\":\"$error_message\""
    
    if [ -n "$context" ]; then
        error_data="$error_data,\"context\":\"$context\""
    fi
    
    if [ -n "$file" ]; then
        error_data="$error_data,\"file\":\"$file\""
    fi
    
    if [ -n "$line" ]; then
        error_data="$error_data,\"line\":$line"
    fi
    
    error_data="$error_data}"
    
    log_json "ERROR" "$error_message" "$error_data"
}

# Summary generation
generate_summary() {
    local total_steps=$1
    local successful_steps=$2
    local failed_steps=$3
    local total_duration=$4
    
    local summary_data="{\"total_steps\":$total_steps,\"successful\":$successful_steps,\"failed\":$failed_steps,\"total_duration_ms\":$total_duration}"
    log_json "SUMMARY" "Automation completed" "$summary_data"
}

# Export functions for use in other scripts
export -f log_json
export -f log_step
export -f log_file_operation
export -f log_test_result
export -f log_command
export -f log_error_context
export -f generate_summary

# Initialize log file
echo "[]" > "$JSON_LOG_FILE"
echo "Devin Auto-Fix Log: $LOG_FILE" > "$LOG_FILE"
echo "JSON Log: $JSON_LOG_FILE" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
