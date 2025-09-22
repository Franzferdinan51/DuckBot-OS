
import React, { useState, useRef, useCallback, useEffect } from 'react';
import { ThreeScene } from './components/ThreeScene';
import { ChatUI } from './components/ChatUI';
import { getAIResponse as getGeminiAIResponse } from './services/geminiService';
import type { MorphTargetDictionary, SceneHandle, Settings, OpenRouterModel } from './types';

// Add SpeechRecognition types to window for browsers that support it
declare global {
    interface Window {
        SpeechRecognition: any;
        webkitSpeechRecognition: any;
    }
}

// --- OpenRouter Service Functions ---
async function getOpenRouterModels(): Promise<OpenRouterModel[]> {
    try {
        const response = await fetch('https://openrouter.ai/api/v1/models');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        // Filter for free models
        return data.data
            .filter((model: any) => model?.pricing?.prompt === "0" && model?.pricing?.completion === "0")
            .map((model: any) => ({ id: model.id, name: model.name }));
    } catch (error) {
        console.error("Could not fetch OpenRouter models:", error);
        return [];
    }
}

async function getOpenRouterResponse(prompt: string, apiKey: string, model: string): Promise<string> {
    if (!apiKey) {
        throw new Error("OpenRouter API key is not set.");
    }
    const url = 'https://openrouter.ai/api/v1/chat/completions';
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: model || "google/gemini-flash-1.5", // Default to a free model
                messages: [{ "role": "user", "content": prompt }]
            })
        });

        if (!response.ok) {
            const errorBody = await response.json();
            console.error("OpenRouter API Error:", errorBody);
            throw new Error(`OpenRouter API Error: ${errorBody?.error?.message || 'Unknown error'}`);
        }

        const data = await response.json();
        return data.choices[0].message.content;
    } catch (error) {
        console.error("Error calling OpenRouter API:", error);
        throw new Error("Failed to fetch response from OpenRouter.");
    }
}

// Define available Gemini models according to guidelines
const GEMINI_MODELS = ['gemini-2.5-flash'];


const App: React.FC = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [isModelLoaded, setIsModelLoaded] = useState(false);
    const [loadProgress, setLoadProgress] = useState(0);
    const [morphTargetDictionary, setMorphTargetDictionary] = useState<MorphTargetDictionary | null>(null);


    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [settings, setSettings] = useState<Settings>({
        apiProvider: 'gemini',
        geminiModel: GEMINI_MODELS[0],
        openRouterApiKey: '',
        openRouterModel: 'google/gemini-flash-1.5',
        speechVoiceURI: null,
    });
    // Temp state for settings form
    const [tempSettings, setTempSettings] = useState<Settings>(settings);
    const [openRouterModels, setOpenRouterModels] = useState<OpenRouterModel[]>([]);
    const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);

    const [isListening, setIsListening] = useState(false);
    const recognitionRef = useRef<any>(null);

    const sceneRef = useRef<SceneHandle>(null);
    
    // --- Effects ---

    // Populate speech synthesis voices
    useEffect(() => {
        const populateVoiceList = () => {
            const availableVoices = window.speechSynthesis.getVoices();
            // Filter for English voices, often higher quality voices are not local.
            const englishVoices = availableVoices.filter(voice => voice.lang.startsWith('en'));
            setVoices(englishVoices);
        };

        populateVoiceList();
        if (window.speechSynthesis.onvoiceschanged !== undefined) {
            window.speechSynthesis.onvoiceschanged = populateVoiceList;
        }
    }, []);

    // Load settings from local storage on initial render
    useEffect(() => {
        try {
            const storedSettings = localStorage.getItem('aiTalkingHeadSettings');
            if (storedSettings) {
                const parsedSettings: Partial<Settings> = JSON.parse(storedSettings);
                // Ensure geminiApiKey is not persisted from older versions
                delete (parsedSettings as any).geminiApiKey;

                const newSettings: Settings = {
                    apiProvider: parsedSettings.apiProvider || 'gemini',
                    geminiModel: parsedSettings.geminiModel || GEMINI_MODELS[0],
                    openRouterApiKey: parsedSettings.openRouterApiKey || '',
                    openRouterModel: parsedSettings.openRouterModel || 'google/gemini-flash-1.5',
                    speechVoiceURI: parsedSettings.speechVoiceURI || null,
                };
                
                setSettings(newSettings);
                setTempSettings(newSettings);
            }
        } catch (error) {
            console.error("Failed to load settings from localStorage:", error);
        }
    }, []);

    // Initialize Speech Recognition
    useEffect(() => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn("Speech Recognition API not supported in this browser.");
            return;
        }
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onresult = (event: any) => {
            const transcript = event.results[event.results.length - 1][0].transcript.trim();
            if (transcript) {
                handleSend(transcript);
            }
        };
        recognition.onend = () => setIsListening(false);
        recognition.onerror = (event: any) => {
            console.error("Speech recognition error:", event.error);
            setIsListening(false);
        };
        recognitionRef.current = recognition;
    }, []);


    // Fetch OpenRouter models when settings modal is opened
    useEffect(() => {
        if (isSettingsOpen && openRouterModels.length === 0) {
            getOpenRouterModels().then(setOpenRouterModels);
        }
    }, [isSettingsOpen, openRouterModels.length]);


    // --- Callbacks & Handlers ---

    const handleModelLoad = useCallback((dictionary: MorphTargetDictionary) => {
        setIsModelLoaded(true);
        setMorphTargetDictionary(dictionary);
        console.log("Model loaded with morph targets:", dictionary);
    }, []);
    
    const handleLoadProgress = useCallback((progress: number) => {
        setLoadProgress(progress);
    }, []);

    const resetMorphTargets = useCallback(() => {
        sceneRef.current?.resetMorphTargets();
    }, []);

    const speakAndAnimate = useCallback((text: string) => {
        if (!window.speechSynthesis || !sceneRef.current) return;
        const utterance = new SpeechSynthesisUtterance(text);
        
        // FIX: Get the latest voice list directly from the browser API to avoid stale state
        // that can occur with the Speech Synthesis API's asynchronous voice loading.
        const availableVoices = window.speechSynthesis.getVoices();
        if (settings.speechVoiceURI && availableVoices.length > 0) {
            const selectedVoice = availableVoices.find(voice => voice.voiceURI === settings.speechVoiceURI);
            if (selectedVoice) {
                utterance.voice = selectedVoice;
            } else {
                 console.warn(`Could not find selected voice URI: ${settings.speechVoiceURI}`);
            }
        }

        resetMorphTargets();
        
        let mouthMorphTargetName: string | null = null;
        if (morphTargetDictionary) {
            // Prioritized list of common mouth-open morph target names
            const possibleNames = ['mouthOpen', 'jawOpen', 'MouthOpen', 'JawOpen', 'vrc.v_oh', 'viseme_O'];
            for (const name of possibleNames) {
                if (name in morphTargetDictionary) {
                    mouthMorphTargetName = name;
                    break;
                }
            }
            // If no common name is found, fall back to a broader search
            if (!mouthMorphTargetName) {
                const allKeys = Object.keys(morphTargetDictionary);
                mouthMorphTargetName = allKeys.find(key => 
                    key.toLowerCase().includes('mouth') || 
                    key.toLowerCase().includes('jaw') ||
                    key.toLowerCase().includes('open')
                ) || null;
                if(mouthMorphTargetName) {
                  console.log(`Found fallback morph target for mouth: ${mouthMorphTargetName}`);
                } else {
                  console.warn("Could not find a suitable morph target for mouth animation.");
                }
            }
        }


        utterance.onboundary = (event) => {
            if (event.name === 'word' && mouthMorphTargetName) {
                sceneRef.current?.setMorphTargetInfluence(mouthMorphTargetName, 1.0);
                setTimeout(() => {
                    sceneRef.current?.setMorphTargetInfluence(mouthMorphTargetName, 0);
                }, 150);
            }
        };
        utterance.onend = () => resetMorphTargets();
        
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
    }, [resetMorphTargets, settings.speechVoiceURI, morphTargetDictionary]);

    const handleSend = async (message: string) => {
        if (settings.apiProvider === 'openrouter' && !settings.openRouterApiKey) {
            alert("OpenRouter API key not set. Please add your key in the settings.");
            setIsSettingsOpen(true);
            return;
        }


        setIsLoading(true);
        try {
            let responseText = '';
            if (settings.apiProvider === 'gemini') {
                responseText = await getGeminiAIResponse(message, settings.geminiModel);
            } else {
                responseText = await getOpenRouterResponse(message, settings.openRouterApiKey, settings.openRouterModel);
            }
            speakAndAnimate(responseText);
        } catch (error) {
            console.error("Failed to get AI response:", error);
            alert(`Sorry, there was an error: ${error instanceof Error ? error.message : "Unknown error"}`);
        } finally {
            setIsLoading(false);
        }
    };
    
    const toggleListening = () => {
        if (!recognitionRef.current) {
            alert("Speech recognition is not supported by your browser.");
            return;
        }
        if (isListening) {
            recognitionRef.current.stop();
        } else {
            recognitionRef.current.start();
            setIsListening(true);
        }
    };
    
    const handleSaveSettings = () => {
        setSettings(tempSettings);
        try {
            const { ...settingsToSave } = tempSettings;
            localStorage.setItem('aiTalkingHeadSettings', JSON.stringify(settingsToSave));
        } catch (error) {
            console.error("Failed to save settings to localStorage:", error);
        }
        setIsSettingsOpen(false);
    };

    return (
        <div className="relative w-screen h-screen overflow-hidden bg-gray-800">
            <ThreeScene ref={sceneRef} onModelLoad={handleModelLoad} onLoadProgress={handleLoadProgress} />
            
            {!isModelLoaded && (
                <div className="absolute inset-0 z-20 flex items-center justify-center bg-black bg-opacity-50">
                    <div className="text-white text-2xl font-semibold">Loading 3D Model... {loadProgress > 0 && `${loadProgress}%`}</div>
                </div>
            )}
            
            {isSettingsOpen && (
                 <div className="absolute inset-0 z-30 flex items-center justify-center bg-black bg-opacity-70" onClick={() => setIsSettingsOpen(false)}>
                    <div className="bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md text-white border border-gray-700" onClick={(e) => e.stopPropagation()}>
                        <h2 className="text-2xl font-bold mb-6">Settings</h2>
                        
                        <div className="space-y-6">
                             {/* Voice Selection */}
                            <div>
                                <label htmlFor="voice-select" className="block mb-2 font-semibold">Voice Selection</label>
                                <select
                                    id="voice-select"
                                    value={tempSettings.speechVoiceURI || ''}
                                    onChange={(e) => setTempSettings({ ...tempSettings, speechVoiceURI: e.target.value })}
                                    className="w-full p-2 bg-gray-700 rounded border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    disabled={voices.length === 0}
                                >
                                    <option value="">Browser Default</option>
                                    {voices.map(voice => (
                                        <option key={voice.voiceURI} value={voice.voiceURI}>
                                            {`${voice.name} (${voice.lang})`}
                                        </option>
                                    ))}
                                </select>
                                {voices.length === 0 && <p className="text-xs text-gray-400 mt-1">Loading voices...</p>}
                            </div>


                            {/* API Provider */}
                            <div>
                                <label className="block mb-2 font-semibold">API Provider</label>
                                <div className="flex gap-4 p-1 bg-gray-700 rounded-md">
                                    <button onClick={() => setTempSettings({...tempSettings, apiProvider: 'gemini'})} className={`flex-1 py-1 rounded ${tempSettings.apiProvider === 'gemini' ? 'bg-blue-600' : 'hover:bg-gray-600'}`}>Gemini</button>
                                    <button onClick={() => setTempSettings({...tempSettings, apiProvider: 'openrouter'})} className={`flex-1 py-1 rounded ${tempSettings.apiProvider === 'openrouter' ? 'bg-blue-600' : 'hover:bg-gray-600'}`}>OpenRouter</button>
                                </div>
                            </div>

                            {tempSettings.apiProvider === 'gemini' ? (
                                <>
                                    <div>
                                        <label htmlFor="gemini-model" className="block mb-2 font-semibold">Gemini Model</label>
                                        <select
                                            id="gemini-model"
                                            value={tempSettings.geminiModel}
                                            onChange={(e) => setTempSettings({ ...tempSettings, geminiModel: e.target.value })}
                                            className="w-full p-2 bg-gray-700 rounded border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        >
                                            {GEMINI_MODELS.map(model => <option key={model} value={model}>{model}</option>)}
                                        </select>
                                    </div>
                                    <div className="p-3 bg-gray-900 rounded-md border border-gray-600">
                                    <p className="text-sm text-gray-300">The Google Gemini API key is configured securely on the server.</p>
                                </div>
                                </>
                            ) : (
                                <>
                                    <div>
                                        <label htmlFor="openrouter-key" className="block mb-2 font-semibold">OpenRouter API Key</label>
                                        <input id="openrouter-key" type="password" value={tempSettings.openRouterApiKey} onChange={(e) => setTempSettings({...tempSettings, openRouterApiKey: e.target.value})} className="w-full p-2 bg-gray-700 rounded border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
                                    </div>
                                    <div>
                                        <label htmlFor="openrouter-model" className="block mb-2 font-semibold">OpenRouter Model (Free models listed)</label>
                                        <input list="openrouter-models-list" id="openrouter-model" value={tempSettings.openRouterModel} onChange={(e) => setTempSettings({...tempSettings, openRouterModel: e.target.value})} className="w-full p-2 bg-gray-700 rounded border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
                                        <datalist id="openrouter-models-list">
                                            {openRouterModels.map(model => <option key={model.id} value={model.id}>{model.name}</option>)}
                                        </datalist>
                                    </div>
                                </>
                            )}
                        </div>
                        
                        <div className="flex justify-end gap-4 mt-8">
                            <button onClick={() => { setIsSettingsOpen(false); setTempSettings(settings); }} className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg transition-colors">Cancel</button>
                            <button onClick={handleSaveSettings} className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors font-semibold">Save</button>
                        </div>
                    </div>
                </div>
            )}
            
            <div className="absolute bottom-0 left-0 right-0 z-10 p-4">
                <ChatUI 
                    onSend={handleSend} 
                    isLoading={isLoading || !isModelLoaded} 
                    onMicClick={toggleListening}
                    isListening={isListening}
                    onSettingsClick={() => setIsSettingsOpen(true)}
                />
            </div>
        </div>
    );
};

export default App;
