# Migrating Secrets from DroneCI to GitHub Actions

When migrating CI/CD pipelines from DroneCI to GitHub Actions, handling secrets securely is a critical aspect. This guide outlines the best practices and steps to effectively migrate secrets.

## Encrypted Secrets in DroneCI

**Example of defining and encrypted secrets in DroneCI**

```yaml
kind: pipeline
name: default

steps:
- name: build
  image: alpine
  environment:
    USERNAME:
      from_secret: username

---
kind: secret
name: username
data: hl3v+FODjduX0UpXBHgYzPzVTppQblg51CVgCbgDk4U=
```

**Example of GitHub Actions Equivalent**

```yaml
name: Build
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Use secret
        run: echo "Username is ${{ secrets.USERNAME }}"
```

## Repository and Organization Secrets

A DroneCI pipeline can access secrets defined at both the repository and organization levels. They are referenced by use of the `from_secret` keyword. They will not an associated secret definition in the pipeline file.

**Example of using organization-level secrets in DroneCI**

```yaml
kind: pipeline
name: default

steps:
- name: build
  image: alpine
  environment:
    USERNAME:
      from_secret: docker_username
    PASSWORD:
      from_secret: docker_password
  commands:
    - echo "You can call the secrets like this examples below."
    - echo $USERNAME
    - echo $PASSWORD
    - echo "In both cases, and for security reasons, you will see asteriks '*******' instead the value under the echo command."
```

**Example of GitHub Actions Equivalent**

```yaml
name: Build
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Use organization secrets
        run: |
          echo "Docker Username is ${{ secrets.DOCKER_USERNAME }}"
          echo "Docker Password is ${{ secrets.DOCKER_PASSWORD }}"
```

---

*For security best practices, migration checklists, and troubleshooting guidance, refer to [Migration Guardrails](docs/migration-guardrails.md) and [Migration Standards](docs/migration-standards.md) in the knowledge base.*