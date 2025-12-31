# Facility Application Backend

## Description
This is the Facility Application backend that handles storing the bookings into the database.

## How to start up the application

### 1. To start up flask on local

flask --app app run --port 9000
flask --app app run --port 9000 --debug

### 2. To make flask listen to all IPs on the machine

flask run --host=0.0.0.0

## How to Deploy Backend to Google Cloud

The steps below show how to build and push the Facility application backend Docker image to Google Cloud Artifact Registry, so it can be run on Cloud Run, GKE, or other environments.

### 1. Install prerequisites

You need the following tools installed locally:

- Docker
- Pack Build (`pack` CLI)
- Google Cloud SDK (`gcloud`)

Example (macOS with Homebrew) for installing gcloud:

```bash
brew install --cask google-cloud-sdk
```

Make sure you have authenticated with your Google account:

```bash
gcloud init
gcloud auth login
```

### 2. Configure Docker and grant IAM permissions

Configure Docker to use Artifact Registry in the region:

```bash
gcloud auth configure-docker asia-southeast1-docker.pkg.dev
```

Grant the account permission to push images to Artifact Registry (replace `EMAIL` with your user or service account):

```bash
gcloud projects add-iam-policy-binding service-desk-482804 \
  --member="user:EMAIL" \
  --role="roles/artifactregistry.writer"
```

### 3. Create the Artifact Registry repository

Create a Docker repository named `facility` in Artifact Registry using command below or console:

```bash
gcloud artifacts repositories create facility \
  --repository-format=docker \
  --location=asia-southeast1 \
  --description="Docker repo for Facility application backend"
```

You only need to run this once per project/region.

### 4. Build the Docker image with Pack

On the local, from the repository root, build the backend image using Buildpacks:

```bash
pack build facility-backend \
  --builder=gcr.io/buildpacks/builder \
  --path facility-backend
```

This produces a local Docker image named `facility-backend`.

### 5. Tag the image for Artifact Registry

Tag the local image with the Artifact Registry repository URL:

```bash
docker tag facility-backend \
  asia-southeast1-docker.pkg.dev/service-desk-482804/facility/facility-backend:latest
```

### 6. Push the image to Artifact Registry

Finally, push the tagged image:

```bash
docker push asia-southeast1-docker.pkg.dev/service-desk-482804/facility/facility-backend:latest
```

You can now use this image in Cloud Run, GKE, or other deployment targets that support Artifact Registry images.

## How to Connect Cloud Run to Cloud SQL (Postgres)

These steps assume you already have:
- A Cloud SQL for PostgreSQL instance created
- The Facility application backend image pushed to Artifact Registry (see section above)

### 1. Enable required Google Cloud APIs

Make sure the Cloud SQL Admin API is enabled in your project:

```bash
gcloud services enable sqladmin.googleapis.com
```

You may also need the Cloud Run API enabled (once per project):

```bash
gcloud services enable run.googleapis.com
```

### 2. Grant Cloud SQL access to the Cloud Run service account

Grant the Cloud Run runtime service account permission to connect to Cloud SQL. Replace the service account email if yours differs:

```bash
gcloud projects add-iam-policy-binding service-desk-482804 \
  --member="serviceAccount:262012824206-compute@developer.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

### 3. Deploy Cloud Run service with environment variables

Deploy the Cloud Run service using the image from Artifact Registry and the `env.yaml` file for configuration:

```bash
gcloud run deploy facility-backend \
  --image asia-southeast1-docker.pkg.dev/service-desk-482804/facility/facility-backend:latest \
  --region asia-southeast1 \
  --platform managed \
  --allow-unauthenticated \
  --env-vars-file env.yaml \
  --add-cloudsql-instances service-desk-482804:asia-southeast1:service-desk-database \
  --port 8080
```

If your application uses the Cloud SQL Auth Proxy (via connection string or socket), ensure the corresponding environment variables (e.g. `DB_HOST`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`) in `env.yaml` match your Cloud SQL instance configuration.
