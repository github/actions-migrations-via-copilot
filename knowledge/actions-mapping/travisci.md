# Travis CI to GitHub Actions Mapping Guide

This guide provides comprehensive mappings for converting Travis CI configurations to GitHub Actions workflows.

## Configuration Structure Mappings

| Travis CI         | GitHub Actions                | Notes                            |
| ----------------- | ----------------------------- | -------------------------------- |
| `.travis.yml`     | `.github/workflows/*.yml`     | Multiple workflow files possible |
| `language:`       | Setup actions                 | Language-specific setup actions  |
| `os:`             | `runs-on:`                    | Runner selection                 |
| `dist:`           | `runs-on:`                    | Ubuntu distribution mapping      |
| `sudo:`           | Not needed                    | All jobs have sudo access        |
| `before_install:` | Early `steps:`                | Pre-setup steps                  |
| `install:`        | `steps:`                      | Dependency installation          |
| `before_script:`  | `steps:`                      | Pre-test setup                   |
| `script:`         | `steps:`                      | Main execution steps             |
| `after_script:`   | `steps:` with `if: always()`  | Post-execution steps             |
| `after_success:`  | `steps:` with `if: success()` | Success-only steps               |
| `after_failure:`  | `steps:` with `if: failure()` | Failure-only steps               |
| `deploy:`         | Deployment job                | Separate job with environment    |

## Language and Runtime Mappings

### Node.js

```yaml
# Travis CI
language: node_js
node_js:
  - "14"
  - "16"
  - "18"

# GitHub Actions
jobs:
  build:
    strategy:
      matrix:
        node-version: [14, 16, 18]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
```

### Python

```yaml
# Travis CI
language: python
python:
  - "3.8"
  - "3.9"
  - "3.10"

# GitHub Actions
jobs:
  build:
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
```

### Ruby

```yaml
# Travis CI
language: ruby
rvm:
  - 2.7
  - 3.0
  - 3.1

# GitHub Actions
jobs:
  build:
    strategy:
      matrix:
        ruby-version: ['2.7', '3.0', '3.1']
    steps:
      - uses: actions/checkout@v4
      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: ${{ matrix.ruby-version }}
```

### Java

```yaml
# Travis CI
language: java
jdk:
  - openjdk8
  - openjdk11
  - openjdk17

# GitHub Actions
jobs:
  build:
    strategy:
      matrix:
        java-version: ['8', '11', '17']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: ${{ matrix.java-version }}
```

### Go

```yaml
# Travis CI
language: go
go:
  - 1.18
  - 1.19
  - 1.20

# GitHub Actions
jobs:
  build:
    strategy:
      matrix:
        go-version: ['1.18', '1.19', '1.20']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: ${{ matrix.go-version }}
```

### PHP

```yaml
# Travis CI
language: php
php:
  - 7.4
  - 8.0
  - 8.1

# GitHub Actions
jobs:
  build:
    strategy:
      matrix:
        php-version: ['7.4', '8.0', '8.1']
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ matrix.php-version }}
```

## Build Matrix Mappings

### Simple Matrix

```yaml
# Travis CI
env:
  - NODE_ENV=test
  - NODE_ENV=production

# GitHub Actions
strategy:
  matrix:
    node-env: [test, production]
env:
  NODE_ENV: ${{ matrix.node-env }}
```

### Multi-Dimensional Matrix

```yaml
# Travis CI
os:
  - linux
  - osx
python:
  - "3.8"
  - "3.9"

# GitHub Actions
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest]
    python-version: ['3.8', '3.9']
runs-on: ${{ matrix.os }}
steps:
  - uses: actions/setup-python@v5
    with:
      python-version: ${{ matrix.python-version }}
```

### Matrix with Include

```yaml
# Travis CI
matrix:
  include:
    - os: linux
      python: 3.8
      env: TOXENV=py38
    - os: osx
      python: 3.9
      env: TOXENV=py39

# GitHub Actions
strategy:
  matrix:
    include:
      - os: ubuntu-latest
        python-version: '3.8'
        toxenv: py38
      - os: macos-latest
        python-version: '3.9'
        toxenv: py39
runs-on: ${{ matrix.os }}
```

### Matrix with Exclude

```yaml
# Travis CI
matrix:
  exclude:
    - os: osx
      node_js: "14"

# GitHub Actions
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest]
    node-version: [14, 16, 18]
    exclude:
      - os: macos-latest
        node-version: 14
```

## Operating System Mappings

| Travis CI OS           | GitHub Actions Runner     | Notes                  |
| ---------------------- | ------------------------- | ---------------------- |
| `os: linux`            | `runs-on: ubuntu-latest`  | Default Linux          |
| `dist: xenial`         | `runs-on: ubuntu-20.04`   | Older Ubuntu           |
| `dist: bionic`         | `runs-on: ubuntu-20.04`   | Ubuntu 18.04           |
| `dist: focal`          | `runs-on: ubuntu-22.04`   | Ubuntu 20.04           |
| `os: osx`              | `runs-on: macos-latest`   | Latest macOS           |
| `osx_image: xcode12.5` | `runs-on: macos-11`       | Specific macOS version |
| `os: windows`          | `runs-on: windows-latest` | Windows Server         |

## Service Dependencies

### PostgreSQL

```yaml
# Travis CI
services:
  - postgresql

# GitHub Actions
services:
  postgres:
    image: postgres:13
    env:
      POSTGRES_PASSWORD: postgres
    ports:
      - 5432:5432
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

### MySQL

```yaml
# Travis CI
services:
  - mysql

# GitHub Actions
services:
  mysql:
    image: mysql:8.0
    env:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: test
    ports:
      - 3306:3306
    options: >-
      --health-cmd="mysqladmin ping"
      --health-interval=10s
      --health-timeout=5s
      --health-retries=3
```

### Redis

```yaml
# Travis CI
services:
  - redis-server

# GitHub Actions
services:
  redis:
    image: redis:6
    ports:
      - 6379:6379
    options: >-
      --health-cmd "redis-cli ping"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

### MongoDB

```yaml
# Travis CI
services:
  - mongodb

# GitHub Actions
services:
  mongodb:
    image: mongo:5.0
    ports:
      - 27017:27017
    options: >-
      --health-cmd "mongo --eval 'db.adminCommand(\"ping\")'"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

### Docker

```yaml
# Travis CI
services:
  - docker

# GitHub Actions
# Docker is pre-installed on all GitHub runners
# No additional configuration needed
steps:
  - run: docker --version
  - run: docker build -t myapp .
```

## Addon Mappings

### APT Packages

```yaml
# Travis CI
addons:
  apt:
    packages:
      - libcurl4-openssl-dev
      - libssl-dev

# GitHub Actions
steps:
  - run: |
      sudo apt-get update
      sudo apt-get install -y libcurl4-openssl-dev libssl-dev
```

### Chrome

```yaml
# Travis CI
addons:
  chrome: stable

# GitHub Actions
steps:
  - uses: browser-actions/setup-chrome@v1
    with:
      chrome-version: stable
```

### Firefox

```yaml
# Travis CI
addons:
  firefox: latest

# GitHub Actions
steps:
  - uses: browser-actions/setup-firefox@v1
    with:
      firefox-version: latest
```

### Homebrew (macOS)

```yaml
# Travis CI
addons:
  homebrew:
    packages:
      - cmake
      - boost

# GitHub Actions
steps:
  - run: |
      brew install cmake boost
```

## Cache Mappings

### Generic Cache

```yaml
# Travis CI
cache:
  directories:
    - node_modules
    - .npm

# GitHub Actions
steps:
  - uses: actions/cache@v4
    with:
      path: |
        node_modules
        .npm
      key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
      restore-keys: |
        ${{ runner.os }}-node-
```

### Language-Specific Cache

```yaml
# Travis CI - npm
cache: npm

# GitHub Actions
steps:
  - uses: actions/setup-node@v4
    with:
      node-version: '16'
      cache: 'npm'

# Travis CI - pip
cache: pip

# GitHub Actions
steps:
  - uses: actions/setup-python@v5
    with:
      python-version: '3.9'
      cache: 'pip'

# Travis CI - bundler
cache: bundler

# GitHub Actions
steps:
  - uses: ruby/setup-ruby@v1
    with:
      ruby-version: '3.0'
      bundler-cache: true
```

## Build Stages

```yaml
# Travis CI
stages:
  - test
  - name: deploy
    if: branch = main

jobs:
  include:
    - stage: test
      script: npm test
    - stage: deploy
      script: ./deploy.sh

# GitHub Actions
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test

  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh
```

## Conditional Execution

### Branch Conditions

| Travis CI                 | GitHub Actions                                     |
| ------------------------- | -------------------------------------------------- |
| `if: branch = main`       | `if: github.ref == 'refs/heads/main'`              |
| `if: branch =~ ^release`  | `if: startsWith(github.ref, 'refs/heads/release')` |
| `if: tag IS present`      | `if: startsWith(github.ref, 'refs/tags/')`         |
| `if: type = pull_request` | `if: github.event_name == 'pull_request'`          |
| `if: type = push`         | `if: github.event_name == 'push'`                  |

### Environment Conditions

```yaml
# Travis CI
if: env(DEPLOY) = true

# GitHub Actions
if: env.DEPLOY == 'true'
```

## Deployment Providers

### Heroku

```yaml
# Travis CI
deploy:
  provider: heroku
  api_key:
    secure: encrypted_key
  app: my-app

# GitHub Actions
- uses: akhileshns/heroku-deploy@v3.13.15
  with:
    heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
    heroku_app_name: my-app
    heroku_email: ${{ secrets.HEROKU_EMAIL }}
```

### AWS S3

```yaml
# Travis CI
deploy:
  provider: s3
  access_key_id: $AWS_ACCESS_KEY
  secret_access_key: $AWS_SECRET_KEY
  bucket: my-bucket

# GitHub Actions
- uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: us-east-1
- run: aws s3 sync ./build s3://my-bucket
```

### GitHub Releases

```yaml
# Travis CI
deploy:
  provider: releases
  api_key: $GITHUB_TOKEN
  file: release.zip

# GitHub Actions
- uses: softprops/action-gh-release@v1
  with:
    files: release.zip
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### npm

```yaml
# Travis CI
deploy:
  provider: npm
  email: user@example.com
  api_key: $NPM_TOKEN

# GitHub Actions
- uses: actions/setup-node@v4
  with:
    node-version: '16'
    registry-url: 'https://registry.npmjs.org'
- run: npm publish
  env:
    NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### GitHub Pages

```yaml
# Travis CI
deploy:
  provider: pages
  skip_cleanup: true
  github_token: $GITHUB_TOKEN
  local_dir: build

# GitHub Actions
- uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./build
```

## Notification Mappings

### Slack

```yaml
# Travis CI
notifications:
  slack:
    rooms:
      - secure: encrypted_webhook

# GitHub Actions
- uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
    payload: |
      {
        "text": "Build ${{ job.status }}: ${{ github.workflow }}"
      }
```

### Email

```yaml
# Travis CI
notifications:
  email:
    recipients:
      - team@example.com
    on_success: change
    on_failure: always

# GitHub Actions
- uses: dawidd6/action-send-mail@v3
  if: failure()
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: Build Failed - ${{ github.workflow }}
    to: team@example.com
    from: CI/CD
```

## Environment Variables

### Travis CI Default Variables to GitHub Context

| Travis CI Variable     | GitHub Actions Equivalent                 |
| ---------------------- | ----------------------------------------- |
| `$TRAVIS_BRANCH`       | `${{ github.ref_name }}`                  |
| `$TRAVIS_COMMIT`       | `${{ github.sha }}`                       |
| `$TRAVIS_PULL_REQUEST` | `${{ github.event.pull_request.number }}` |
| `$TRAVIS_REPO_SLUG`    | `${{ github.repository }}`                |
| `$TRAVIS_BUILD_NUMBER` | `${{ github.run_number }}`                |
| `$TRAVIS_BUILD_ID`     | `${{ github.run_id }}`                    |
| `$TRAVIS_JOB_NUMBER`   | `${{ github.job }}`                       |
| `$TRAVIS_TAG`          | `${{ github.ref_name }}` (when tag)       |
| `$TRAVIS_BUILD_DIR`    | `${{ github.workspace }}`                 |
| `$TRAVIS_EVENT_TYPE`   | `${{ github.event_name }}`                |

## Trigger Mappings

```yaml
# Travis CI - All branches
branches:
  only:
    - main
    - develop

# GitHub Actions
on:
  push:
    branches:
      - main
      - develop

# Travis CI - Exclude branches
branches:
  except:
    - experimental

# GitHub Actions
on:
  push:
    branches-ignore:
      - experimental

# Travis CI - Tags only
branches:
  only:
    - /^v\d+\.\d+\.\d+$/

# GitHub Actions
on:
  push:
    tags:
      - 'v*.*.*'
```

## Lifecycle Hook Mappings

### Complete Lifecycle Example

```yaml
# Travis CI
before_install:
  - echo "Before install"

install:
  - npm install

before_script:
  - echo "Before script"

script:
  - npm test
  - npm run build

after_script:
  - echo "After script"

after_success:
  - npm run coverage

after_failure:
  - cat logs/error.log

# GitHub Actions
steps:
  - uses: actions/checkout@v4

  - name: Before install
    run: echo "Before install"

  - name: Install dependencies
    run: npm install

  - name: Before script
    run: echo "Before script"

  - name: Run tests
    run: npm test

  - name: Build
    run: npm run build

  - name: After script
    if: always()
    run: echo "After script"

  - name: Upload coverage
    if: success()
    run: npm run coverage

  - name: Show error logs
    if: failure()
    run: cat logs/error.log
```

## Best Practices

1. **Matrix Strategy**: Use GitHub Actions matrix for multi-dimensional builds
2. **Caching**: Implement caching with `actions/cache` or built-in cache options
3. **Service Configuration**: Add health checks to service containers
4. **Environment Protection**: Use GitHub environments for deployment protection
5. **Secret Management**: Store all sensitive data in GitHub Secrets
6. **Conditional Execution**: Use `if:` conditions for conditional steps and jobs
7. **Job Dependencies**: Use `needs:` to define job execution order
8. **Artifact Sharing**: Use upload/download artifact actions for file sharing
9. **Validation**: Run actionlint for workflow validation
10. **Documentation**: Create comprehensive migration reports with actual validation results
