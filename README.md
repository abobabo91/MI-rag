# Vertex AI RAG Chat

A powerful, document-aware chat application powered by Google's state-of-the-art Gemini models and Vertex AI RAG Engine.

---

## 📖 What is this? (Plain English)

Imagine you have a super-smart assistant (the AI), but it doesn't know anything about your specific company documents or private data. **RAG (Retrieval-Augmented Generation)** is the technology that "hands" the AI your documents so it can read them and answer questions based *specifically* on your data.

This tool allows you to:
1.  **Upload Documents:** Text files, PDFs, etc.
2.  **Store them Securely:** Using Google's **Vertex AI RAG Corpus** (think of this as a secure digital library).
3.  **Chat:** Ask questions, and the AI will look up the answers in your documents and cite its sources.

### Key Components
*   **Vertex AI:** Google's platform for building AI applications. It provides the "brains" (Gemini models).
*   **Gemini Models (e.g., 3 Pro, 2.5 Flash):** The specific AI versions. Newer versions (higher numbers) are smarter or faster.
*   **Cloud Run:** The service that hosts this website on the internet so you don't have to keep your laptop open.

---

## 🛠️ Setup & Prerequisites

Before running this, you need a Google Cloud Project with the **Vertex AI API** enabled.

### 1. Authentication (OAuth)
To log in securely, you need Google OAuth credentials.

1.  Go to the [Google Cloud Console > APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials).
2.  Click **Create Credentials** > **OAuth client ID**.
3.  Application type: **Web application**.
4.  **Authorized Redirect URIs:**
    *   For local testing: `http://localhost:8501`
    *   For Cloud deployment: `https://vertex-rag-app-928136222747.us-east1.run.app` (This is your currently running app).
5.  Download the JSON file or copy the **Client ID** and **Client Secret**.

### 2. Vertex AI RAG Corpus
You need a "Corpus" (a storage bucket for your RAG index) created in Vertex AI.
*   **Manage Corpora:** [Vertex AI RAG Console](https://console.cloud.google.com/vertex-ai/rag/corpus)
*   The App currently uses a hardcoded ID: `6917529027641081856`.
*   If you need to change this, edit `PROJECT_ID` and `DEFAULT_RAG_CORPUS_ID` in `utils.py`.

---

## 💻 How to Run Locally

1.  **Install Requirements:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Secrets:**
    Create a file named `.streamlit/secrets.toml` with your credentials:
    ```toml
    [google_auth]
    client_id = "YOUR_CLIENT_ID"
    client_secret = "YOUR_CLIENT_SECRET"
    redirect_uri = "http://localhost:8501"
    ```

3.  **Run the App:**
    ```bash
    streamlit run RAG_Chat.py
    ```

---

## 🚀 How to Deploy to Google Cloud Run

We deploy to **Cloud Run** because it's serverless (scales to zero when not used to save money) and secure.
*   **Manage Services:** [Cloud Run Console](https://console.cloud.google.com/run/overview)

### Option 1: Automatic Deployment (Recommended)
This project is connected to **Cloud Build**. Whenever you push changes to the `master` branch on GitHub, a new deployment is automatically triggered!

1.  Make your changes.
2.  Commit and push:
    ```bash
    git add .
    git commit -m "Your update message"
    git push origin master
    ```
3.  Watch the build status in the [Cloud Build Console](https://console.cloud.google.com/cloud-build/builds).

### Option 2: Manual Deployment (CLI)
If you need to deploy manually from your terminal (e.g., for testing without pushing):

Run this single command from the project root:
```bash
gcloud builds submit . --tag gcr.io/isd-1-440812/vertex-rag-app && gcloud run deploy vertex-rag-app --image gcr.io/isd-1-440812/vertex-rag-app --region us-east1 --allow-unauthenticated
```

### Configuration (One Time Setup)
Regardless of how you deploy, you need to configure your secrets once.

#### Configure Secrets (Option A: CLI)
We don't upload the `secrets.toml` file to the cloud for security. Instead, we use **Environment Variables**. Run this command to set them (replace with your actual values):

```bash
gcloud run services update vertex-rag-app --region us-east1 --set-env-vars "GOOGLE_CLIENT_ID=your-client-id,GOOGLE_CLIENT_SECRET=your-client-secret,REDIRECT_URI=https://vertex-rag-app-928136222747.us-east1.run.app"
```

#### Configure Secrets (Option B: Cloud Console UI)
If you prefer clicking through the website:
1.  Go to your [Cloud Run Service](https://console.cloud.google.com/run/overview).
2.  Click **Edit & Deploy New Revision**.
3.  Go to the **Container** tab (usually selected by default).
4.  Scroll down to **Variables & Secrets** > **Environment variables**.
5.  Click **Add Variable** and add these three:
    *   `GOOGLE_CLIENT_ID`: (From your secrets file)
    *   `GOOGLE_CLIENT_SECRET`: (From your secrets file)
    *   `REDIRECT_URI`: (Your Cloud Run URL, e.g., `https://...run.app`)
6.  Click **Deploy**.

### Finalize Auth
1.  Copy your Service URL: **`https://vertex-rag-app-928136222747.us-east1.run.app`**
2.  Go back to the **Google Cloud Console > Credentials**.
3.  Add this URL to the **Authorized Redirect URIs** list for your Client ID.

---

## 🤖 Using the App

1.  **Login:** Use your Google Account.
2.  **Select Model:** Use the sidebar to choose between models like **Gemini 2.5 Flash** (fast) or **Gemini 3 Pro** (smart/preview). You can also type a custom model ID.
3.  **Upload:** Add new documents via the sidebar.
4.  **Chat:** Ask questions! The AI will cite the specific document chunks it used.
