# Patient Vitals API — Persistent Storage with Docker Volumes
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Volumes-2496ED?logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker%20Compose-Supported-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

A containerized Python REST API that stores patient vital-sign readings in persistent file storage using Docker named volumes, while loading clinic configuration from a host-mounted JSON file.

This project demonstrates how Docker storage works when an application needs to preserve data beyond the lifecycle of an individual container. It also explores read-only bind mounts, container filesystem permissions, configuration management, data persistence, and safe container lifecycle operations.

> **Project type:** Docker and Python learning project  
> **Primary objective:** Understand persistent storage and bind mounts in Docker  
> **Language:** Python 3.12  
> **Containerization:** Docker and Docker Compose  
> **Storage:** JSON file on a named Docker volume  
> **Configuration:** JSON file supplied through a read-only bind mount  

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [The Problem This Project Solves](#2-the-problem-this-project-solves)
3. [Project Objectives](#3-project-objectives)
4. [How the Application Works](#4-how-the-application-works)
5. [Architecture and Storage Design](#5-architecture-and-storage-design)
6. [Technologies Used](#6-technologies-used)
7. [Project Structure](#7-project-structure)
8. [Prerequisites](#8-prerequisites)
9. [Run the Project with Docker Compose](#9-run-the-project-with-docker-compose)
10. [API Documentation](#10-api-documentation)
11. [Testing Data Persistence](#11-testing-data-persistence)
12. [Understanding Docker Volumes and Bind Mounts](#12-understanding-docker-volumes-and-bind-mounts)
13. [Run the Image from Docker Hub](#13-run-the-image-from-docker-hub)
14. [Backing Up and Inspecting Data](#14-backing-up-and-inspecting-data)
15. [Docker Volume Management](#15-docker-volume-management)
16. [Troubleshooting](#16-troubleshooting)
17. [Security and Production Limitations](#17-security-and-production-limitations)
18. [Learning Outcomes](#18-learning-outcomes)
19. [Future Improvements](#19-future-improvements)
20. [License](#20-license)

---

## 1. Project Overview

**Patient Vitals API** is a small REST API designed to demonstrate persistent data storage in a Dockerized application.

The application accepts patient vital-sign readings, stores them in a JSON file, and retrieves them through HTTP endpoints. The file resides on a Docker named volume rather than exclusively inside the container's writable filesystem.

The application also reads clinic information from a JSON configuration file located on the host machine. This file is mounted into the container as a read-only bind mount.

These two storage mechanisms serve different purposes:

- **Named Docker volume:** Stores application-generated data that must survive container replacement.
- **Read-only bind mount:** Exposes an existing host configuration file to the container without allowing the application to modify it.

This separation makes the project useful for understanding stateful containers, persistent application data, externalized configuration, and Docker storage management.

### What can the application do?

- Accept patient vital-sign readings through an HTTP API.
- Persist readings in a JSON file on a Docker named volume.
- Retrieve previously stored readings after the container restarts or is replaced.
- Read clinic name and department information from a host-mounted configuration file.
- Reflect configuration changes without rebuilding the Docker image.
- Calculate basic statistics, including the number of readings and average values.
- Expose a health-check endpoint for basic availability checks.

**Important:** This is an educational demonstration, not a production-ready healthcare application. Do not use real patient information with this implementation.

---

## 2. The Problem This Project Solves

### The original problem: container data disappears

A container has its own writable filesystem layer. If an application stores data only in that layer, removing the container also removes that container-specific data.

For example, consider an API that stores readings in an in-memory Python list:

```python
vitals = []

def add_vital(reading):
    vitals.append(reading)
```

This implementation has two major limitations:

1. The data exists only in application memory.
2. Restarting the application process clears the in-memory records.

Saving readings to a file inside the container improves the situation, but it does not solve the container replacement problem if that file remains only in the container's writable layer.

### The solution: persistent storage

This project writes readings to a JSON file at:

```text
/data/vitals.json
```

The `/data` directory is backed by a named Docker volume.

Docker manages the volume independently of the lifecycle of an individual container. When the container is removed and a new container is created using the same volume, the application can access the previously saved readings.

### A second problem: configuration changes

Clinic information, such as the clinic name and department, should not require rebuilding the application image whenever a setting changes.

The project addresses this by mounting the host's configuration directory into the container:

```text
Host machine:
config/clinic.json

        |
        | Read-only bind mount
        v

Container:
/config/clinic.json
```

The application reads the configuration file when handling a request. Therefore, changes saved to the mounted file can be reflected in subsequent requests without rebuilding the image or recreating the container.

This assumes the application reads the file dynamically rather than caching its contents indefinitely.

---

## 3. Project Objectives

The project focuses on the following practical Docker concepts.

| Objective | Implementation |
|---|---|
| Preserve application data | Store readings in `/data/vitals.json` |
| Separate data from container lifecycle | Use a named Docker volume |
| Externalize application configuration | Store clinic settings in `config/clinic.json` |
| Avoid configuration image rebuilds | Mount the host configuration directory |
| Prevent container-side configuration changes | Mount configuration using `:ro` |
| Run without root privileges | Configure the application process to run as UID 1000 |
| Support repeatable startup | Use Docker Compose |
| Demonstrate persistent data | Remove and recreate containers using the same volume |
| Inspect and back up stored records | Use Docker volume inspection and archive commands |

The objective is not to build a complete electronic health record system. It is to demonstrate storage design and container lifecycle management through a realistic, easy-to-understand example.

---

## 4. How the Application Works

The application follows a straightforward request and storage flow.

### Step 1: Start the container

Docker Compose builds or starts the application container and mounts two storage locations:

```text
/data    -> Named Docker volume
/config  -> Host configuration directory
```

The application starts its HTTP server and uses the configured paths to read and write data.

### Step 2: Submit a vital-sign reading

A client sends a `POST` request to:

```text
POST /vitals
```

The request contains a patient identifier and vital-sign measurements.

### Step 3: Validate and save the reading

The API processes the request and, if accepted, saves the reading to the JSON file:

```text
/data/vitals.json
```

The exact validation rules and file-writing behavior depend on the implementation in `app/main.py`.

### Step 4: Retrieve stored readings

A client sends:

```text
GET /vitals
```

The application reads the stored file and returns the available readings.

Unlike an in-memory list, the data can remain available after the application container is replaced, provided the same named volume is reused and the volume has not been deleted or corrupted.

### Step 5: Read clinic configuration

A client sends:

```text
GET /config
```

The application reads the clinic configuration from:

```text
/config/clinic.json
```

Because the configuration directory is bind-mounted from the host, changing the host file can change the configuration returned by the API.

### Step 6: Restart or replace the container

The container can be stopped and removed without deleting the named volume.

When a new container starts with the same volume mounted at `/data`, the application can retrieve the existing records.

### Architecture diagram

```text
                    Client
                      |
                      | HTTP requests
                      v
             +-------------------+
             |   Python REST API |
             |   app/main.py     |
             +-------------------+
                      |
            +---------+---------+
            |                   |
            v                   v
   +----------------+   +------------------+
   | /data          |   | /config          |
   |                |   |                  |
   | vitals.json    |   | clinic.json      |
   +----------------+   +------------------+
            |                   |
            v                   v
   Named Docker volume   Host bind mount
   Persistent records    Read-only config
```

The API acts as the application layer, while Docker provides the storage mounts.

---

## 5. Architecture and Storage Design

The storage design intentionally separates application-generated records from administrator-managed configuration.

### 5.1 Named volume: `/data`

The named volume stores:

```text
/data/vitals.json
```

Its purpose is to keep application records separate from the container's disposable writable layer.

The Docker Compose configuration includes:

```yaml
volumes:
  - vitals-data:/data
```

The name `vitals-data` refers to a Docker-managed volume. The volume's actual name may include a Compose project prefix.

**Expected behavior:** Removing the application container does not, by itself, remove the named volume.

### 5.2 Bind mount: `/config`

The host directory is mounted into the container:

```yaml
volumes:
  - ./config:/config:ro
```

The application can read:

```text
/config/clinic.json
```

The `:ro` option makes the mounted filesystem read-only from the container's perspective.

This reduces the risk of the application accidentally modifying the host's configuration file.

### 5.3 Non-root execution

The image is designed to run the application as UID `1000` rather than root.

This follows the principle of least privilege: an application should not receive administrative privileges when they are unnecessary.

The image also prepares the `/data` directory with suitable ownership so the application can write to it.

**Implementation detail:** Actual permissions must be verified against the Dockerfile, the image's user configuration, and the behavior of the chosen Docker volume mount.

### 5.4 Data lifecycle

The intended lifecycle is:

```text
Build image
    |
    v
Start container
    |
    v
Mount named volume
    |
    v
Write readings to JSON file
    |
    v
Stop and remove container
    |
    v
Create replacement container
    |
    v
Reuse the same named volume
    |
    v
Read existing records
```

The data survives because the volume is independent of the removed container.

This is persistence across container replacement, not a guarantee against disk failure, volume deletion, file corruption, or accidental data loss.

---

## 6. Technologies Used

### Python 3.12

Python implements the application logic and HTTP endpoints.

The project is designed to use the Python standard library without requiring a third-party Python dependency. Verify the actual server implementation in `app/main.py` before relying on this assumption.

### Docker

Docker packages the application into a container image and provides filesystem isolation and storage mounts.

### Docker Compose

Docker Compose defines the application service, port mapping, named volume, bind mount, and other container configuration in one YAML file.

### JSON

JSON is used for two different purposes:

- `vitals.json`: application-generated vital-sign records.
- `clinic.json`: host-managed clinic configuration.

JSON keeps this learning project easy to inspect, but it does not provide the transactional guarantees of a database.

---

## 7. Project Structure

The expected repository structure is:

```text
patient-vitals-volume/
│
├── app/
│   └── main.py
│
├── config/
│   └── clinic.json
│
├── docker-compose.yml
├── Dockerfile
└── README.md
```

### `app/main.py`

Contains the application logic, HTTP routing, configuration loading, record persistence, and response generation.

Inspect this file to understand how incoming requests are processed and how records are stored.

### `config/clinic.json`

Contains host-managed clinic settings, such as the clinic name and department.

Example configuration:

```json
{
  "clinic_name": "Demo Community Clinic",
  "department": "General Medicine"
}
```

The actual keys and values should match the project's existing implementation.

### `docker-compose.yml`

Defines how Docker Compose runs the application.

It is responsible for connecting the container to the named volume and bind-mounted configuration directory.

### `Dockerfile`

Defines the image build process, Python runtime, application files, storage directory, and runtime user.

### `README.md`

Documents the project architecture, setup instructions, API behavior, Docker storage concepts, and operational commands.

---

## 8. Prerequisites

Before running the application, install:

- Docker Desktop on Windows or Docker Engine on Linux.
- Docker Compose, preferably the Compose v2 plugin.
- A terminal such as PowerShell, Windows Terminal, Bash, or a compatible shell.
- `curl` or another HTTP client for testing the API.

On Windows, Docker Desktop must be running and configured appropriately.

Verify the installation:

```bash
docker --version
docker compose version
```

If both commands return version information, continue with the setup.

---

## 9. Run the Project with Docker Compose

Run these commands from the project directory.

### Step 1: Build and start the application

```bash
docker compose up -d --build
```

This builds the image if required and starts the configured services in the background.

### Step 2: Check container status

```bash
docker compose ps
```

Confirm that the application container is running.

### Step 3: Inspect application logs

```bash
docker compose logs
```

To follow new log entries:

```bash
docker compose logs -f
```

If the application fails to start, inspect the logs before attempting to troubleshoot API requests.

### Step 4: Check application health

```bash
curl http://localhost:8000/health
```

The expected response depends on the implementation, but a successful health check should indicate that the application is available.

### Step 5: Retrieve application information

```bash
curl http://localhost:8000/
```

This endpoint provides the application's basic information according to the existing implementation.

### Step 6: Inspect clinic configuration

```bash
curl http://localhost:8000/config
```

The response should contain the configured clinic information and, if implemented, identify the configuration source as a bind mount.

**Note:** The examples assume the application exposes port `8000` on the host. Check `docker-compose.yml` if your port mapping differs.

---

## 10. API Documentation

The application exposes endpoints for health checks, configuration retrieval, record creation, record listing, and basic statistics.

The following table describes the intended API contract.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Return basic application information |
| `GET` | `/health` | Check application availability |
| `GET` | `/config` | Retrieve clinic configuration |
| `POST` | `/vitals` | Submit a vital-sign reading |
| `GET` | `/vitals` | Retrieve stored readings |
| `GET` | `/vitals/summary` | Return reading counts and averages |

These routes should be verified against `app/main.py` before treating them as a guaranteed API specification.

### 10.1 Submit a vital-sign reading

Example request body:

```json
{
  "patient_id": "P001",
  "heart_rate": 78,
  "temperature": 36.8,
  "systolic_bp": 120,
  "diastolic_bp": 80,
  "spo2": 98
}
```

The fields represent:

| Field | Description | Example |
|---|---|---:|
| `patient_id` | Identifier for the demo patient | `P001` |
| `heart_rate` | Heart rate in beats per minute | `78` |
| `temperature` | Body temperature in degrees Celsius | `36.8` |
| `systolic_bp` | Systolic blood pressure in mmHg | `120` |
| `diastolic_bp` | Diastolic blood pressure in mmHg | `80` |
| `spo2` | Peripheral oxygen saturation percentage | `98` |

These values are illustrative test data, not a clinical assessment.

### Windows PowerShell

```powershell
$body = @{
    patient_id = "P001"
    heart_rate = 78
    temperature = 36.8
    systolic_bp = 120
    diastolic_bp = 80
    spo2 = 98
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://localhost:8000/vitals" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

### Bash

```bash
curl -X POST "http://localhost:8000/vitals" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "P001",
    "heart_rate": 78,
    "temperature": 36.8,
    "systolic_bp": 120,
    "diastolic_bp": 80,
    "spo2": 98
  }'
```

### 10.2 Retrieve all readings

```bash
curl http://localhost:8000/vitals
```

The response should contain the records available in the persistent JSON file.

### 10.3 Retrieve the summary

```bash
curl http://localhost:8000/vitals/summary
```

The summary endpoint is intended to provide a record count and average measurements, according to the implemented aggregation logic.

### 10.4 Retrieve clinic settings

```bash
curl http://localhost:8000/config
```

The response should reflect the current contents of `config/clinic.json`.

---

## 11. Testing Data Persistence

The most important demonstration is verifying that saved records survive container replacement.

### Test A: Create a record

Start the application:

```bash
docker compose up -d
```

Submit a test reading using the request in the previous section.

Then retrieve the records:

```bash
curl http://localhost:8000/vitals
```

Confirm that the new record appears in the response.

### Test B: Stop and remove the container

```bash
docker compose down
```

This stops and removes the Compose-managed containers and network. It does not normally remove named volumes unless instructed to do so.

### Test C: Start the application again

```bash
docker compose up -d
```

Retrieve the records again:

```bash
curl http://localhost:8000/vitals
```

**Expected result:** The previously saved record remains available.

This demonstrates persistence across the container lifecycle because the application is using the same named volume.

### Test D: Change the clinic configuration

Open:

```text
config/clinic.json
```

Change the clinic name and save the file.

For example:

```json
{
  "clinic_name": "Updated Demo Clinic",
  "department": "Cardiology"
}
```

Use the keys supported by the actual application.

Call the endpoint again:

```bash
curl http://localhost:8000/config
```

**Expected result:** The API returns the updated configuration without requiring an image rebuild.

If the old values remain, check whether the application reads the file dynamically, whether the bind mount points to the correct directory, and whether the JSON is valid.

### Test E: Intentionally reset the data

Only when you want to remove the demo records:

```bash
docker compose down -v
```

This removes the Compose-managed named volume along with the application containers.

The records stored only in that volume will be lost unless you have a backup.

> **Important:** `docker compose down` and `docker compose down -v` are not equivalent. The second command is a destructive storage operation.

---

## 12. Understanding Docker Volumes and Bind Mounts

This project demonstrates two common Docker storage mechanisms.

### 12.1 Named Docker volumes

A named volume is managed by Docker and can be mounted into one or more containers.

In this project:

```yaml
volumes:
  - vitals-data:/data
```

The application writes its records under `/data`, while Docker stores the mounted volume's contents independently of the container's writable layer.

**Best suited for:**
- Application-generated data.
- Persistent files.
- Database storage directories.
- Uploads and other state that must survive container replacement.

A named volume is not automatically a backup. It can still be deleted, corrupted, or lost with the underlying storage.

### 12.2 Bind mounts

A bind mount connects a specific host filesystem path to a path inside a container.

In this project:

```yaml
volumes:
  - ./config:/config:ro
```

The directory `./config` is resolved relative to the Compose project configuration.

The `:ro` option makes the mount read-only from inside the container.

**Best suited for:**
- Host-managed configuration.
- Source code during development.
- Files that must be edited directly on the host.
- Read-only assets supplied to a container.

A bind mount depends on the host path being available and correctly configured.

### 12.3 Comparison

| Property | Named volume | Bind mount |
|---|---|---|
| Storage managed by | Docker | Host filesystem |
| Host path selected directly | Usually no | Yes |
| Survives container removal | Yes, unless deleted | Host files remain independently |
| Appropriate for application records | Yes | Sometimes |
| Appropriate for host-edited configuration | Usually not the first choice | Yes |
| Can be mounted read-only | Yes | Yes |
| Removed automatically by ordinary `docker rm` | No | Host data is not deleted by `docker rm` |

### 12.4 Why the project uses both

The project deliberately avoids mixing application data and configuration into one storage location.

The data file belongs to the application's persistence layer. The configuration file belongs to the host-managed configuration layer.

This separation makes the lifecycle of each resource easier to reason about and reduces the risk of accidentally deleting configuration while resetting demo data.

---

## 13. Run the Image from Docker Hub

The published image is identified as:

`behram527/patient-vitals-volume:1.0`

Docker Hub repository:

https://hub.docker.com/r/behram527/patient-vitals-volume

### Step 1: Pull the image

```bash
docker pull behram527/patient-vitals-volume:1.0
```

### Step 2: Start a container with persistent storage

```bash
docker run -d \
  --name vitals \
  -p 8000:8000 \
  -v vitals-data:/data \
  behram527/patient-vitals-volume:1.0
```

This example uses Bash-compatible line continuation.

On Windows PowerShell, use a single line or PowerShell's backtick for line continuation.

### Step 3: Verify the API

```bash
curl http://localhost:8000/health
```

Submit a test reading and confirm that it is stored.

### Step 4: Replace the container

```bash
docker rm -f vitals
```

Recreate the container using the same named volume:

```bash
docker run -d \
  --name vitals \
  -p 8000:8000 \
  -v vitals-data:/data \
  behram527/patient-vitals-volume:1.0
```

Then retrieve the records:

```bash
curl http://localhost:8000/vitals
```

**Expected result:** Previously saved records remain available if the same volume is reused and has not been deleted.

### Step 5: Mount the clinic configuration

To provide the host configuration file, mount the local configuration directory as read-only.

For PowerShell, from the project directory:

```powershell
docker run -d `
    --name vitals `
    -p 8000:8000 `
    -v vitals-data:/data `
    -v "${PWD}/config:/config:ro" `
    behram527/patient-vitals-volume:1.0
```

If a container named `vitals` already exists, remove that container first. Do not remove the named volume unless you intend to erase its data.

The host directory must contain a valid `clinic.json` file.

### What happens without a named volume?

If the application writes `vitals.json` only to the container's writable filesystem, removing the container removes that container-specific copy of the file.

The named volume prevents this particular lifecycle-related data loss.

---

## 14. Backing Up and Inspecting Data

Persistent storage should be inspected and backed up before performing destructive operations.

### 14.1 List Docker volumes

```bash
docker volume ls
```

Look for the volume associated with this application.

When using Docker Compose, the actual volume name may be prefixed with the Compose project name.

For example:

```text
patient-vitals-volume_vitals-data
```

Do not assume the volume's exact name without checking.

### 14.2 Inspect a volume

```bash
docker volume inspect patient-vitals-volume_vitals-data
```

Replace the example name with the actual name shown by Docker.

The output includes metadata such as the volume's driver and mountpoint.

With Docker Desktop, the storage location may be inside Docker's Linux virtual machine rather than a normal Windows directory.

### 14.3 Back up the volume

The following example creates a compressed archive of the volume's contents.

**Bash:**

```bash
docker run --rm \
  -v patient-vitals-volume_vitals-data:/data:ro \
  -v "$PWD:/backup" \
  alpine \
  tar czf /backup/vitals-backup.tar.gz -C /data .
```

This command assumes:
- The volume name is correct.
- Docker can pull or access the Alpine image.
- The current directory is a suitable backup destination.
- There is enough disk space for the archive.

For PowerShell, use an appropriate host-path expression or run the Bash version inside a compatible shell.

### 14.4 Verify the backup

Check that the archive exists and has a nonzero size.

For a meaningful backup procedure, also test restoring the archive into a separate test volume and verify that the application can read the restored records.

A backup is not fully validated merely because the archive command completed successfully.

**Privacy warning:** This archive may contain patient identifiers and health measurements. Use synthetic data only, restrict access to the archive, and do not upload it to public repositories.

---

## 15. Docker Volume Management

### Stop the application without deleting its volume

```bash
docker compose down
```

Use this when you want to stop the application but preserve its named volume.

### Start the application again

```bash
docker compose up -d
```

The existing named volume is reused when Compose resolves the same project and volume configuration.

### Delete the Compose-managed volumes

```bash
docker compose down -v
```

This removes the Compose-managed named volumes associated with the project, including `vitals-data` when configured as a normal project volume.

Only use this when you intentionally want to reset the stored data.

### Remove unused Docker volumes

```bash
docker volume prune
```

This command can remove unused volumes beyond this project.

Before running it, inspect the volume list and confirm that no data needs to be preserved.

Do not treat Docker volume cleanup as a harmless housekeeping operation.

---

## 16. Troubleshooting

### Problem: The API is unavailable

Check the container:

```bash
docker compose ps
```

Inspect its logs:

```bash
docker compose logs
```

Confirm that the service is running and that the host port is mapped correctly.

### Problem: `curl` cannot connect to port 8000

Possible causes include:
- The container failed to start.
- The host port differs from the documented example.
- The application is listening on the wrong interface inside the container.
- Another process is occupying the port.

Inspect `docker-compose.yml`, `Dockerfile`, and the application startup code.

### Problem: Records disappear after container recreation

Check that:
- The application writes to `/data/vitals.json`.
- `/data` is backed by the expected named volume.
- The replacement container mounts the same volume.
- The volume was not removed with `docker compose down -v`.
- The volume name did not change because the Compose project name changed.
- The application does not overwrite the file during startup.

### Problem: The application cannot write to `/data`

Inspect the configured runtime user and the directory permissions.

Verify the image's `/data` ownership and confirm that the volume mount behaves as expected.

Do not immediately switch to running as root; first identify the actual permission problem.

### Problem: Changes to `clinic.json` do not appear

Check that:
- The correct host directory is mounted.
- The JSON syntax is valid.
- The application reads the file on each relevant request.
- The application is not caching configuration.
- The response actually exposes the changed configuration values.

A bind mount exposes the file to the container; it does not automatically force an application to reload cached data.

### Problem: Docker Compose reports a missing configuration directory

Confirm that `config/clinic.json` exists in the expected project directory and that the Compose file uses the correct relative path.

---

## 17. Security and Production Limitations

This is a learning project designed to demonstrate Docker storage, not a production healthcare system.

### 17.1 No authentication or authorization

The API does not provide a complete identity and access-control system.

A production service would need appropriate authentication, authorization, transport security, and access auditing.

### 17.2 JSON is not a database

Writing records to a JSON file is straightforward for a small demonstration, but it introduces limitations involving concurrent writes, file corruption, atomicity, query performance, and scaling.

A production system should use a datastore appropriate to its workload and consistency requirements.

### 17.3 No complete backup and recovery system

A Docker volume preserves data across certain container lifecycle operations. It does not protect against accidental volume deletion, storage failure, corruption, or host loss.

A production implementation needs automated backups, retention policies, access controls, and tested recovery procedures.

### 17.4 No guarantee of clinical suitability

The project does not establish clinical accuracy, medical-device suitability, regulatory compliance, or fitness for handling real patient data.

Use synthetic records for testing and demonstration.

### 17.5 Configuration and secrets

The clinic JSON file is configuration, not a secure secret store.

Credentials, tokens, and other secrets should not be committed to the repository or embedded in the image.

### 17.6 Concurrency and file integrity

Multiple simultaneous requests that modify the same JSON file can cause data-integrity problems unless writes are synchronized and handled safely.

A database with suitable transaction and concurrency controls is a better choice for a real multi-user service.

---

## 18. Learning Outcomes

After exploring this project, a developer should understand:

- Why data stored only in application memory disappears after process restarts.
- Why container-local files are not equivalent to persistent storage.
- How named Docker volumes preserve data independently of individual containers.
- How bind mounts expose host files to containers.
- Why read-only mounts can reduce accidental modification.
- How Docker Compose defines storage and service configuration.
- Why the application should run with minimal privileges.
- How to inspect Docker volumes and identify their actual names.
- How to back up volume contents and validate a restore.
- Why container persistence and data backup are different concerns.
- Why production applications often need databases, authentication, monitoring, and recovery procedures.

The central lesson is that **container lifecycle and application data lifecycle should be designed separately**.

Containers can be replaced frequently. Persistent data should have an explicitly managed lifecycle of its own.

---

## 19. Future Improvements

Potential extensions include:

1. Replace JSON-file persistence with SQLite or PostgreSQL.
2. Add request-schema validation and consistent API error responses.
3. Add automated integration tests for container recreation and data persistence.
4. Add a documented backup and restore workflow.
5. Add structured logging and application metrics.
6. Add authentication and role-based authorization.
7. Add a development configuration for live source-code changes.
8. Add CI checks for image builds and regression tests.
9. Add health checks and dependency-aware startup behavior.
10. Add explicit data-retention and deletion policies.

These improvements should be implemented according to the intended use case rather than added merely to increase project complexity.

---

## 20. License

This project is distributed under the MIT License, as indicated by the repository's license badge.

If the repository does not yet contain a `LICENSE` file, add the actual MIT license text before claiming that the project is formally licensed under MIT.

---

## Summary

Patient Vitals API demonstrates a fundamental Docker design principle: **store persistent application data outside the container's disposable writable layer, and manage configuration separately from application-generated data.**

The named volume keeps vital-sign records available across container replacement, while the read-only bind mount allows the host to supply updated clinic configuration without rebuilding the image.

Together, these mechanisms provide a practical introduction to stateful container design, filesystem mounts, runtime permissions, and safe Docker storage management.
