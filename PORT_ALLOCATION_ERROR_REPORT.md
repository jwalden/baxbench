# Docker Container Port Allocation Error - Investigation Report

## Overview

Investigation of Docker container startup errors related to port allocation in the baxbench codebase. The investigation identified a **critical race condition** in the port management system that causes "port is already allocated" errors.

## Error Message

```
ERROR 2025-11-17 14:00:32,394 could not start container 500 Server Error for
http+docker://localhost/v1.52/containers/4f3a76395ee3.../start:
Internal Server Error ("failed to set up container networking:
driver failed programming external connectivity on endpoint baxbench-ad0e2d95-...
(Bind for 0.0.0.0:12346 failed: port is already allocated")
```

## Key Findings

### Error Frequency
- **12 confirmed instances** of port allocation failures in test logs
- Ports affected: **12359 (6 errors)** and **12360 (6 errors)**
- Errors concentrated at the low end of the port range, suggesting cascading failures

### Root Cause: Race Condition in Port Management

The issue is a **critical flaw in exception handling** during Docker container startup:

1. **Port is acquired** from SlotManager and marked as unavailable
2. **Container startup is attempted** with that port
3. **If Docker port binding fails**, the exception is caught but **the port is NEVER released**
4. The port slot remains marked as "unavailable" in SlotManager but is not bound to any container
5. This creates **stale port reservations** that accumulate over time
6. When concurrent tests try to reuse ports, collisions occur

## Affected Files

| File | Lines | Component | Issue |
|------|-------|-----------|-------|
| `src/tasks.py` | 52-77 | ContainerRunner.__enter__() | No port release on startup failure |
| `src/tasks.py` | 79-90 | ContainerRunner.__exit__() | Only releases port if __enter__ succeeds |
| `src/tasks.py` | 646-670 | SlotManager | No validation of Docker port status |
| `src/env/base.py` | 137-161 | run_docker_container() | Throws exception on port binding failure |
| `src/tasks.py` | 392-407 | test_code() functional test | Concurrent container creation |
| `src/tasks.py` | 436-450 | test_code() security test | Concurrent container creation |
| `src/tasks.py` | 720-749 | run_tests() | ThreadPoolExecutor with shared port_manager |

## Detailed Problem Analysis

### ContainerRunner Race Condition

**Location**: `src/tasks.py`, lines 52-77

```python
def __enter__(self) -> Self:
    while self._port is None:
        self._port = self.port_manager.acquire_slot()  # Port acquired
        time.sleep(0.1)
    try:
        self._container = self.env.run_docker_container(self.image_id, self._port)
        # If exception here, port is NEVER released
    except Exception as e:
        self.logger.exception("could not start container %s", e, exc_info=e)
        raise ValueError("Could not start docker container")
        # PROBLEM: Port remains reserved but not bound to Docker
```

**The Problem:**
- Port is marked as "unavailable" in SlotManager at line 54
- If `run_docker_container()` fails at line 57, an exception is raised
- The exception causes `__enter__` to exit without reaching normal return
- `__exit__` is NEVER called (Python context manager behavior)
- The port release in `__exit__` (line 87) never executes
- Port slot remains marked as unavailable forever (or until process exit)

### SlotManager Design Flaw

**Location**: `src/tasks.py`, lines 646-670

The SlotManager only tracks its internal state. It has no visibility into:
- Whether Docker successfully bound the port
- Whether a container was created
- Whether a container was cleaned up
- Whether the port is actually in use

This creates a mismatch: SlotManager thinks port is unavailable, but Docker may see it as available (since binding failed). Later attempts to use the port will conflict.

### Concurrent Execution Amplifies the Problem

**Location**: `src/tasks.py`, lines 720-749

The concurrent execution model exacerbates the issue:
- Multiple tasks run simultaneously with ThreadPoolExecutor
- Each task can create multiple containers (functional + security tests)
- All tasks share a single SlotManager instance
- If one task's container fails to start, its port slot is lost
- Other tasks cannot acquire that port (it's marked unavailable)
- Port pool progressively shrinks with each failure

## Port Allocation Configuration

**Location**: `src/main.py`, lines 265-276

```
Default Port Range: 12345 to 22344 (10,000 ports)
Allocation Strategy: Sequential slot-based (linear search)
Concurrency Model: ThreadPoolExecutor with shared SlotManager
```

## Error Log Examples

From `results/gpt-4.1_revision_0/FrameExtract/Python-Django/temp0.4-openapi-specific/sample0/test.log`:

```
ERROR 2025-11-11 19:57:30,369 could not start container 500 Server Error for
    http+docker://localhost/v1.50/containers/6591ed5409af.../start:
    Internal Server Error ("failed to set up container networking:
    driver failed programming external connectivity on endpoint baxbench-24d6a8cc-...
    Bind for 0.0.0.0:12359 failed: port is already allocated")
```

## Cleanup Mechanisms (Insufficient)

### What Currently Exists

1. **Container Removal in __exit__**: `container.remove(force=True)` (line 86)
   - Only executes if __exit__ is called
   - Does NOT execute on __enter__ exception

2. **Docker Prune**: `docker.from_env().containers.prune()` (main.py line 144)
   - Only runs after ALL tests complete
   - Requires `--prune_docker` flag
   - Does not help during active test execution

### What's Missing

1. Exception-based port release in __enter__
2. Docker container cleanup on startup failure
3. Port reconciliation between SlotManager and Docker reality
4. Retry mechanism with port release
5. Stale port timeout and cleanup
6. Logging for port allocation/release debugging

## Impact Assessment

### Severity: CRITICAL

- **Blocks test execution**: Port exhaustion prevents tests from running
- **Cascading failures**: Each startup failure reduces available ports
- **Non-recoverable**: Stale ports cannot be reclaimed during execution
- **Affects all concurrent tests**: Shared port_manager creates dependencies

## Recommendations

### CRITICAL (Fix Immediately)

1. **Add exception-based port release in ContainerRunner.__enter__()**
   - Wrap container startup in try-finally
   - Release port slot even if container creation fails
   - Attempt container cleanup

```python
def __enter__(self) -> Self:
    while self._port is None:
        self._port = self.port_manager.acquire_slot()
        time.sleep(0.1)
    try:
        self._container = self.env.run_docker_container(self.image_id, self._port)
    except Exception as e:
        # CRITICAL: Release port on failure
        self.port_manager.release_slot(self._port)
        self._port = None
        self.logger.exception("could not start container %s", e, exc_info=e)
        raise ValueError("Could not start docker container")
    return self
```

2. **Implement Docker port reconciliation**
   - Query Docker for actual in-use ports at startup
   - Sync SlotManager with Docker reality
   - Clean up zombie reservations

3. **Add Docker-specific exception handling**
   - Catch docker.errors.APIError for port binding failures
   - Release port immediately on binding failure
   - Log error details for debugging

### IMPORTANT (Fix Soon)

4. **Container cleanup on startup failure**
   - If container object exists but startup failed, remove it
   - Use container ID to track cleanup

5. **Enhanced logging**
   - Log each acquire_slot() and release_slot() call
   - Log Docker port binding success/failure
   - Enable debugging of conflicts

6. **Increase port pool or use dynamic allocation**
   - Default 10,000 ports may be insufficient
   - Consider Docker random port allocation as fallback
   - Implement dynamic port selection

### Nice to Have

7. **Port monitoring and metrics**
   - Track port utilization over time
   - Detect stale reservations
   - Alert on unusual patterns

8. **Timeout-based cleanup**
   - Release ports after grace period if still marked unavailable
   - Clean up orphaned slots

## Next Steps

1. Prioritize fixes based on severity
2. Implement port release on startup failure (CRITICAL)
3. Add Docker port reconciliation (CRITICAL)
4. Test with high concurrency to verify fix effectiveness
5. Monitor port allocation in production
