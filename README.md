# 🤠 PDS Engineering Actions: Roundup

This is an [action for GitHub](https://github.com/features/actions) that does a "roundup"; that is, continuous integration and continuous delivery of PDS software. (Somehow we got started on this "Western" kind of terminology and dadgum, we're stickin' with it 🤠.)


## ℹ️ Using this Action

To use this action in your own workflow, just provide it `with` the following parameter(s):

-   `assembly` — Tells what kind if roundup we're doing, such as `stable` (production); defaults to `unstable` or "development" releases.

Depending on the roundup, you may also need the following environment variables:

-   `ADMIN_GITHUB_TOKEN` — an access token that has administrative permissions in the repository; see below
-   `pypi_username` — Username to use when registering a Python package
-   `pypi_password` — Password for `pypi_username`
-   `ossrh_username` — Username to use for uploading a snapshot [OSSRH](https://central.sonatype.org/pages/ossrh-guide.html) artifact
-   `ossrh_password` — Password for `ossrh_username`
-   `CODE_SIGNING_KEY` — GPG **private** key (base64 encoded) with which to sign artifacts

(Note that `GITHUB_TOKEN` is also used by the Roundup, but it's automatically provided by the GitHub Actions system.)


### 👮‍♂️ GitHub Admin Token

The Roundup action must have access to various target repositories. This is afforded by a token, `ADMIN_GITHUB_TOKEN` in the environment. To set up such a token:

1.  Vist your GitHub account's Settings.
2.  Go to "Developer Settings".
3.  Go to "Personal access tokens".
4.  Press "Generate new token"; authenticate if needed.
5.  Add a note for the token, such as "PDS Ping Repo Access"
6.  Check the following scopes:
    -   `repo:status`
    -   `repo_deployment`
    -   `public_repo`
7. Press "Generate new token"

Save the token (a hex string) and install it in your source repository or organization:

1.  Visit the source repository's or organization's web page on GitHub.
2.  Go to "Settings".
3.  Go to "Secrets".
4.  Press "New secret".
5.  Name the secret, such as `ADMIN_GITHUB_TOKEN`, and insert the token's saved hex string as the value.
6.  Press "Add secret".

You can now (and should) destroy any saved copies of the token's hex string.


### 🔑 Code Signing Key

Signing code artifacts helps ensure that the code is not just created by who we say created it but that it's unmodified and free from inserted hacks like trojans or viruses. (Of course, it says nothing about the code's _quality_, which may be questionable or could itself _be_ a trojan or virus.) The Roundup uses the code signing key to automatically make these assertions by signing code artifacts it sends to the [OSSRH](https://central.sonatype.org/pages/ossrh-guide.html) (in the future, we could also sign Python artifacts sent to the [PyPI](https://pypi.org/)).

**📒 Note:** Whether automatically signing artifacts is a safe practice is left for future discussion.

To set up a code signing key for the Roundup action, first create an OpenPGP-compatible key pair using ``gpg`` or compatible tool; for example, with [GnuPG 2.2](https://www.gnupg.org/), run ``gpg --full-generate-key``:

-   For the kind of key, choose "RSA (sign only)".
-   For the key length, 1024 bits is fine; 4096 is great.
-   For the expiration period, 0 is the least secure, and is what PDS recommends.
-   For the real name, your own name or a group moniker like `PDS Engineering Node` works.
-   For the email address, use your email address or a group email such as `pds-dev@jpl.nasa.gov`.
-   For the comment, mention that it's a code-signing key only; for example, use `SIGNING KEY ONLY from automated processes; trust accordingly`.
-   For the passphrase, skip it; use **no passphrase**.

Note the hex identifier of the generated key pair; use that to export the **private** key and encode it as [base-64](https://en.wikipedia.org/wiki/Base64), which you can then copy and paste into your repository's (or your organization's) secrets. For example, [macOS](https://www.apple.com/macos/) users could type:

    gpg --export-secret-keys HEX-KEY-ID | base64 | pbcopy

This puts the encoded private key onto your pasteboard, ready for pasting into GitHub. Use it as the value for `CODE_SIGNING_KEY`; see the demonstration `yaml` file below.

**📒 Note:** Don't forget to upload the corresponding _public_ key to various keyservers, such as keys.gnupg.net, keys.openpgp.org, keyserver.ubuntu.com pool.sks-keyservers.net, etc.


## 💁‍♀️ Demonstration

The following is a brief example how a workflow that shows how this action can be used:

```yaml
name: 📦 CI/CD

on:
    push:
      branches:
          - master

jobs:
    roundup:
        name: 🤠 Roundup
        runs-on: ubuntu-latest
        steps:
            - 
                name: 💳 Checking out repository
                uses: actions/checkout@v2
            -
                name: 🐄 Rounding it up
                uses: NASA-PDS/roundup-action@master
                with:
                    assembly: 'stable'
                env:
                    ADMIN_GITHUB_TOKEN: ${{secrets.pat}}
                    CODE_SIGNING_KEY:   ${{secrets.CODE_SIGNING_KEY}}
                    ossrh_username:     jocowboy
                    ossrh_password:     ${{secrets.OSSRH_USERNAME}}
                    pypi_username:      snakewrangler
                    pypi_password:      ${{secrets.PYPI_PASSWORD}}
```


## 🔧 Development

Make a local image for testing:

    docker image build --tag pds-roundup:latest .

You can then poke aorund in it:

    docker container run --interactive --tty --rm --name roundup --volume ${PWD}:/mnt --entrypoint /bin/sh pds-roundup:latest

But you could also invoke it the way GitHub Actions does:

    docker container run --interactive --tty --rm --name roundup-dev --workdir /github/workspace \
        --env INPUT_MODE --env HOME --env GITHUB_JOB --env GITHUB_REF --env GITHUB_SHA --env GITHUB_REPOSITORY \
        --env GITHUB_REPOSITORY_OWNER --env GITHUB_RUN_ID --env GITHUB_RUN_NUMBER --env GITHUB_ACTOR \
        --env GITHUB_WORKFLOW --env GITHUB_HEAD_REF --env GITHUB_BASE_REF --env GITHUB_EVENT_NAME \
        --env GITHUB_SERVER_URL --env GITHUB_API_URL --env GITHUB_GRAPHQL_URL \
        --env GITHUB_ACTION --env GITHUB_EVENT_PATH --env GITHUB_PATH --env GITHUB_ENV --env RUNNER_OS \
        --env RUNNER_TOOL_CACHE --env RUNNER_TEMP --env RUNNER_WORKSPACE --env ACTIONS_RUNTIME_URL \
        --env ACTIONS_RUNTIME_TOKEN --env ACTIONS_CACHE_URL --env GITHUB_ACTIONS=true --env CI=true \
        --env GITHUB_WORKSPACE=/github/workspace \
        --env GITHUB_TOKEN=$(cat my-dev-token.txt) \
        --env ADMIN_GITHUB_TOKEN=$(cat my-dev-token.txt) \
        --env pypi_username=joe_cowboy4life \
        --env pypi_password=s3cr3t \
        --env ossrh_username=java_cowboy4life \
        --env ossrh_password=m0rec0ff33 \
        --env GITHUB_REPOSITORY=joecowboy/test-repo \
        --volume /Users/joe/Documents/Development/test-repo:"/github/workspace" \
        pds-roundup --debug --assembly unstable

Or run it locally:

    env ADMIN_GITHUB_TOKEN=abcd0123 GITHUB_REPOSITORY=owner/repo GITHUB_WORKSPACE=/tmp PATH=${PWD}/bin:${PATH} ${PWD}/bin/roundup --debug --assembly unstable


### 🤷‍♀️ Buildout

For reasons I can't fathom, the Python environment used to bootstrap the [buildout](http://buildout.org/) must have [github3.py](https://pypi.org/project/github3.py/) installed into it, despite `github3.py` listed as a dependency in this package. So, as of 2020-10-05, here are the gymnastics:

```console
python3 -m venv /tmp/huh
/tmp/huh/bin/pip install github3.py
/tmp/huh/bin/python3 bootstrap.py --setuptools-version=50.3.0
bin/buildout
```

You can then:

- Run `bin/python` to get a Python with dependencies "baked in" for testing or exploration
- Run `bin/roundup` to try a local roundup (but be prepared to pass in an insane amount of environment variables; see above)
- Run `bin/test` to execute unit, functional, and integration tests with XML test reports suitable for Jenkins or other CI/CD tools
- Expore `parts/omelette` for a greppable source tree of the Roundup code and all its dependencies



