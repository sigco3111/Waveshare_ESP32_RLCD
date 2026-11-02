# Source Privacy Review

The review object is the independent open-source directory and the source ZIP generated from it; it does not include the development workspace, full device backups, or user configuration. This record is not a substitute for checking Git staged content before the formal commit, nor a complete security audit.

The checks cover private key markers, common access token formats, credential filenames, logs and Flash images, plus credential assignments and personal paths in code. Check results and source file hashes are recorded in SOURCE_PRIVACY_REVIEW.json; the record contains only relative paths, classification, and hashes, and does not copy suspicious credential originals.

Manually reviewed hits:

- GitHub addresses, author nickname, and public contact information in the README and UI are project attribution, and are retained.
- `192.168.1.*` in the Reporter tests is test input, and is retained.
- `pairing_token` is generated randomly at runtime or read from user configuration; the Wi-Fi password field is settings form data; no embedded actual values were found.
- `release/keys/syna-release-public.pem` is a verification public key and may be public; the release private key must not be committed.
- Build records and scripts still contain author environment paths or default toolchain paths; these are portability limits, not a verified generic environment.
- Original Flash images, Reporter configuration, and raw device logs are kept locally on the computer and are not copied into the release package.

Generated directories and caches are excluded; when formally uploading, review the actual staged list and avoid commands that force-add ignored files. Re-check and regenerate the candidate package and hash manifest after source content changes.
