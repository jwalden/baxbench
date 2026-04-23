# Port Allocation Issue - Detailed Code Analysis with Snippets

## File 1: src/tasks.py - ContainerRunner Class

### PROBLEMATIC CODE: Port Acquisition Without Exception Handling

**Lines 52-77** in `/Users/waldenjw/sh/research/projects/baxbench/src/tasks.py`:

```python
@dataclass
class ContainerRunner:
    env: Env
    port_manager: "SlotManager"
    image_id: str
    logger: logging.Logger
    _container: Container | None = None
    _port: int | None = None

    def __enter__(self) -> Self:
        while self._port is None:
            self._port = self.port_manager.acquire_slot()  # LINE 54: Port acquired
            time.sleep(0.1)
        try:
            self._container = self.env.run_docker_container(self.image_id, self._port)
            # LINE 57: If exception here, port is NEVER released
        except Exception as e:
            self.logger.exception("could not start container %s", e, exc_info=e)
            raise ValueError("Could not start docker container")
            # PROBLEM: When this raises, __exit__ is NOT called
            # Port slot remains marked as unavailable in port_manager
            # But Docker never bound to this port
        
        self.logger.info("started container, port=%d", self._port)
        
        # make sure that the server is online before we process, otherwise let it fail
        start = time.time()
        while True:
            try:
                response = requests.get(f"http://localhost:{self._port}")
                self.logger.info("Server is up! Server response: %s", response)
                break
            except requests.ConnectionError as e:
                self.logger.warning("Server is not up yet: %s", e)
            if time.time() - start > self.env.wait_to_start_time:
                self.logger.error("Server did not start in time")
                self.__exit__(*exc_info())
            self.logger.info("Waiting for server to start...")
            time.sleep(1.0)
        return self
```

### INSUFFICIENT CLEANUP: Port Release in __exit__

**Lines 79-90** in `/Users/waldenjw/sh/research/projects/baxbench/src/tasks.py`:

```python
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        assert self.container is not None
        assert self._port is not None
        container_logs = cast(
            bytes, self.container.logs(stdout=True, stderr=True, follow=False)
        )
        self.logger.info("container logs:\n%s", container_logs.decode())
        self.container.remove(force=True)
        self.port_manager.release_slot(self._port)
        # This only executes if __enter__ succeeds and __exit__ is called
        # If __enter__ raises exception at line 57, this code never executes
        self.logger.info("-" * 100)
        self.logger.info("removed container")
        self.logger.info("-" * 100)
```

### THE RACE CONDITION: Usage in test_code()

**Lines 392-407** (functional test example) in `/Users/waldenjw/sh/research/projects/baxbench/src/tasks.py`:

```python
                    try:
                        with ContainerRunner(
                            self.env, port_manager, image_id, logger
                        ) as cr:  # If __enter__ raises exception, __exit__ is never called
                            server_ran_before = self.env.process_still_running(
                                cr.container.id, logger
                            )
                            passed = run_test_with_timeout(
                                ft,
                                AppInstance(
                                    port=cr.port,
                                    log_file_path=sample_dir / (ft.__name__ + ".log"),
                                    container_id=cr.container.id,
                                    env=self.env,
                                ),
                                timeout,
                            )
                    except Exception as e:
                        logger.exception("got exception:\n%s", str(e), exc_info=e)
                        had_exception = True
                        # Port was already released in __exit__ IF it got there
                        # But if __enter__ failed, port is still marked as unavailable
```

## File 2: src/tasks.py - SlotManager Class

### PORT ALLOCATION LOGIC

**Lines 646-670** in `/Users/waldenjw/sh/research/projects/baxbench/src/tasks.py`:

```python
class SlotManager:
    def __init__(
        self,
        manager: multiprocessing.managers.SyncManager,
        num_slots: int,
        min: int = 0,
    ):
        self.slots = manager.list([True for _ in range(num_slots)])
        # Each slot: True = available, False = reserved
        self.lock = manager.Lock()
        self.min = min  # Minimum port number (12345 by default)

    def acquire_slot(self) -> int | None:
        with self.lock:
            for i, is_free in enumerate(self.slots):
                if is_free:
                    self.slots[i] = False  # Mark as reserved
                    return i + self.min    # Return actual port number
            return None  # No free slot available

    def release_slot(self, slot_index: int) -> None:
        slot_index -= self.min
        with self.lock:
            if 0 <= slot_index < len(self.slots):
                self.slots[slot_index] = True  # Mark as available
```

### PROBLEM WITH THIS DESIGN

The SlotManager has no way to know if:
1. A port was successfully bound by Docker
2. A port binding failed
3. A container was cleaned up
4. A reserved port is actually in use

It only tracks its internal state. If a port binding fails but the slot isn't released, that port will be stuck in the "reserved" state forever.

## File 3: src/env/base.py - Docker Container Startup

### WHERE PORT BINDING HAPPENS

**Lines 137-161** in `/Users/waldenjw/sh/research/projects/baxbench/src/env/base.py`:

```python
    def run_docker_container(self, image_id: str, use_port: int) -> Container:
        uid = uuid.uuid4()

        # Load environment variables from .env file if it exists
        env_vars = {}
        env_file_path = pathlib.Path(__file__).parent.parent.parent / ".env"
        if env_file_path.exists():
            # Use dotenv_values to parse .env file without modifying os.environ
            env_vars = dotenv_values(env_file_path)
            # Filter out None values and convert to dict[str, str]
            env_vars = {k: v for k, v in env_vars.items() if v is not None}

        return cast(
            Container,
            _docker_client.containers.run(
                image_id,
                name=f"baxbench-{uid}",
                detach=True,
                ports={f"{self.port}/tcp": use_port},  # PORT BINDING HERE
                auto_remove=False,
                # Set the memory limit to 1GB.
                mem_limit=2**30,
                environment=env_vars if env_vars else {},
            ),
            # Port binding error occurs here when port already in use
            # The exception propagates to ContainerRunner.__enter__
            # But the port was already marked as reserved
        )
```

The error occurs when `_docker_client.containers.run()` tries to bind the port. This throws an exception that propagates up to `ContainerRunner.__enter__()` where it's caught at line 58, but the port release at line 87 never happens because `__exit__` is never called.

## File 4: src/main.py - Task Handler and Port Configuration

### PORT CONFIGURATION

**Lines 265-276** in `/Users/waldenjw/sh/research/projects/baxbench/src/main.py`:

```python
    parser.add_argument(
        "--num_ports",
        type=int,
        default=10000,
        help="Number of ports to use for docker containers",
    )
    parser.add_argument(
        "--min_port",
        type=int,
        default=12345,
        help="Minimum port number to use for docker containers",
    )
```

Default range: 12345 to 22344

### CONCURRENT TEST EXECUTION

**Lines 720-749** in `/Users/waldenjw/sh/research/projects/baxbench/src/tasks.py`:

```python
    def run_tests(
        self,
        samples: list[int],
        timeout: int,
        num_ports: int,
        min_port: int,
        force: bool,
    ) -> list[int]:
        with multiprocessing.Manager() as manager:
            port_manager = SlotManager(manager, num_ports, min_port)

            with tqdm.tqdm(total=len(self.tasks)) as pbar:

                def run_test_task(index_and_task: tuple[int, Task]) -> int:
                    i, task = index_and_task
                    task.test_code(
                        results_dir=self.results_dir,
                        samples=samples,
                        port_manager=port_manager,  # Shared across all threads
                        timeout=timeout,
                        force=force,
                    )
                    with pbar.get_lock():  # type: ignore[no-untyped-call]
                        pbar.update(1)
                    return 1

                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=self.max_concurrent_runs
                ) as executor:
                    return list(executor.map(run_test_task, enumerate(self.tasks)))
```

Multiple tasks run concurrently with a shared port_manager. If one task's container startup fails, it can starve the port pool for other tasks.

## Actual Error Log Extract

From `/Users/waldenjw/sh/research/projects/baxbench/results/gpt-4.1_revision_0/FrameExtract/Python-Django/temp0.4-openapi-specific/sample0/test.log`:

```
INFO 2025-11-11 19:57:24,357 copying file: bandit_log.json
...
INFO 2025-11-11 19:57:29,819 done building docker image. id: sha256:3d3ea74eba85e9948a1357974009c553d44c6e2ece7c13c493ef060e3d0ab375
INFO 2025-11-11 19:57:29,820 running functional test:
ERROR 2025-11-11 19:57:30,369 could not start container 500 Server Error for 
    http+docker://localhost/v1.50/containers/6591ed5409af6cb5bf698c83b4192ad815b672dd0f3a0d37b48509d7c9e31483/start: 
    Internal Server Error ("failed to set up container networking: driver failed programming external connectivity 
    on endpoint baxbench-24d6a8cc-ae86-4da2-9995-9b15a5a8f924 
    (f238f3b13983ad5ccd1181cc3ffa61d45ae633031f523e39f78590b19f79d237): 
    Bind for 0.0.0.0:12359 failed: port is already allocated")
Traceback (most recent call last):
  File "/home/waldenj/sh/research/projects/baxbench/src/tasks.py", line 57, in __enter__
    self._container = self.env.run_docker_container(self.image_id, self._port)
    # Port was acquired at line 54 and marked as unavailable
    # But Docker couldn't bind it, so it threw an exception
  File "/home/waldenj/sh/research/projects/baxbench/src/env/base.py", line 151, in run_docker_container
    _docker_client.containers.run(
  ...
docker.errors.APIError: 500 Server Error for 
    http+docker://localhost/v1.50/containers/6591ed5409af6cb5bf698c83b4192ad815b672dd0f3a0d37b48509d7c9e31483/start: 
    Internal Server Error ("failed to set up container networking: driver failed programming external connectivity 
    on endpoint baxbench-24d6a8cc-ae86-4da2-9995-9b15a5a8f924 
    (f238f3b13983ad5ccd1181cc3ffa61d45ae633031f523e39f78590b19f79d237): 
    Bind for 0.0.0.0:12359 failed: port is already allocated")

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/waldenj/sh/research/projects/baxbench/src/tasks.py", line 392, in test_code
    with ContainerRunner(
         ^^^^^^^^^^^^^^^^
  File "/home/waldenj/sh/research/projects/baxbench/src/tasks.py", line 60, in __enter__
    raise ValueError("Could not start docker container")
ValueError: Could not start docker container
INFO 2025-11-11 19:57:30,372 Functional test func_test_frame_extract failed
```

Note the sequence:
1. Docker container created (with UUID 6591ed5409af...)
2. Docker tries to bind port 12359
3. **Docker reports: "port is already allocated"**
4. Exception propagates from env/base.py line 151 to tasks.py line 57
5. Exception caught and re-raised at line 60
6. **Port slot 12359 remains marked as unavailable in SlotManager**
7. Container object remains unreleased (no cleanup attempted)

## Summary of Issues

| Issue | Location | Severity | Impact |
|-------|----------|----------|--------|
| Port not released on startup failure | tasks.py:57-60 | CRITICAL | Stale port reservations |
| No container cleanup on startup failure | tasks.py:57-60 | CRITICAL | Orphaned containers |
| No Docker port reconciliation | SlotManager | HIGH | Stale slots accumulate |
| No exception handling for port binding | env/base.py:151 | MEDIUM | Exceptions propagate uncaught |
| Concurrent access to same ports | tasks.py:746 | HIGH | Race conditions |
| No retry with different port | tasks.py:54-60 | MEDIUM | Single failure blocks test |
| Limited logging of port operations | SlotManager | LOW | Hard to debug |

