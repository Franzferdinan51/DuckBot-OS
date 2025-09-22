export interface MorphTargetDictionary {
  [key: string]: number;
}

export interface SceneHandle {
  setMorphTargetInfluence: (name: string, value: number) => void;
  resetMorphTargets: () => void;
}

export type ApiProvider = 'duckbot' | 'lmstudio' | 'openrouter';

export interface Settings {
    apiProvider: ApiProvider;
    duckbotUrl: string;
    duckbotToken: string | null;
    lmStudioUrl: string;
    lmStudioModel: string;
    openRouterApiKey: string;
    openRouterModel: string;
    speechVoiceURI: string | null;
    useVibeVoice: boolean;
}

export interface DuckBotModel {
    id: string;
    name: string;
    description?: string;
}

export interface LMStudioModel {
    id: string;
    name: string;
    size?: number;
}

export interface OpenRouterModel {
    id: string;
    name: string;
}

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp?: number;
}

export interface DuckBotResponse {
    content: string;
    model?: string;
    usage?: {
        prompt_tokens?: number;
        completion_tokens?: number;
        total_tokens?: number;
    };
}