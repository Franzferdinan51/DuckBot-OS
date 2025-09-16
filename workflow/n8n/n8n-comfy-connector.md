# n8n → ComfyUI Connector (Talking-Head News)

Follow these steps to connect your existing n8n workflow to ComfyUI so the anchor image reads the generated news script as a video.

## Prerequisites
- ComfyUI running at `http://127.0.0.1:8188`.
- Custom nodes installed in ComfyUI Manager: `EdgeTTS` (TTS) and `Wav2Lip`.
- Copy your anchor image to ComfyUI input: `C:\\Users\\Duck1\\Desktop\\workflow\\ComfyUI\\input\\DuckBotNewsAnchor7.png`.

## ComfyUI (API Workflow)
- File added: `ComfyUI-trading-news-video-workflow.API.json` (API format).
- It expects a text input, generates TTS, lip-syncs the anchor, and saves MP4 to `ComfyUI\\output`.
- If your installed node class names differ, adjust the `class_type` fields accordingly in that JSON.

## n8n – Add two nodes after your LLM

1) Function node: “Build Comfy Payload”
- Purpose: Inject the LLM’s news text into the ComfyUI API prompt.
- Function Code:

```
const newsText = $json.newsText ?? $json.summary ?? $json.text ?? 'Breaking news...';

const body = {
  prompt: {
    "1": { class_type: "Text", inputs: { text: newsText } },
    "2": { class_type: "EdgeTTS", inputs: { text: ["1", "text"], voice: "en-US-GuyNeural", rate: "+0%", volume: "+0%" } },
    "3": { class_type: "LoadImage", inputs: { image: "DuckBotNewsAnchor7.png" } },
    "4": { class_type: "Wav2Lip", inputs: { face: ["3", "IMAGE"], audio: ["2", "AUDIO"] } },
    "5": { class_type: "SaveVideo", inputs: { video: ["4", "VIDEO"], filename_prefix: "news_cast" } },
  },
  client_id: 'n8n',
};

return [{ body }];
```

2) HTTP Request node: “Send to ComfyUI”
- Method: `POST`
- URL: `http://127.0.0.1:8188/prompt`
- Authentication: None
- Headers: `Content-Type: application/json`
- Body: Raw → JSON → Expression → `={{$json.body}}`

(Optional) Poll completion:
- The POST response contains `prompt_id`. Poll `GET http://127.0.0.1:8188/history/{{$json.prompt_id}}` until you see a saved video output.

## Notes & Troubleshooting
- Paths: `LoadImage.image` must be just the filename in ComfyUI’s `input` folder.
- Class names: If ComfyUI shows “unknown class”, install the corresponding custom nodes or update `class_type` to match the installed node name.
- Voice: Change `voice` (e.g., `en-US-JennyNeural`) and TTS rate/volume as needed.
- Output: Check `C:\\Users\\Duck1\\Desktop\\workflow\\ComfyUI\\output\\` for the MP4.

## Mapping to Your Existing Files
- ComfyUI: Use `ComfyUI-trading-news-video-workflow.API.json` instead of the old `trading-news-video-workflow.json` when calling the API.
- n8n: Insert the two nodes above into `OpenRouter Trading  Analysis Bot-Video Beta3` right after the node that produces the final news text.

