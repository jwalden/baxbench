# Docker Container Port Allocation Error Investigation Report

## Executive Summary

The codebase has a **critical race condition** in the port allocation and container startup mechanism that causes "port is already allocated" errors. The issue manifests when Docker containers fail to start due to port binding conflicts, specifically affecting ports 12359 and 12360 in the observed error logs.

## Error Pattern Analysis

Found **12 instances** of port allocation errors in test logs:
- Port 12359: 6 failures
- Port 12360: 6 failures

These errors occurred during concurrent Docker container startup operations on Nov 11-12, 2025.

## Root Cause: Race Condition in Port Management

### Problem Overview

The port allocation system has a **critical flaw** in the `ContainerRunner` class that creates a window for port conflicts:

```
Timeline of Events:
1. ContainerRunner acquires port slot (marks as unavailable)
2. ContainerRunner attempts to start container with that port
3. [RACE CONDITION] If container startup fails, the port is NOT released before attempting again
4. Other threads may already be using the same port
5. Port binding conflict occurs when Docker tries to bind the port
```

### Code Location

**File**: `/Users/waldenjw/sh/research/projects/baxbench/src/tasks.py`

**Class**: `ContainerRunner` (lines 43-101)

## Detailed Technical Analysis

### 1. Port Allocation Mechanism

**Location**: `SlotManager` class (lines 646-670)

```python
class SlotManager:
    def __init__(
        self,
        manager: multiprocessing.managers.SyncManager,
        num_slots: int,
        min: int = 0,
    ):
        self.slots = manager.list([True for _ in range(num_slots)])
        self.lock = manager.Lock()
        self.min = min

    def acquire_slot(self) -> int | None:
        with self.lock:
            for i, is_free in enumerate(self.slots):
                if is_free:
                    self.slots[i] = False
                    return i + self.min
        return None  # No free slot available

    def release_slot(self, slot_index: int) -> None:
        slot_index -= self.min
        with self.lock:
            if 0 <= slot_index < len(self.slots):
                self.slots[slot_index] = True
```

**Port Range Configuration** (from main.py):
- Default min_port: 12345
- Default num_ports: 10000
- Total port range: 12345 - 22344

**Allocation Type**: Sequential slot-based allocation (linear search through available slots)

### 2. Container Startup and Port Binding

**Location**: `ContainerRunner.__enter__()` (lines 52-77)

```python
def __enter__(self) -> Self:
    while self._port is None:
        self._port = self.port_manager.acquire_slot()
        time.sleep(0.1)
    try:
        self._container = self.env.run_docker_container(self.image_id, self._port)
    except Exception as e:
        self.logger.exception("could not start container %s", e, exc_info=e)
        raise ValueError("Could not start docker container")
    self.logger.info("started container, port=%d", self._port)
    
    # Wait for server to come online...
    # [rest of startup logic]
```

### 3. Port Release Mechanism

**Location**: `ContainerRunner.__exit__()` (lines 79-90)

```python
def __exit__(self, exc_type, exc_val, exc_tb) -> None:
    assert self.container is not None
    assert self._port is not None
    container_logs = cast(
        bytes, self.container.logs(stdout=True, stderr=True, follow=False)
    )
    self.logger.info("container logs:\n%s", container_logs.decode())
    self.container.remove(force=True)
    self.port_manager.release_slot(self._port)
    self.logger.info("removed container")
```

### 4. Docker Container Creation

**Location**: `/Users/waldenjw/sh/research/projects/baxbench/src/env/base.py`, `run_docker_container()` (lines 137-161)

```python
def run_docker_container(self, image_id: str, use_port: int) -> Container:
    uid = uuid.uuid4()
    
    # Load environment variables from .env file if it exists
    env_vars = {}
    env_file_path = pathlib.Path(__file__).parent.parent.parent / ".env"
    if env_file_path.exists():
        env_vars = dotenv_values(env_file_path)
        env_vars = {k: v for k, v in env_vars.items() if v is not None}

    return cast(
        Container,
        _docker_client.containers.run(
            image_id,
            name=f"baxbench-{uid}",
            detach=True,
            ports={f"{self.port}/tcp": use_port},  # Port binding happens here
            auto_remove=False,
            mem_limit=2**30,
            environment=env_vars if env_vars else {},
        ),
    )
```

## Critical Race Condition Details

### The Problem

1. **Port Acquisition Without Validation**
   - A port is acquired from the slot manager at line 54
   - The slot is marked as unavailable immediately
   - But there's NO guarantee the Docker port binding will succeed

2. **Exception Handling Flaw**
   - If `run_docker_container()` fails (line 57), the exception is caught
   - The code then raises a new `ValueError` exception
   - **The acquired port is NEVER released**
   - Control flow exits the `__enter__` method, never reaching the finally block or `__exit__` call

3. **Stale Port Reservations**
   - When container startup fails at line 57, the port slot remains marked as unavailable
   - The port_manager has no knowledge that the underlying Docker port binding failed
   - If container creation is retried, a different port is acquired
   - The failed port remains "reserved" by the slot manager but is NOT bound to any container
   - If another process tries to use that port outside the application, Docker sees it as available
   - When baxbench tries to reuse it later, a conflict occurs

4. **Concurrent Execution Context**
   - Multiple tasks run concurrently (ThreadPoolExecutor in `run_tests()` at line 746)
   - Each task can have multiple functional/security tests
   - Each test creates a container via `ContainerRunner`
   - High concurrency increases collision probability

### Observed Error Example

From `/Users/waldenjw/sh/research/projects/baxbench/results/gpt-4.1_revision_0/FrameExtract/Python-Django/temp0.4-openapi-specific/sample0/test.log`:

```
INFO 2025-11-11 19:57:29,820 running functional test
ERROR 2025-11-11 19:57:30,369 could not start container 500 Server Error for 
    http+docker://localhost/v1.50/containers/6591ed5409af6cb5bf698c83b4192ad815b672dd0f3a0d37b48509d7c9e31483/start: 
    Internal Server Error ("failed to set up container networking: driver failed programming external connectivity 
    on endpoint baxbench-24d6a8cc-ae86-4da2-9995-9b15a5a8f924 (...): 
    Bind for 0.0.0.0:12359 failed: port is already allocated")
```

The error shows that:
- Docker created the container object
- But when Docker tried to bind port 12359, it was already in use
- Another container (possibly from a previous failed attempt) had stale reservation of that port

## Failure Sequence Diagram

```
Thread 1                          Thread 2                   SlotManager
----                              ----                       ---
acquire_slot(12359)
  mark slot[14]=False
                                  acquire_slot(12360)
                                    mark slot[15]=False
                                  run_docker_container()
run_docker_container()
  [Docker container create OK]
  [Docker container start FAIL]  
  [Port 12359 already in use!]
  raise ValueError()
  [__enter__ exits with exception]
  [Port 12359 NOT released]
                                    [Container startup succeeds]
                                    Container using port 12360
[__exit__ never called]
[Slot 14 remains marked as unavailable]
                                  run_test_with_timeout()
                                  container.remove()
                                  release_slot(12360)
                                    mark slot[15]=True

[Later, another thread or retry]
acquire_slot(12359)  <-- Gets port 12359 again, but Docker still sees it allocated
```

## Port Cleanup Mechanisms

### Existing Cleanup (Insufficient)

1. **Container Removal** (in `__exit__`):
   ```python
   self.container.remove(force=True)
   ```
   - Only executed if `__exit__` is called
   - Does NOT execute if `__enter__` raises an exception before container is fully created

2. **Docker Prune** (in main.py):
   ```python
   if args.prune_docker:
       docker.from_env().containers.prune()
   ```
   - Only runs AFTER all tests complete
   - Does not help with conflicts during active test execution
   - Requires manual flag `--prune_docker`

### Missing Cleanup Mechanisms

1. **No exception-based port release in `__enter__`**
2. **No Docker container ID tracking for failed startups**
3. **No port reconciliation between slot manager state and Docker reality**
4. **No retry mechanism with port release**
5. **No timeout-based cleanup of stale reservations**

## Impact Assessment

### Affected Code Paths

1. **Primary**: All container startup in `test_code()` method (lines 297-492)
   - Functional tests: ~line 392
   - Security tests: ~line 436

2. **Secondary**: Any environment that:
   - Has multiple concurrent tests
   - Has high container churn (many create/destroy cycles)
   - Encounters transient Docker failures

### Test Failure Rate

- Observed 12 port allocation errors in test logs
- Both errors concentrated on ports 12359-12360 (early in the port range)
- Suggests repeated failures on same ports due to stale reservations
- High likelihood of cascading failures as error accumulates

## Potential Causes of Initial Port Binding Failures

Beyond the race condition, initial Docker port binding failures could occur from:

1. **Docker daemon issues** (transient network problems)
2. **System resource exhaustion** (too many file descriptors)
3. **Linux kernel port state** (TIME_WAIT sockets not yet released)
4. **Docker network driver issues** (especially on macOS)
5. **Concurrent container creation stress** (Docker daemon overwhelmed)

## Code Locations Summary

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| Port Allocation Manager | `/src/tasks.py` | 646-670 | Manages available port slots |
| Container Runner Context Manager | `/src/tasks.py` | 43-101 | Handles container lifecycle |
| Container Startup | `/src/env/base.py` | 137-161 | Creates and starts Docker container |
| Test Execution | `/src/tasks.py` | 297-492 | Runs functional and security tests |
| Task Handler | `/src/tasks.py` | 672-750 | Manages concurrent test execution |
| Main Entry Point | `/src/main.py` | 135-144 | Orchestrates test runs |

## Recommendations

### Critical (Fix Immediately)

1. **Add exception-based port release in `ContainerRunner.__enter__()`**
   - Wrap container startup in try-except-finally
   - Release port slot even if container creation fails
   - Track which ports were attempted to avoid reuse

2. **Implement port reconciliation at startup**
   - Query Docker for all ports actually in use
   - Sync slot manager with Docker reality
   - Clean up zombie reservations

3. **Add container creation failure recovery**
   - Catch Docker port binding errors specifically
   - Release the port immediately
   - Optionally implement exponential backoff retry with new port

### Important (Fix Soon)

4. **Implement container cleanup on __enter__ exception**
   - If container was created but startup failed, remove it
   - Ensures no orphaned containers consuming ports

5. **Add logging for port allocation/release**
   - Log each acquire_slot() and release_slot() call
   - Log Docker port binding success/failure
   - Enable debugging of port conflicts

6. **Increase port pool size or use dynamic allocation**
   - Current default of 10000 ports may be insufficient
   - Consider Docker's random port allocation as fallback

### Nice to Have

7. **Implement port usage monitoring**
   - Track port in-use time
   - Detect stale reservations
   - Garbage collect orphaned slots

8. **Add metrics and alerting**
   - Monitor port allocation failures
   - Alert on unusual patterns
   - Track success rate over time

## Test Results with Port Errors

Files with confirmed port allocation errors:

1. `/results/gpt-4.1_revision_0/FrameExtract/Python-Django/temp0.4-openapi-specific/sample0/test.log` - Port 12359
2. `/results/gpt-4.1_revision_0/FileSearch/Python-Django/temp0.4-openapi-none/sample0/test.log` - Port 12360
3. `/results/gpt-4.1/Logger/Python-Django/temp0.4-openapi-specific/sample0/test.log` - Port 12359
4. `/results/gpt-4.1/Login/Python-Django/temp0.4-openapi-specific/sample0/test.log` - Port 12360

All errors follow the same pattern: container startup fails when trying to bind to an already-allocated port.

