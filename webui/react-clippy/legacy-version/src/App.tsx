import React, { useState, useCallback, useRef, useEffect } from 'react';
import { ThreeScene } from './components/ThreeScene';
import { ChatUI } from './components/ChatUI';
import { AIService } from './services/duckbotService';
import type { MorphTargetDictionary, SceneHandle, Settings, ApiProvider } from './types';

// Electron IPC types
declare global {
    interface Window {
        electronAPI?: {
            minimizeToTray: () => void;
            toggleAlwaysOnTop: (alwaysOnTop: boolean) => void;
            getDuckBotStatus: () => Promise<{ webui: boolean; clippy: boolean }>;
            startDuckBot: () => void;
            stopDuckBot: () => void;
        };
        SpeechRecognition?: any;
        webkitSpeechRecognition?: any;
    }
}

const App: React.FC = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [isModelLoaded, setIsModelLoaded] = useState(false);
    const [loadProgress, setLoadProgress] = useState(0);
    const [morphTargetDictionary, setMorphTargetDictionary] = useState<MorphTargetDictionary | null>(null);
    const [connectionStatus, setConnectionStatus] = useState<'connected' | 'connecting' | 'disconnected'>('disconnected');

    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [settings, setSettings] = useState<Settings>({
        apiProvider: 'duckbot',
        duckbotUrl: 'http://localhost:8787',
        duckbotToken: null,
        lmStudioUrl: 'http://localhost:1234',
        lmStudioModel: '',
        openRouterApiKey: '',
        openRouterModel: 'google/gemma-2-9b-it:free',
        speechVoiceURI: null,
        useVibeVoice: true,
    });
    const [tempSettings, setTempSettings] = useState<Settings>(settings);
    const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
    const [availableModels, setAvailableModels] = useState<string[]>([]);
    const [interactionCount, setInteractionCount] = useState(0);

    const [isListening, setIsListening] = useState(false);
    const recognitionRef = useRef<any>(null);
    const sceneRef = useRef<SceneHandle>(null);
    const aiServiceRef = useRef(new AIService());

    // Load settings from localStorage
    useEffect(() => {
        try {
            const storedSettings = localStorage.getItem('duckbotClippySettings');
            if (storedSettings) {
                const parsedSettings: Partial<Settings> = JSON.parse(storedSettings);
                const newSettings: Settings = {
                    apiProvider: parsedSettings.apiProvider || 'duckbot',
                    duckbotUrl: parsedSettings.duckbotUrl || 'http://localhost:8787',
                    duckbotToken: parsedSettings.duckbotToken || null,
                    lmStudioUrl: parsedSettings.lmStudioUrl || 'http://localhost:1234',
                    lmStudioModel: parsedSettings.lmStudioModel || '',
                    openRouterApiKey: parsedSettings.openRouterApiKey || '',
                    openRouterModel: parsedSettings.openRouterModel || 'google/gemma-2-9b-it:free',
                    speechVoiceURI: parsedSettings.speechVoiceURI || null,
                    useVibeVoice: parsedSettings.useVibeVoice !== undefined ? parsedSettings.useVibeVoice : true,
                };
                
                setSettings(newSettings);
                setTempSettings(newSettings);
            }
        } catch (error) {
            console.error("Failed to load settings from localStorage:", error);
        }
    }, []);

    // Initialize speech synthesis voices
    useEffect(() => {
        const populateVoiceList = () => {
            const availableVoices = window.speechSynthesis.getVoices();
            const englishVoices = availableVoices.filter(voice => voice.lang.startsWith('en'));
            setVoices(englishVoices);
        };

        populateVoiceList();
        if (window.speechSynthesis.onvoiceschanged !== undefined) {
            window.speechSynthesis.onvoiceschanged = populateVoiceList;
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

    // Test AI connection on startup and settings change
    useEffect(() => {
        const testConnection = async () => {
            setConnectionStatus('connecting');
            
            try {
                const service = aiServiceRef.current;
                
                // Configure services based on current settings
                if (settings.apiProvider === 'duckbot') {
                    service.getDuckBotService().setBaseUrl(settings.duckbotUrl);
                    service.getDuckBotService().setToken(settings.duckbotToken);
                    const isConnected = await service.getDuckBotService().testConnection();
                    setConnectionStatus(isConnected ? 'connected' : 'disconnected');
                    
                    if (isConnected) {
                        // Load available models
                        const models = await service.getDuckBotService().getAvailableModels();
                        setAvailableModels(models);
                    }
                } else if (settings.apiProvider === 'lmstudio') {
                    service.getLMStudioService().setBaseUrl(settings.lmStudioUrl);
                    const isConnected = await service.getLMStudioService().testConnection();
                    setConnectionStatus(isConnected ? 'connected' : 'disconnected');
                    
                    if (isConnected) {
                        const models = await service.getLMStudioService().getAvailableModels();
                        setAvailableModels(models.map(m => m.id));
                    }
                } else if (settings.apiProvider === 'openrouter') {
                    service.getOpenRouterService().setApiKey(settings.openRouterApiKey);
                    const isConnected = await service.getOpenRouterService().testConnection();
                    setConnectionStatus(isConnected ? 'connected' : 'disconnected');
                }
            } catch (error) {
                console.error('Connection test failed:', error);
                setConnectionStatus('disconnected');
            }
        };

        testConnection();
    }, [settings.apiProvider, settings.duckbotUrl, settings.duckbotToken, settings.lmStudioUrl, settings.openRouterApiKey]);

    const handleModelLoad = useCallback((dictionary: MorphTargetDictionary) => {
        setIsModelLoaded(true);
        setMorphTargetDictionary(dictionary);
        console.log("DuckBot Clippy: 3D model loaded with morph targets:", dictionary);
    }, []);
    
    const handleLoadProgress = useCallback((progress: number) => {
        setLoadProgress(progress);
    }, []);

    const resetMorphTargets = useCallback(() => {
        sceneRef.current?.resetMorphTargets();
    }, []);

    const speakAndAnimate = useCallback(async (text: string, useVibeVoice: boolean = false) => {
        if (!sceneRef.current) return;

        resetMorphTargets();
        
        let mouthMorphTargetName: string | null = null;
        if (morphTargetDictionary) {
            // Find mouth animation morph target
            const possibleNames = ['mouthOpen', 'jawOpen', 'MouthOpen', 'JawOpen', 'vrc.v_oh', 'viseme_O'];
            for (const name of possibleNames) {
                if (name in morphTargetDictionary) {
                    mouthMorphTargetName = name;
                    break;
                }
            }
            
            if (!mouthMorphTargetName) {
                const allKeys = Object.keys(morphTargetDictionary);
                mouthMorphTargetName = allKeys.find(key => 
                    key.toLowerCase().includes('mouth') || 
                    key.toLowerCase().includes('jaw') ||
                    key.toLowerCase().includes('open')
                ) || null;
            }
        }

        // Try VibeVoice TTS if enabled and using DuckBot
        if (useVibeVoice && settings.useVibeVoice && settings.apiProvider === 'duckbot' && connectionStatus === 'connected') {
            try {
                const service = aiServiceRef.current.getDuckBotService();
                const audioUrl = await service.generateVoiceScript(text, 'en-alice');
                
                if (audioUrl && audioUrl !== text) { // Check if we got an audio URL back
                    // Play audio and animate
                    const audio = new Audio(audioUrl);
                    
                    // Animate mouth during playback
                    const animatemouth = () => {
                        if (mouthMorphTargetName && sceneRef.current) {
                            sceneRef.current.setMorphTargetInfluence(mouthMorphTargetName, Math.random() * 0.8 + 0.2);
                        }
                    };
                    
                    const animationInterval = setInterval(animatemouth, 100);
                    
                    audio.onended = () => {
                        clearInterval(animationInterval);
                        resetMorphTargets();
                    };
                    
                    audio.onerror = () => {
                        clearInterval(animationInterval);
                        resetMorphTargets();
                        // Fallback to browser TTS
                        fallbackToSpeechSynthesis();
                    };
                    
                    audio.play();
                    return; // Exit early if VibeVoice worked
                }
            } catch (error) {
                console.log('VibeVoice TTS not available, falling back to browser TTS');
            }
        }
        
        // Fallback to browser speech synthesis
        function fallbackToSpeechSynthesis() {
            if (!window.speechSynthesis) return;
            
            const utterance = new SpeechSynthesisUtterance(text);
            
            // Apply selected voice
            const availableVoices = window.speechSynthesis.getVoices();
            if (settings.speechVoiceURI && availableVoices.length > 0) {
                const selectedVoice = availableVoices.find(voice => voice.voiceURI === settings.speechVoiceURI);
                if (selectedVoice) {
                    utterance.voice = selectedVoice;
                }
            }

            // Animate mouth during speech
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
        }
        
        fallbackToSpeechSynthesis();
    }, [resetMorphTargets, settings.speechVoiceURI, morphTargetDictionary, settings.apiProvider, connectionStatus]);

    const handleSend = async (message: string) => {
        if (connectionStatus !== 'connected') {
            console.error('Not connected to AI service');
            return;
        }

        setIsLoading(true);
        try {
            const service = aiServiceRef.current;
            let responseText = '';

            // Check if message is asking for special DuckBot features
            const imageGenerationKeywords = ['generate image', 'create image', 'draw', 'image of', 'picture of', 'generate an image'];
            const costKeywords = ['cost summary', 'costs', 'spending', 'budget', 'usage costs'];
            const servicesKeywords = ['services status', 'service status', 'services', 'system status'];
            const ragKeywords = ['search knowledge', 'search documents', 'find information', 'knowledge base'];
            const workflowKeywords = ['n8n workflows', 'workflows', 'automation'];
            const queueKeywords = ['queue status', 'queue', 'task queue'];
            
            const isImageRequest = imageGenerationKeywords.some(keyword => 
                message.toLowerCase().includes(keyword)
            );
            const isCostRequest = costKeywords.some(keyword => 
                message.toLowerCase().includes(keyword)
            );
            const isServicesRequest = servicesKeywords.some(keyword => 
                message.toLowerCase().includes(keyword)
            );
            const isRagRequest = ragKeywords.some(keyword => 
                message.toLowerCase().includes(keyword)
            );
            const isWorkflowRequest = workflowKeywords.some(keyword => 
                message.toLowerCase().includes(keyword)
            );
            const isQueueRequest = queueKeywords.some(keyword => 
                message.toLowerCase().includes(keyword)
            );

            if (settings.apiProvider === 'duckbot') {
                if (isImageRequest) {
                    try {
                        // Use ComfyUI integration for image generation
                        const imageResult = await service.getDuckBotService().generateImage(message, 'auto');
                        
                        if (imageResult.success && imageResult.image_url) {
                            // Show image in popup or preview
                            const imagePreview = document.createElement('div');
                            imagePreview.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80';
                            imagePreview.innerHTML = `
                                <div class="max-w-4xl max-h-4xl p-4 bg-gray-800 rounded-lg">
                                    <div class="flex justify-between items-center mb-4">
                                        <h3 class="text-white text-lg font-semibold">Generated Image</h3>
                                        <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                                                class="text-gray-400 hover:text-white">
                                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                            </svg>
                                        </button>
                                    </div>
                                    <img src="${imageResult.image_url}" alt="Generated image" 
                                         class="max-w-full max-h-96 object-contain rounded" />
                                    <p class="text-gray-300 text-sm mt-2">${message}</p>
                                </div>
                            `;
                            document.body.appendChild(imagePreview);
                            
                            responseText = `I've generated an image for you! The image should appear in a popup window. ${imageResult.message || 'Image generation completed successfully.'}`;
                        } else {
                            responseText = `I tried to generate an image, but encountered an issue: ${imageResult.error || 'Unknown error'}. Let me try a different approach or you can ask me something else.`;
                        }
                    } catch (error) {
                        console.log('Image generation failed, falling back to text response');
                        responseText = await service.chat(message, 'duckbot', 'auto');
                    }
                } else if (isCostRequest) {
                    try {
                        const costSummary = await service.getDuckBotService().getCostSummary(7);
                        if (costSummary.error) {
                            responseText = `I couldn't retrieve your cost summary: ${costSummary.error}`;
                        } else {
                            responseText = `Here's your cost summary for the last 7 days: Total spent: $${costSummary.total || 0}, Queries: ${costSummary.query_count || 0}, Average per query: $${costSummary.average_cost || 0}. ${costSummary.details || ''}`;
                        }
                    } catch (error) {
                        responseText = `I couldn't retrieve your cost information. ${error instanceof Error ? error.message : 'Unknown error'}`;
                    }
                } else if (isServicesRequest) {
                    try {
                        const services = await service.getDuckBotService().getServices();
                        if (services.error) {
                            responseText = `I couldn't check services status: ${services.error}`;
                        } else {
                            const servicesList = services.services || [];
                            if (servicesList.length > 0) {
                                const statusReport = servicesList.map(svc => `${svc.name}: ${svc.status}`).join(', ');
                                responseText = `Service Status: ${statusReport}. All systems are ${servicesList.every(svc => svc.status === 'running') ? 'operational' : 'mixed'}.`;
                            } else {
                                responseText = 'No services information available.';
                            }
                        }
                    } catch (error) {
                        responseText = `I couldn't check services status. ${error instanceof Error ? error.message : 'Unknown error'}`;
                    }
                } else if (isRagRequest) {
                    try {
                        const searchQuery = message.replace(/search knowledge|search documents|find information|knowledge base/gi, '').trim();
                        const ragResults = await service.getDuckBotService().searchRAG(searchQuery || message);
                        if (ragResults.error) {
                            responseText = `I couldn't search the knowledge base: ${ragResults.error}`;
                        } else {
                            const results = ragResults.results || [];
                            if (results.length > 0) {
                                responseText = `Found ${results.length} relevant documents: ${results.map(r => r.title || r.content?.substring(0, 100)).join(', ')}`;
                            } else {
                                responseText = `I searched the knowledge base but didn't find specific information about "${searchQuery || message}". Try a different search term.`;
                            }
                        }
                    } catch (error) {
                        responseText = `I couldn't search the knowledge base. ${error instanceof Error ? error.message : 'Unknown error'}`;
                    }
                } else if (isQueueRequest) {
                    try {
                        const queueStatus = await service.getDuckBotService().getQueueStatus();
                        if (queueStatus.error) {
                            responseText = `I couldn't check the queue status: ${queueStatus.error}`;
                        } else {
                            responseText = `Queue Status: ${queueStatus.queue_size || 0} items in queue. ${queueStatus.processing ? 'Currently processing tasks.' : 'Queue is idle.'}`;
                        }
                    } catch (error) {
                        responseText = `I couldn't check the queue status. ${error instanceof Error ? error.message : 'Unknown error'}`;
                    }
                } else if (isWorkflowRequest) {
                    responseText = `I can help with n8n workflows! The workflow automation system is available at http://localhost:5678. You can create, manage, and monitor automated workflows there. Would you like me to help you with a specific workflow task?`;
                } else {
                    // Normal text chat
                    responseText = await service.chat(message, 'duckbot', 'auto');
                }
            } else {
                // Other providers (LM Studio, OpenRouter) - basic chat only
                if (settings.apiProvider === 'lmstudio') {
                    responseText = await service.chat(message, 'lmstudio', settings.lmStudioModel);
                } else if (settings.apiProvider === 'openrouter') {
                    responseText = await service.chat(message, 'openrouter', settings.openRouterModel);
                }
            }

            // Add gamification - track interactions and provide motivational messages
            const newCount = interactionCount + 1;
            setInteractionCount(newCount);
            
            // Add motivational messages at milestones
            if (newCount % 10 === 0 && newCount > 0) {
                const milestoneMessages = [
                    "🎉 Great job! You've had " + newCount + " conversations with me!",
                    "🌟 You're getting good at this AI assistant thing!",
                    "🚀 " + newCount + " interactions and counting! Keep exploring!",
                    "💪 You're becoming a DuckBot power user!",
                ];
                const milestoneMessage = milestoneMessages[Math.floor(Math.random() * milestoneMessages.length)];
                responseText += " " + milestoneMessage;
            }
            
            speakAndAnimate(responseText, true); // Enable VibeVoice TTS
        } catch (error) {
            console.error("Failed to get AI response:", error);
            const errorMessage = `Sorry, there was an error: ${error instanceof Error ? error.message : "Unknown error"}`;
            speakAndAnimate(errorMessage);
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
            localStorage.setItem('duckbotClippySettings', JSON.stringify(tempSettings));
        } catch (error) {
            console.error("Failed to save settings to localStorage:", error);
        }
        setIsSettingsOpen(false);
    };

    const handleMinimizeToTray = () => {
        if (window.electronAPI?.minimizeToTray) {
            window.electronAPI.minimizeToTray();
        }
    };

    return (
        <div className="relative w-screen h-screen overflow-hidden bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
            {/* 3D Scene */}
            <ThreeScene ref={sceneRef} onModelLoad={handleModelLoad} onLoadProgress={handleLoadProgress} />
            
            {/* Loading overlay */}
            {!isModelLoaded && (
                <div className="absolute inset-0 z-20 flex items-center justify-center bg-black bg-opacity-75">
                    <div className="text-center">
                        <div className="text-white text-2xl font-semibold mb-2">
                            Loading DuckBot Clippy...
                        </div>
                        {loadProgress > 0 && (
                            <div className="text-teal-400 text-lg">
                                {loadProgress}%
                            </div>
                        )}
                        <div className="text-gray-400 text-sm mt-2">
                            Your 3D AI assistant is getting ready
                        </div>
                    </div>
                </div>
            )}
            
            {/* Settings Modal */}
            {isSettingsOpen && (
                <div className="absolute inset-0 z-30 flex items-center justify-center bg-black bg-opacity-80" onClick={() => setIsSettingsOpen(false)}>
                    <div className="bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md text-white border border-gray-700" onClick={(e) => e.stopPropagation()}>
                        <h2 className="text-2xl font-bold mb-6">DuckBot Clippy Settings</h2>
                        
                        <div className="space-y-6 max-h-96 overflow-y-auto">
                            {/* API Provider Selection */}
                            <div>
                                <label className="block mb-2 font-semibold">AI Provider</label>
                                <div className="grid grid-cols-3 gap-2">
                                    {(['duckbot', 'lmstudio', 'openrouter'] as ApiProvider[]).map(provider => (
                                        <button 
                                            key={provider}
                                            onClick={() => setTempSettings({...tempSettings, apiProvider: provider})} 
                                            className={`py-2 px-3 rounded text-sm font-medium transition-colors ${
                                                tempSettings.apiProvider === provider 
                                                    ? 'bg-teal-600 text-white' 
                                                    : 'bg-gray-700 hover:bg-gray-600'
                                            }`}
                                        >
                                            {provider === 'duckbot' ? 'DuckBot' : provider === 'lmstudio' ? 'LM Studio' : 'OpenRouter'}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Provider-specific settings */}
                            {tempSettings.apiProvider === 'duckbot' && (
                                <div className="space-y-4">
                                    <div>
                                        <label htmlFor="duckbot-url" className="block mb-2 font-semibold">DuckBot URL</label>
                                        <input 
                                            id="duckbot-url"
                                            type="text" 
                                            value={tempSettings.duckbotUrl} 
                                            onChange={(e) => setTempSettings({...tempSettings, duckbotUrl: e.target.value})} 
                                            className="w-full p-2 bg-gray-700 rounded border border-gray-600 focus:outline-none focus:ring-2 focus:ring-teal-500"
                                            placeholder="http://localhost:8787"
                                        />
                                    </div>
                                    <div className="p-3 bg-gray-900 rounded-md border border-gray-600">
                                        <p className="text-sm text-gray-300">
                                            Make sure DuckBot WebUI is running on the specified URL. The token will be automatically retrieved.
                                        </p>
                                    </div>
                                </div>
                            )}

                            {tempSettings.apiProvider === 'lmstudio' && (
                                <div className="space-y-4">
                                    <div>
                                        <label htmlFor="lmstudio-url" className="block mb-2 font-semibold">LM Studio URL</label>
                                        <input 
                                            id="lmstudio-url"
                                            type="text" 
                                            value={tempSettings.lmStudioUrl} 
                                            onChange={(e) => setTempSettings({...tempSettings, lmStudioUrl: e.target.value})} 
                                            className="w-full p-2 bg-gray-700 rounded border border-gray-600 focus:outline-none focus:ring-2 focus:ring-teal-500"
                                            placeholder="http://localhost:1234"
                                        />
                                    </div>
                                    <div className="p-3 bg-gray-900 rounded-md border border-gray-600">
                                        <p className="text-sm text-gray-300">
                                            Make sure LM Studio is running with local server enabled and at least one model loaded.
                                        </p>
                                    </div>
                                </div>
                            )}

                            {tempSettings.apiProvider === 'openrouter' && (
                                <div className="space-y-4">
                                    <div>
                                        <label htmlFor="openrouter-key" className="block mb-2 font-semibold">OpenRouter API Key</label>
                                        <input 
                                            id="openrouter-key"
                                            type="password" 
                                            value={tempSettings.openRouterApiKey} 
                                            onChange={(e) => setTempSettings({...tempSettings, openRouterApiKey: e.target.value})} 
                                            className="w-full p-2 bg-gray-700 rounded border border-gray-600 focus:outline-none focus:ring-2 focus:ring-teal-500"
                                        />
                                    </div>
                                    <div>
                                        <label htmlFor="openrouter-model" className="block mb-2 font-semibold">Model</label>
                                        <input 
                                            id="openrouter-model"
                                            type="text" 
                                            value={tempSettings.openRouterModel} 
                                            onChange={(e) => setTempSettings({...tempSettings, openRouterModel: e.target.value})} 
                                            className="w-full p-2 bg-gray-700 rounded border border-gray-600 focus:outline-none focus:ring-2 focus:ring-teal-500"
                                            placeholder="google/gemma-2-9b-it:free"
                                        />
                                    </div>
                                </div>
                            )}

                            {/* VibeVoice TTS Toggle */}
                            <div>
                                <label className="flex items-center mb-2 font-semibold">
                                    <input
                                        type="checkbox"
                                        checked={tempSettings.useVibeVoice}
                                        onChange={(e) => setTempSettings({ ...tempSettings, useVibeVoice: e.target.checked })}
                                        className="mr-2 text-teal-600 bg-gray-700 border-gray-600 rounded focus:ring-teal-500 focus:ring-2"
                                    />
                                    Use VibeVoice TTS (DuckBot)
                                </label>
                                <p className="text-xs text-gray-400">
                                    {tempSettings.useVibeVoice 
                                        ? "High-quality multi-speaker TTS via DuckBot's VibeVoice integration" 
                                        : "Using browser's built-in speech synthesis"}
                                </p>
                            </div>

                            {/* Voice Selection */}
                            <div>
                                <label htmlFor="voice-select" className="block mb-2 font-semibold">
                                    {tempSettings.useVibeVoice ? "Fallback Voice" : "Browser Voice Selection"}
                                </label>
                                <select
                                    id="voice-select"
                                    value={tempSettings.speechVoiceURI || ''}
                                    onChange={(e) => setTempSettings({ ...tempSettings, speechVoiceURI: e.target.value })}
                                    className="w-full p-2 bg-gray-700 rounded border border-gray-600 focus:outline-none focus:ring-2 focus:ring-teal-500"
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
                                {tempSettings.useVibeVoice && (
                                    <p className="text-xs text-gray-400 mt-1">
                                        This voice will be used if VibeVoice TTS is unavailable
                                    </p>
                                )}
                            </div>
                        </div>
                        
                        <div className="flex justify-end gap-4 mt-8">
                            <button onClick={() => { setIsSettingsOpen(false); setTempSettings(settings); }} className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg transition-colors">Cancel</button>
                            <button onClick={handleSaveSettings} className="px-4 py-2 bg-teal-600 hover:bg-teal-500 rounded-lg transition-colors font-semibold">Save</button>
                        </div>
                    </div>
                </div>
            )}
            
            {/* Chat Interface */}
            <div className="absolute bottom-4 left-4 right-4 z-10">
                <ChatUI 
                    onSend={handleSend} 
                    isLoading={isLoading || !isModelLoaded} 
                    onMicClick={toggleListening}
                    isListening={isListening}
                    onSettingsClick={() => setIsSettingsOpen(true)}
                    onMinimizeClick={window.electronAPI ? handleMinimizeToTray : undefined}
                    connectionStatus={connectionStatus}
                    currentProvider={settings.apiProvider}
                />
            </div>
        </div>
    );
};

export default App;