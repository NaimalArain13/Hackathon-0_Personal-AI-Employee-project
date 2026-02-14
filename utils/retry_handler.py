"""
Retry handler with exponential backoff and circuit breaker pattern.
Implements robust error handling for Gold Tier MCP server calls.

Constitutional Compliance:
    - Principle X: NO auto-retry for destructive operations (create/post/payment)
    - Only read operations and status checks should retry
"""

import time
import random
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Any, Optional, List, Tuple
from collections import deque
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation, requests pass through
    OPEN = "open"          # Too many failures, reject requests immediately
    HALF_OPEN = "half_open"  # Testing if service recovered, allow limited requests


class OperationType(Enum):
    """Operation type for retry policy decisions."""
    READ = "read"          # GET operations, status checks - YES retry
    WRITE = "write"        # POST/PUT/DELETE operations - NO retry (destructive)
    IDEMPOTENT = "idempotent"  # Safe to retry (e.g., PUT with idempotency key)


def exponential_backoff_with_jitter(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter_percent: float = 0.1
) -> float:
    """
    Calculate exponential backoff delay with jitter.

    Args:
        attempt: Current retry attempt number (0-indexed)
        base_delay: Base delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        jitter_percent: Jitter percentage (default: 0.1 = 10%)

    Returns:
        Delay in seconds with jitter applied

    Example:
        attempt=0 → ~1.0s
        attempt=1 → ~2.0s
        attempt=2 → ~4.0s
        attempt=3 → ~8.0s
        attempt=4 → ~16.0s
        attempt=5 → ~32.0s
        attempt=6 → ~60.0s (capped at max_delay)
    """
    # Exponential backoff: base * (2 ^ attempt)
    delay = min(base_delay * (2 ** attempt), max_delay)

    # Add jitter to prevent thundering herd
    jitter = random.uniform(0, delay * jitter_percent)

    return delay + jitter


def retry_with_backoff(
    func: Callable,
    max_attempts: int = 5,
    operation_type: OperationType = OperationType.READ,
    exceptions: Tuple[type, ...] = (Exception,),
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    on_retry: Optional[Callable[[int, Exception], None]] = None
) -> Any:
    """
    Retry a function with exponential backoff.

    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts (default: 5)
        operation_type: Type of operation for retry policy
        exceptions: Tuple of exceptions to catch
        base_delay: Base delay for backoff (default: 1.0s)
        max_delay: Maximum delay (default: 60.0s)
        on_retry: Optional callback(attempt, exception) called before each retry

    Returns:
        Result of func() if successful

    Raises:
        Last exception if all attempts fail

    Constitutional Compliance:
        - WRITE operations: max_attempts forced to 1 (NO retry per Principle X)
        - READ operations: retry with exponential backoff (safe)
    """
    # Constitutional enforcement: NO retry for destructive operations
    if operation_type == OperationType.WRITE:
        logger.warning(
            f"WRITE operation detected - forcing max_attempts=1 (NO retry per Principle X)"
        )
        max_attempts = 1

    last_exception = None

    for attempt in range(max_attempts):
        try:
            result = func()
            if attempt > 0:
                logger.info(f"Retry successful after {attempt} attempts")
            return result

        except exceptions as e:
            last_exception = e

            # If this is the last attempt, raise the exception
            if attempt == max_attempts - 1:
                logger.error(f"All {max_attempts} attempts failed: {e}")
                raise

            # Calculate backoff delay
            delay = exponential_backoff_with_jitter(attempt, base_delay, max_delay)

            # Log retry attempt
            logger.warning(
                f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                f"Retrying in {delay:.2f}s..."
            )

            # Call retry callback if provided
            if on_retry:
                on_retry(attempt, e)

            # Wait before retry
            time.sleep(delay)

    # This should never be reached, but just in case
    raise last_exception


class CircuitBreaker:
    """
    Circuit breaker implementation to prevent cascading failures.

    States:
        - CLOSED: Normal operation, all requests pass through
        - OPEN: Too many failures, requests fail immediately without trying
        - HALF_OPEN: Testing recovery, allow limited requests

    Thresholds:
        - Failure threshold: 5 failures in 60 seconds → Open
        - Timeout: 30 seconds in Open state → Half-Open
        - Success threshold: 2 consecutive successes → Closed
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: int = 30,
        window_seconds: int = 60
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Service/circuit name for logging
            failure_threshold: Failures in window to trigger OPEN state
            success_threshold: Successes in HALF_OPEN to return to CLOSED
            timeout_seconds: Seconds in OPEN before trying HALF_OPEN
            window_seconds: Time window for failure counting
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds
        self.window_seconds = window_seconds

        self.state = CircuitState.CLOSED
        self.failure_times: deque = deque()  # Timestamps of recent failures
        self.success_count = 0  # Consecutive successes in HALF_OPEN state
        self.opened_at: Optional[datetime] = None

        logger.info(f"Circuit breaker '{name}' initialized in CLOSED state")

    def _clean_old_failures(self):
        """Remove failures outside the time window."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.window_seconds)
        while self.failure_times and self.failure_times[0] < cutoff:
            self.failure_times.popleft()

    def _should_open(self) -> bool:
        """Check if circuit should open based on failure threshold."""
        self._clean_old_failures()
        return len(self.failure_times) >= self.failure_threshold

    def _should_try_half_open(self) -> bool:
        """Check if enough time has passed to try HALF_OPEN state."""
        if self.opened_at is None:
            return False
        elapsed = (datetime.utcnow() - self.opened_at).total_seconds()
        return elapsed >= self.timeout_seconds

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args, **kwargs: Arguments to pass to function

        Returns:
            Result of func(*args, **kwargs)

        Raises:
            CircuitBreakerOpenError: If circuit is OPEN
            Exception: Any exception raised by func
        """
        # Check current state
        if self.state == CircuitState.OPEN:
            if self._should_try_half_open():
                logger.info(f"Circuit '{self.name}': OPEN → HALF_OPEN (testing recovery)")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit '{self.name}' is OPEN. Service unavailable."
                )

        # Try to execute the function
        try:
            result = func(*args, **kwargs)

            # Record success
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                logger.info(
                    f"Circuit '{self.name}': Success {self.success_count}/{self.success_threshold} "
                    f"in HALF_OPEN state"
                )

                # Check if we should close the circuit
                if self.success_count >= self.success_threshold:
                    logger.info(f"Circuit '{self.name}': HALF_OPEN → CLOSED (service recovered)")
                    self.state = CircuitState.CLOSED
                    self.failure_times.clear()
                    self.opened_at = None

            return result

        except Exception as e:
            # Record failure
            self.failure_times.append(datetime.utcnow())

            if self.state == CircuitState.HALF_OPEN:
                # Immediate transition to OPEN on failure in HALF_OPEN
                logger.warning(f"Circuit '{self.name}': HALF_OPEN → OPEN (recovery failed)")
                self.state = CircuitState.OPEN
                self.opened_at = datetime.utcnow()
                self.success_count = 0

            elif self.state == CircuitState.CLOSED:
                # Check if we should open the circuit
                if self._should_open():
                    logger.error(
                        f"Circuit '{self.name}': CLOSED → OPEN "
                        f"({len(self.failure_times)} failures in {self.window_seconds}s)"
                    )
                    self.state = CircuitState.OPEN
                    self.opened_at = datetime.utcnow()

            raise

    def reset(self):
        """Manually reset circuit breaker to CLOSED state."""
        logger.info(f"Circuit '{self.name}': Manual reset → CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_times.clear()
        self.success_count = 0
        self.opened_at = None

    def get_state(self) -> dict:
        """Get current circuit breaker state for monitoring."""
        self._clean_old_failures()
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": len(self.failure_times),
            "failure_threshold": self.failure_threshold,
            "success_count": self.success_count,
            "success_threshold": self.success_threshold,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None
        }


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is in OPEN state."""
    pass


class RateLimitError(Exception):
    """Exception raised when API rate limit is hit."""
    pass


def detect_rate_limit(exception: Exception) -> bool:
    """
    Detect if an exception is a rate limit error.

    Args:
        exception: Exception to check

    Returns:
        True if this is a rate limit error
    """
    # Common rate limit indicators
    rate_limit_keywords = [
        "rate limit",
        "too many requests",
        "quota exceeded",
        "429",  # HTTP status code
        "throttled",
        "rate exceeded"
    ]

    error_message = str(exception).lower()
    return any(keyword in error_message for keyword in rate_limit_keywords)


def handle_rate_limit(
    exception: Exception,
    base_delay: float = 60.0,
    max_delay: float = 300.0
) -> float:
    """
    Calculate appropriate backoff delay for rate limit errors.

    Args:
        exception: Rate limit exception
        base_delay: Base delay in seconds (default: 60s)
        max_delay: Maximum delay in seconds (default: 300s = 5 minutes)

    Returns:
        Delay in seconds before retry

    Note:
        Tries to extract retry-after header if available in exception.
    """
    # Try to extract Retry-After from exception message
    retry_after = None
    error_message = str(exception)

    # Common patterns: "Retry after 120 seconds", "retry-after: 60"
    import re
    patterns = [
        r'retry[- ]after[:\s]+(\d+)',
        r'wait[:\s]+(\d+)',
        r'in[:\s]+(\d+)\s*seconds?'
    ]

    for pattern in patterns:
        match = re.search(pattern, error_message, re.IGNORECASE)
        if match:
            retry_after = int(match.group(1))
            break

    if retry_after:
        delay = min(retry_after, max_delay)
        logger.warning(f"Rate limit hit. Retry-After header: {retry_after}s, using {delay}s")
    else:
        delay = base_delay
        logger.warning(f"Rate limit hit. No Retry-After header, using default {delay}s")

    return delay


# Global circuit breakers for each service (singleton pattern)
_circuit_breakers = {}


def get_circuit_breaker(service_name: str) -> CircuitBreaker:
    """
    Get or create a circuit breaker for a service.

    Args:
        service_name: Name of the service (e.g., "odoo", "facebook", "twitter")

    Returns:
        CircuitBreaker instance for the service
    """
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = CircuitBreaker(name=service_name)
        logger.info(f"Created circuit breaker for service '{service_name}'")

    return _circuit_breakers[service_name]


def get_all_circuit_states() -> List[dict]:
    """
    Get states of all circuit breakers for monitoring.

    Returns:
        List of circuit breaker state dictionaries
    """
    return [cb.get_state() for cb in _circuit_breakers.values()]


if __name__ == "__main__":
    # Example usage and testing
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== Exponential Backoff with Jitter Test ===")
    for i in range(7):
        delay = exponential_backoff_with_jitter(i)
        print(f"Attempt {i}: {delay:.2f}s")

    print("\n=== Retry with Backoff Test (READ operation) ===")
    attempt_count = [0]  # Use list to allow mutation in nested function

    def flaky_function():
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            raise ConnectionError(f"Simulated failure {attempt_count[0]}")
        return "Success!"

    try:
        result = retry_with_backoff(
            flaky_function,
            max_attempts=5,
            operation_type=OperationType.READ,
            exceptions=(ConnectionError,),
            base_delay=0.1  # Fast for testing
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed: {e}")

    print("\n=== Retry with Backoff Test (WRITE operation - NO retry) ===")
    write_attempt_count = [0]  # Use list to allow mutation in nested function

    def write_function():
        write_attempt_count[0] += 1
        raise ValueError(f"Write failed (attempt {write_attempt_count[0]})")

    try:
        result = retry_with_backoff(
            write_function,
            max_attempts=5,  # Will be forced to 1
            operation_type=OperationType.WRITE,
            exceptions=(ValueError,)
        )
    except ValueError as e:
        print(f"Expected failure: {e}")
        print(f"Write attempts: {write_attempt_count[0]} (should be 1)")

    print("\n=== Circuit Breaker Test ===")
    cb = CircuitBreaker(name="test_service", failure_threshold=3, timeout_seconds=2)

    def failing_service():
        raise RuntimeError("Service is down")

    # Trigger failures to open circuit
    for i in range(5):
        try:
            cb.call(failing_service)
        except (RuntimeError, CircuitBreakerOpenError):
            print(f"Attempt {i+1}: Service failed")
            print(f"Circuit state: {cb.get_state()['state']}")

    # Circuit should be OPEN now
    try:
        cb.call(failing_service)
    except CircuitBreakerOpenError as e:
        print(f"\nCircuit is OPEN: {e}")

    # Wait for timeout and test HALF_OPEN
    print(f"\nWaiting {cb.timeout_seconds}s for HALF_OPEN...")
    time.sleep(cb.timeout_seconds)

    def working_service():
        return "Service recovered!"

    # Should transition to HALF_OPEN and then CLOSED
    for i in range(3):
        try:
            result = cb.call(working_service)
            print(f"Attempt {i+1}: {result}")
            print(f"Circuit state: {cb.get_state()['state']}")
        except Exception as e:
            print(f"Error: {e}")

    print("\n=== Rate Limit Detection Test ===")
    rate_limit_errors = [
        Exception("HTTP 429: Too Many Requests"),
        Exception("Rate limit exceeded. Retry after 120 seconds"),
        Exception("API quota exceeded for today"),
    ]

    for error in rate_limit_errors:
        is_rate_limit = detect_rate_limit(error)
        print(f"'{error}' → Rate limit: {is_rate_limit}")
        if is_rate_limit:
            delay = handle_rate_limit(error)
            print(f"  Suggested delay: {delay}s")
