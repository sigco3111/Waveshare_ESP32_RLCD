# Release Materials

This directory contains third-party licenses, public signature verification tools, and the public key. It does not contain the signing private key, device backups, or build artifacts.

Before an official release, complete the [Release Checklist](../docs/RELEASE_CHECKLIST.md), rebuild and verify the artifacts from the release source, then generate the hash manifest. sign_release.py supports sign / verify; run --help to see the parameters. Only the publisher holding the corresponding private key can sign official files, and the private key must not be uploaded.

The version number file and the in-program display are 1.0.0, but this organized directory is not yet an official release. Do not describe development-machine test records, unaccepted Mac packages, or new local manifests as officially released artifacts.