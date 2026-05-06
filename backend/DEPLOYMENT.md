# SpeechWell Backend Deployment

The backend should be deployed as a Docker web service. It needs FFmpeg, Python ML dependencies, local model files from `ml/models/`, and writable persistent storage for uploads, processed audio, generated reports, cache files, and the SQLite database.

## Recommended: Render

1. Push this repo to GitHub.
2. In Render, choose **New +** -> **Blueprint**.
3. Select this repository.
4. Render will read `render.yaml` and create `speechwell-backend`.
5. Set `CORS_ORIGINS` to your frontend URLs:

```text
https://your-vercel-app.vercel.app,https://acexlab.github.io
```

6. Optional but recommended: set one cloud LLM key for grammar/chat:

```text
OPENAI_API_KEY=...
CHAT_PROVIDER=openai
GRAMMAR_PROVIDER=openai
```

After deployment, confirm:

```text
https://your-render-service.onrender.com/api/health
```

Then set the frontend Vercel env var:

```text
VITE_API_URL=https://your-render-service.onrender.com
```

Redeploy the frontend after changing `VITE_API_URL`.

## Notes

- The first audio analysis can be slow because Whisper may download/cache its runtime model to `/var/data/.cache`.
- Keep the persistent disk attached. Without it, uploads, reports, SQLite data, and model caches are lost on restart.
- The Docker image intentionally excludes `ml/datasets/`, reports, local DB files, and virtual environments.
