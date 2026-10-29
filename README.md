# Patient Vitals on a Docker Volume

The last API kept every reading in memory. Restart the container and the records were gone. This one writes them to a file, and that file sits on a named Docker volume, so replacing the container does not throw the data away.

Clinic name and department come from a JSON file on a bind mount. I can change that file on my machine and the running container picks it up. No image rebuild.

I put this together to practice the part of Docker that actually matters once an app has state: volumes, bind mounts, and a few habits that keep you from deleting the only copy.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Volumes-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## What this shows

- A named volume at `/data` holds `vitals.json`. `docker rm` does not delete it.
- A read-only bind mount at `/config` serves `clinic.json` from the host.
- The image runs as uid 1000, and `/data` is created with that owner so a fresh volume is writable.
- Records stay on disk across `docker compose down` and come back on the next `up`.
- `docker compose down -v` is the reset switch. It removes the volume on purpose.

## Tech

- Python 3.12 (standard library only)
- Docker
- Docker Compose

## Project layout

```text
patient-vitals-volume/
├── app/
│   └── main.py
├── config/
│   └── clinic.json
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Docker image

`behram527/patient-vitals-volume:1.0`

https://hub.docker.com/r/behram527/patient-vitals-volume

## Run it with Compose

From this folder:

```bash
docker compose up -d --build
```

Compose does two storage things here:

```yaml
volumes:
  - vitals-data:/data
  - ./config:/config:ro
```

`vitals-data` is a named volume Docker manages. `./config` is a bind mount of a folder I already have, and `:ro` means the container can read it and cannot rewrite it.

Record a reading:

```bash
curl -X POST "http://localhost:8000/vitals" ^
  -H "Content-Type: application/json" ^
  -d "{\"patient_id\":\"P001\",\"heart_rate\":78,\"temperature\":36.8,\"systolic_bp\":120,\"diastolic_bp\":80,\"spo2\":98}"
```

On bash, swap the `^` line breaks for `\`.

List what was saved:

```bash
curl http://localhost:8000/vitals
curl http://localhost:8000/config
```

`/config` should say `"source": "bind mount"` and the clinic name from `config/clinic.json`.

Stop the container without touching the data, then start it again:

```bash
docker compose down
docker compose up -d
curl http://localhost:8000/vitals
```

The same record is still there. That is the volume doing its job.

Change `config/clinic.json` (clinic name is enough), save it, and call `/config` again. The new name shows up immediately because both sides are looking at the same file.

## Run it from Docker Hub

Pull:

```bash
docker pull behram527/patient-vitals-volume:1.0
```

With a named volume, data survives the container:

```bash
docker run -d --name vitals -p 8000:8000 -v vitals-data:/data behram527/patient-vitals-volume:1.0
```

Check it, then throw the container away and start a new one on the same volume:

```bash
docker rm -f vitals
docker run -d --name vitals -p 8000:8000 -v vitals-data:/data behram527/patient-vitals-volume:1.0
curl http://localhost:8000/vitals
```

If you also want the clinic file from your machine:

```bash
docker run -d --name vitals -p 8000:8000 ^
  -v vitals-data:/data ^
  -v "%CD%\config:/config:ro" ^
  behram527/patient-vitals-volume:1.0
```

Skip the volume and the file lives only in the container layer. `docker rm` takes the readings with it:

```bash
docker rm -f vitals
docker run -d --name vitals -p 8000:8000 behram527/patient-vitals-volume:1.0
```

## Useful volume commands

```bash
docker volume ls
docker volume inspect patient-vitals-volume_vitals-data
```

The inspect output shows where Docker parked the files. On Docker Desktop that path is inside the Linux VM, not a normal folder in Explorer.

Back up the volume by copying the file out with a short-lived container:

```bash
docker run --rm -v patient-vitals-volume_vitals-data:/data -v "%CD%:/backup" alpine tar czf /backup/vitals-backup.tar.gz -C /data .
```

Compose name prefix can differ. `docker volume ls` is the way to confirm the real name before you archive it.

Remove the volume only when you mean to wipe the records:

```bash
docker compose down -v
```

`docker volume prune` deletes every volume that no container is using. I look at `docker volume ls` before I run that on a machine that has anything I care about.

## How I decide between the two

I use a named volume when the app creates the data and I need it after the container is replaced. Vitals, uploads, a database directory.

I use a bind mount when the file already lives on the host and the container should see that exact file. Here that is `clinic.json`. Source code during development is the other common case.

I leave scratch files in the container layer when losing them is fine.

A couple of habits that fell out of building this:

- One volume for the data. The config stays on the bind mount, not mixed into `vitals-data`.
- The mount is read-only because the API only needs to read the clinic file.
- The process runs as uid 1000, and the image creates `/data` as that user. A new named volume picks up those permissions, so the app can write without running as root.
- The image tag is `1.0`, not `latest`, so a later rebuild does not silently change what this volume was written by.
- `down` stops the app. `down -v` deletes the data. I treat those as different commands.

## Endpoints

| Method | Path | What it does |
| --- | --- | --- |
| GET | `/` | App name, clinic, and where the data file is |
| GET | `/health` | Health check |
| GET | `/config` | Clinic settings and whether they came from the bind mount |
| POST | `/vitals` | Append one reading to the volume |
| GET | `/vitals` | Return every reading in the file |
| GET | `/vitals/summary` | Count and averages |

Example body:

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

## Build locally

```bash
docker build -t behram527/patient-vitals-volume:1.0 .
```

## Limits

This is a learning project. The file on the volume is not a database, there is no login, and nothing here should receive real patient data. A production service would want authentication, backups you have actually restored, and a datastore that matches the write load.
