
export interface MorphTargetDictionary {
  [key: string]: number;
}

export interface SceneHandle {
  setMorphTargetInfluence: (name: string, value: number) => void;
  resetMorphTargets: () => void;
}

export type ApiProvider = 'gemini' | 'openrouter';

export interface Settings {
    apiProvider: ApiProvider;
    geminiModel: string;
    openRouterApiKey: string;
    openRouterModel: string;
    speechVoiceURI: string | null;
}

export interface OpenRouterModel {
    id: string;
    name: string;
}
