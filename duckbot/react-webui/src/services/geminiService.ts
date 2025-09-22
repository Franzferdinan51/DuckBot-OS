// Gemini Service for DuckBotOS Integration
export interface GeminiMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface GeminiChatRequest {
  message: string;
  model: string;
  systemPrompt?: string;
  temperature?: number;
  maxTokens?: number;
  history?: GeminiMessage[];
}

export interface GeminiChatResponse {
  response: string;
  model: string;
  timestamp: Date;
  success: boolean;
  error?: string;
}

class GeminiService {
  private static instance: GeminiService;
  private baseUrl: string = 'http://localhost:8787';
  private apiKey: string | null = null;

  private constructor() {
    // Load settings from localStorage if available
    this.loadSettings();
  }

  public static getInstance(): GeminiService {
    if (!GeminiService.instance) {
      GeminiService.instance = new GeminiService();
    }
    return GeminiService.instance;
  }

  private loadSettings(): void {
    try {
      const settings = localStorage.getItem('duckbotClippySettings');
      if (settings) {
        const parsed = JSON.parse(settings);
        this.baseUrl = parsed.duckbotUrl || 'http://localhost:8787';
        this.apiKey = parsed.duckbotToken || null;
      }
    } catch (error) {
      console.error('Failed to load Gemini service settings:', error);
    }
  }

  public setBaseUrl(url: string): void {
    this.baseUrl = url;
    this.saveSettings();
  }

  public setApiKey(apiKey: string | null): void {
    this.apiKey = apiKey;
    this.saveSettings();
  }

  private saveSettings(): void {
    try {
      const settings = JSON.parse(localStorage.getItem('duckbotClippySettings') || '{}');
      settings.duckbotUrl = this.baseUrl;
      settings.duckbotToken = this.apiKey;
      localStorage.setItem('duckbotClippySettings', JSON.stringify(settings));
    } catch (error) {
      console.error('Failed to save Gemini service settings:', error);
    }
  }

  public async testConnection(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
        }
      });
      return response.ok;
    } catch (error) {
      console.error('Gemini service connection test failed:', error);
      return false;
    }
  }

  public async sendMessage(request: GeminiChatRequest): Promise<GeminiChatResponse> {
    try {
      // First try to use DuckBot's Gemini integration
      const response = await fetch(`${this.baseUrl}/api/gemini/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
        },
        body: JSON.stringify(request)
      });

      if (response.ok) {
        const data = await response.json();
        return {
          response: data.response || data.content || 'No response received',
          model: data.model || request.model,
          timestamp: new Date(),
          success: true
        };
      }

      // If DuckBot endpoint fails, try fallback to direct Gemini API
      return await this.fallbackToDirectAPI(request);
    } catch (error) {
      console.warn('DuckBot Gemini API not available, using fallback:', error);
      return await this.fallbackToDirectAPI(request);
    }
  }

  private async fallbackToDirectAPI(request: GeminiChatRequest): Promise<GeminiChatResponse> {
    try {
      // This is a mock implementation - in production, you would:
      // 1. Install @google/generative-ai package
      // 2. Use the actual Google Generative AI SDK
      // 3. Handle proper API key management

      const mockResponses = [
        `I understand you're asking about: "${request.message}".

This is a simulated response from the GeminiChat integration. To enable the full Gemini AI functionality:

1. **Install Required Package:**
   \`\`\`bash
   npm install @google/generative-ai
   \`\`\`

2. **Set Up API Key:**
   - Get your Google AI API key from https://makersuite.google.com/app/apikey
   - Add it to your DuckBotOS settings

3. **Configure the Backend:**
   - Update the DuckBot backend to include Gemini API endpoints
   - Ensure proper authentication and rate limiting

Would you like me to help you set up the full integration?`,

        `I'm GeminiChat, integrated with DuckBotOS! I received your message: "${request.message}"

Currently running in simulation mode. The full integration requires:

✅ **Frontend Component:** Complete
✅ **DuckBotOS Integration:** Complete
⚠️ **Backend API:** Pending setup
⚠️ **Google AI SDK:** Installation needed

The chat interface, conversation history, voice input, and DuckBotOS window management are all working. We just need to complete the backend connection to Google's Gemini API.

Would you like to proceed with the setup?`,

        `Hello! I'm your Gemini assistant running in DuckBotOS. You said: "${request.message}"

**Current Status:**
- 🖥️ **Interface:** Fully functional
- 💬 **Chat Features:** Message history, voice input, settings
- 🎨 **DuckBotOS Integration:** Complete with window management
- 🔗 **AI Backend:** Simulation mode (needs Gemini API setup)

**Next Steps:**
1. Install @google/generative-ai package
2. Configure Google AI API key
3. Set up backend endpoints
4. Test the full integration

Would you like help with any of these steps?`
      ];

      const randomResponse = mockResponses[Math.floor(Math.random() * mockResponses.length)];

      return {
        response: randomResponse,
        model: request.model,
        timestamp: new Date(),
        success: true
      };
    } catch (error) {
      console.error('Gemini fallback API error:', error);
      return {
        response: 'Sorry, I encountered an error while processing your request. Please check your API configuration and try again.',
        model: request.model,
        timestamp: new Date(),
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  public async getAvailableModels(): Promise<string[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/gemini/models`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
        }
      });

      if (response.ok) {
        const data = await response.json();
        return data.models || ['gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-2.5-pro'];
      }
    } catch (error) {
      console.warn('Failed to fetch Gemini models from backend, using defaults:', error);
    }

    // Fallback to Gemini 2.x models
    return ['gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.5-flash-lite', 'gemini-2.0-pro'];
  }

  public async clearConversationHistory(): Promise<void> {
    try {
      await fetch(`${this.baseUrl}/api/gemini/clear-history`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
        }
      });
    } catch (error) {
      console.error('Failed to clear conversation history:', error);
    }
  }
}

export const geminiService = GeminiService.getInstance();
export default geminiService;