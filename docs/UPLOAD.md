# Upload to your personal GitHub account

The portfolio directory already contains a **fresh Git repository on `main` with no commits and no remote**. No upload has been performed. The original repository is separate.

## 1. Complete the publication review

Read [PUBLICATION_REVIEW.md](PUBLICATION_REVIEW.md) and resolve the rights and permission concerns before uploading anything, including to a private repository. Review the source and screenshot. No licence has been chosen for you.

## 2. Open the prepared folder

In File Explorer, open the folder containing this README and the application files. Right-click inside it and select **Open in Terminal**. Use PowerShell. Confirm you are in the portfolio folder:

```powershell
Get-Location
git rev-parse --show-toplevel
git status --short
git remote -v
```

The repository root must be the portfolio folder, not its parent. `git remote -v` should print nothing. Do not run these instructions from the original project.

## 3. Install and verify

If you have not created a local environment in this folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run the checks:

If `py` is unavailable, use the path to an installed Python interpreter for environment creation. Python 3.11 or 3.12 is the CI target. Read the [installation limitation](VERIFICATION.md) if pip cannot find the pinned packages; do not proceed until installation and checks work on your machine.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe demo.py --headless --scenario pass
.\.venv\Scripts\python.exe demo.py --headless --scenario fail
.\.venv\Scripts\python.exe demo.py --headless --scenario lid-open
.\.venv\Scripts\python.exe demo.py --report
.\.venv\Scripts\python.exe tools/check_publication.py
```

Every command should exit successfully. The workbook and logs stay local and ignored.

## 4. Set your commit identity locally

Replace the text inside the quotes before running these commands. Use your GitHub account's exact private/no-reply commit address from its email settings if you want to keep your personal address private. These commands affect only this repository.

```powershell
git config --local user.name "YOUR PUBLIC DISPLAY NAME"
git config --local user.email "YOUR GITHUB NO-REPLY COMMIT ADDRESS"
```

## 5. Review and make the first commit

```powershell
git add .
git diff --cached --stat
git diff --cached
.\.venv\Scripts\python.exe tools/check_publication.py
git commit -m "Prepare offline light transmission quality tester demo"
git status --short
```

Read the staged changes before the commit. The file list should contain source, tests, docs, the synthetic examples, the SVG badge, the regenerated PNG, and Git/CI settings. It should contain no runtime JSON, report workbooks, logs, environments, original documents, or other workplace files. After committing, `git status --short` should print nothing.

## 6. Create an empty GitHub repository

Sign in to your personal account at [GitHub](https://github.com/new). Choose your personal account as owner and enter:

- Name: `light-transmission-quality-tester`
- Description: copy the description in [PORTFOLIO.md](PORTFOLIO.md).
- Visibility: Public only after resolving the publication review.
- Leave README, `.gitignore`, and licence initialisation unselected: the local folder already supplies the relevant files.

Select **Create repository** and copy its HTTPS repository URL. This follows [GitHub's instructions for adding local code](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).

## 7. Connect and upload

Replace `YOUR_USERNAME` in the URL with your actual personal GitHub username, and adjust the repository name if you chose another one:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/light-transmission-quality-tester.git
git remote -v
```

Check that the displayed URL points to your personal repository. Then upload:

```powershell
git push -u origin main
```

Complete the browser sign-in if Git Credential Manager prompts you. If authentication fails, follow [GitHub's authentication documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github); do not put a token into a source file or remote URL.

## 8. Check the result and add it to your CV

Refresh the repository page. Verify the README and screenshot render, open the **Actions** tab, and confirm the offline checks pass. Do not describe the hosted workflow as passing until its run succeeds. Add topics from [PORTFOLIO.md](PORTFOLIO.md) through the repository's About settings. Link the repository URL on your CV and use the two proposed bullets only where they match your contribution.

Never upload the parent workspace or copy additional workplace material into this repository. Future commits should repeat the staged-file review and publication scan.
