# Deployment Notes

The assessment asks for:

1. A source code repository, such as GitHub or similar.
2. A deployed application URL that other people can access and test.

## Recommended Deployment Path

Use GitHub plus Streamlit Community Cloud.

## GitHub Repository Steps

From the project folder:

```bash
git init
git add .
git commit -m "Initial TTB label verification assistant"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git push -u origin main
```

If Git is not installed locally, create a new GitHub repository in the browser and upload the files from this archive.

## Streamlit Community Cloud Steps

1. Go to `https://streamlit.io/cloud`.
2. Sign in with GitHub.
3. Select **New app**.
4. Choose the repository and branch.
5. Set the main file path to `app.py`.
6. Deploy the app.
7. Copy the deployed Streamlit URL into the assessment form.

## Important Deployment Files

- `requirements.txt` installs Python packages.
- `packages.txt` installs the system-level `tesseract-ocr` package on Streamlit Cloud.
- `.streamlit/config.toml` contains basic Streamlit runtime configuration.

## Local Run Command

```bash
streamlit run app.py
```

If Tesseract OCR is missing locally, install it first and ensure it is available on `PATH`.
