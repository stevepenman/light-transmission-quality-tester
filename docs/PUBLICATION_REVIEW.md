# Publication review

Prepared on 25 October 2026. This document intentionally records categories and actions without reproducing removed identifiers or credentials.

## Included material

The portfolio directory was built from an explicit allowlist: seven application modules, the shared stylesheet, and the existing Python tests. The old sample-report script was excluded and replaced with a deterministic runner. New material consists of an output-path helper, offline runner, synthetic JSON fixtures, neutral SVG badge, a newly rendered screenshot, regression tests, documentation, Git settings, CI, and a heuristic scanner.

## Exclusions and replacements

| Category | Action |
| --- | --- |
| Existing Git history and remotes | Excluded; a fresh local repository was initialised |
| Workplace names and identifying references | Selected source and asset paths reviewed; branding replaced with neutral demo labels |
| Embedded access codes and fallback access | Removed; public session-only demo gate substituted |
| Existing settings and calibration | Excluded; defaults and newly written synthetic examples supplied |
| Histories, counters, logs, reports, databases | Excluded; no original runtime data was copied |
| Credential documents and operator documents | Excluded without importing their contents |
| Existing screenshots, images, and design references | Excluded; one screenshot regenerated from fictional readings |
| Personal contacts and network settings | No real contacts supplied; examples use reserved example domains |
| Equipment access and outbound delivery | Live initialisation and sending code removed; mocks and inert methods retained |
| Local editor environments and installed packages | Excluded; dependencies declared in a minimal requirements file |

The source review covered filenames, string literals, comments, configuration paths, fixture contents, and application-generated labels. Known identifying terms were checked privately against the final publication candidates; removed terms are not listed here. The generated PNG was visually reviewed. File and byte-level checks were used to confirm the original project files remained unchanged.

## Repeatable checks

`python tools/check_publication.py` scans the files Git would publish, including new untracked candidates and staged files. It checks common private network addresses, key/token patterns, personal filesystem paths, non-example email addresses, unexpected binary images, and excluded artifact types. It emits filenames and rule descriptions rather than secret values.

The scanner is heuristic. It cannot recognize every company name, machine identifier, personal detail, encoded secret, or sensitive algorithm. It is not a substitute for reviewing `git diff --cached` before committing. `.gitignore` prevents accidental additions of common runtime and credential artifacts; previously tracked files would still need explicit review.

## Remaining publication concerns

1. **Rights and permission are unresolved.** The original documentation indicated restricted ownership. Replacing names and data does not establish permission to publish source, UI design, algorithms, or workflows. Obtain any necessary permission before uploading; making a repository private still uploads it to a third party.
2. Confirm the retained generic sample workflow, limits, and protocol details may be disclosed. If they cannot, this derivative should not be uploaded.
3. Review the regenerated screenshot and CV wording against your actual contribution. This preparation does not establish authorship.
4. No licence or copyright assertion was created. Third-party dependencies retain their own terms and are not vendored here.
5. Local Git has no commit or remote. Choose the public identity and email you want associated with your first commit.

The portfolio files contain no claim of hardware validation, production deployment, measured performance, or business savings.
