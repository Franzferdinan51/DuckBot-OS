import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAI } from '../../contexts/AIContext';
import { useAuth } from '../../contexts/AuthContext';
import toast from 'react-hot-toast';

const Avatar3D = ({ onClose }) => {
  // State management
  const [isLoading, setIsLoading] = useState(false);
  const [isModelLoaded, setIsModelLoaded] = useState(false);
  const [loadProgress, setLoadProgress] = useState(0);
  const [morphTargetDictionary, setMorphTargetDictionary] = useState(null);
  const [modelUrl, setModelUrl] = useState('/duckbot-os-static/Blender.glb');
  
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [settings, setSettings] = useState({
    apiProvider: 'duckbot',
    speechVoiceURI: null,
  });
  const [tempSettings, setTempSettings] = useState(settings);
  const [voices, setVoices] = useState([]);
  
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);
  const sceneRef = useRef(null);
  const canvasRef = useRef(null);
  const threeSceneRef = useRef(null);
  
  const { apiCall } = useAuth();
  const { sendMessage, isThinking } = useAI();

  // Initialize Three.js scene
  useEffect(() => {
    let scene, camera, renderer, mixer, model;
    let animationId;

    const initThreeJS = async () => {
      // Dynamically import Three.js modules
      const THREE = await import('https://unpkg.com/three@0.165.0/build/three.module.js');
      const { GLTFLoader } = await import('https://unpkg.com/three@0.165.0/examples/jsm/loaders/GLTFLoader.js');

      if (!canvasRef.current) return;

      // Scene setup
      scene = new THREE.Scene();
      scene.background = new THREE.Color(0x1e293b);

      camera = new THREE.PerspectiveCamera(75, canvasRef.current.offsetWidth / canvasRef.current.offsetHeight, 0.1, 1000);
      camera.position.set(0, 1.6, 3);

      renderer = new THREE.WebGLRenderer({ 
        canvas: canvasRef.current,
        antialias: true,
        alpha: true 
      });
      renderer.setSize(canvasRef.current.offsetWidth, canvasRef.current.offsetHeight);
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;

      // Lighting
      const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
      scene.add(ambientLight);

      const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
      directionalLight.position.set(5, 5, 5);
      directionalLight.castShadow = true;
      scene.add(directionalLight);

      // Load 3D model
      const loader = new GLTFLoader();
      
      try {
        const gltf = await new Promise((resolve, reject) => {
          loader.load(
            modelUrl,
            resolve,
            (progress) => {
              const progressPercentage = Math.round((progress.loaded / progress.total) * 100);
              setLoadProgress(progressPercentage);
            },
            reject
          );
        });

        model = gltf.scene;
        scene.add(model);
        
        // Extract morph targets
        const morphTargets = {};
        model.traverse((child) => {
          if (child.isMesh && child.morphTargetDictionary) {
            Object.assign(morphTargets, child.morphTargetDictionary);
          }
        });
        
        setMorphTargetDictionary(morphTargets);
        console.log('Model loaded with morph targets:', morphTargets);

        // Setup animation mixer if animations exist
        if (gltf.animations.length > 0) {
          mixer = new THREE.AnimationMixer(model);
          // Play idle animation if available
          const idleAction = mixer.clipAction(gltf.animations[0]);
          idleAction.play();
        }

        setIsModelLoaded(true);
        setLoadProgress(100);
      } catch (error) {
        console.error('Model loading failed:', error);
        toast.error('Failed to load 3D model');
      }

      // Animation loop
      const animate = () => {
        animationId = requestAnimationFrame(animate);
        
        if (mixer) {
          mixer.update(0.016); // ~60fps
        }
        
        renderer.render(scene, camera);
      };
      animate();

      // Store scene reference for morph target control
      threeSceneRef.current = { scene, model, mixer };
    };

    initThreeJS();

    // Handle window resize
    const handleResize = () => {
      if (!canvasRef.current || !camera || !renderer) return;
      
      camera.aspect = canvasRef.current.offsetWidth / canvasRef.current.offsetHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(canvasRef.current.offsetWidth, canvasRef.current.offsetHeight);
    };
    
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
      if (renderer) {
        renderer.dispose();
      }
    };
  }, [modelUrl]);

  // Initialize voices
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

  // Initialize speech recognition
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
    
    recognition.onresult = (event) => {
      const transcript = event.results[event.results.length - 1][0].transcript.trim();
      if (transcript) {
        handleSend(transcript);
      }
    };
    
    recognition.onend = () => setIsListening(false);
    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
      toast.error(`Speech recognition error: ${event.error}`);
    };
    
    recognitionRef.current = recognition;
  }, []);

  // Morph target control functions
  const setMorphTargetInfluence = useCallback((name, value) => {
    if (!threeSceneRef.current?.model || !morphTargetDictionary) return;
    
    threeSceneRef.current.model.traverse((child) => {
      if (child.isMesh && child.morphTargetDictionary && name in child.morphTargetDictionary) {
        const index = child.morphTargetDictionary[name];
        child.morphTargetInfluences[index] = value;
      }
    });
  }, [morphTargetDictionary]);

  const resetMorphTargets = useCallback(() => {
    if (!threeSceneRef.current?.model || !morphTargetDictionary) return;
    
    Object.keys(morphTargetDictionary).forEach(name => {
      setMorphTargetInfluence(name, 0);
    });
  }, [morphTargetDictionary, setMorphTargetInfluence]);

  // Speech and animation function
  const speakAndAnimate = useCallback((text) => {
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

    resetMorphTargets();
    
    // Find suitable morph target for mouth animation
    let mouthMorphTargetName = null;
    if (morphTargetDictionary) {
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

    // Animate mouth during speech
    utterance.onboundary = (event) => {
      if (event.name === 'word' && mouthMorphTargetName) {
        setMorphTargetInfluence(mouthMorphTargetName, 1.0);
        setTimeout(() => {
          setMorphTargetInfluence(mouthMorphTargetName, 0);
        }, 150);
      }
    };

    utterance.onend = () => resetMorphTargets();

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }, [settings.speechVoiceURI, morphTargetDictionary, resetMorphTargets, setMorphTargetInfluence]);

  // Handle chat messages
  const handleSend = async (message) => {
    if (!message.trim() || isThinking) return;

    setIsLoading(true);
    try {
      // Use DuckBot backend API
      const response = await apiCall('/api/duckbot-os/chat', {
        method: 'POST',
        body: new URLSearchParams({
          message: message,
          model: 'auto',
          provider: 'auto'
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          // Animate avatar and speak
          speakAndAnimate(data.response);
          toast.success('Response generated');
        } else {
          toast.error(data.error || 'Unknown error');
        }
      } else {
        toast.error('Failed to get response from DuckBot');
      }
    } catch (error) {
      console.error("Chat error:", error);
      toast.error(`Chat error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleListening = () => {
    if (!recognitionRef.current) {
      toast.error("Speech recognition not supported");
      return;
    }
    
    if (isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
      setIsListening(true);
      toast.success("Listening...");
    }
  };

  const handleSaveSettings = () => {
    setSettings(tempSettings);
    try {
      localStorage.setItem('duckbotAvatarSettings', JSON.stringify(tempSettings));
    } catch (error) {
      console.error("Failed to save settings:", error);
    }
    setIsSettingsOpen(false);
    toast.success("Settings saved");
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setModelUrl(url);
      setIsModelLoaded(false);
      setLoadProgress(0);
      toast.success("Loading new model...");
    }
  };

  return (
    <div className="avatar-3d h-full flex flex-col bg-slate-900">
      {/* Header */}
      <div className="flex-shrink-0 bg-slate-800 p-4 border-b border-slate-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="text-2xl">🦆</div>
            <div>
              <h2 className="text-lg font-semibold text-white">DuckBot 3D Avatar</h2>
              <div className="text-xs text-slate-400">
                Voice-enabled AI companion with Windows device voice fallback
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="btn-secondary text-xs"
            >
              ⚙️ Settings
            </button>
            <button
              onClick={onClose}
              className="btn-secondary text-xs text-red-400"
            >
              ✕ Close
            </button>
          </div>
        </div>
      </div>

      {/* 3D Avatar Area */}
      <div className="flex-1 relative bg-gradient-to-b from-slate-800 to-slate-900">
        <canvas
          ref={canvasRef}
          className="w-full h-full"
          style={{ display: isModelLoaded ? 'block' : 'none' }}
        />
        
        {!isModelLoaded && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="text-white text-2xl font-semibold mb-4">
                Loading 3D Avatar...
              </div>
              <div className="w-64 bg-slate-700 rounded-full h-2 mb-2">
                <div 
                  className="bg-green-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${loadProgress}%` }}
                />
              </div>
              <div className="text-slate-400 text-sm">
                {loadProgress > 0 && `${loadProgress}%`}
              </div>
            </div>
          </div>
        )}

        {/* Floating Chat Input */}
        <div className="absolute bottom-4 left-4 right-4">
          <div className="bg-slate-800/90 backdrop-blur-sm rounded-lg p-4 border border-slate-600">
            <div className="flex space-x-2">
              <input
                type="text"
                placeholder="Talk to your AI companion..."
                className="flex-1 bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleSend(e.target.value);
                    e.target.value = '';
                  }
                }}
                disabled={isLoading}
              />
              <button
                onClick={toggleListening}
                className={`px-4 py-2 rounded transition-colors ${
                  isListening 
                    ? 'bg-red-500 hover:bg-red-600 text-white' 
                    : 'bg-green-500 hover:bg-green-600 text-white'
                }`}
                disabled={isLoading}
              >
                {isListening ? '🛑 Stop' : '🎤 Listen'}
              </button>
            </div>
            
            {(isLoading || isThinking) && (
              <div className="mt-2 text-sm text-green-400 flex items-center space-x-2">
                <div className="flex space-x-1">
                  {[...Array(3)].map((_, i) => (
                    <motion.div
                      key={i}
                      className="w-2 h-2 bg-green-400 rounded-full"
                      animate={{
                        scale: [1, 1.5, 1],
                        opacity: [0.5, 1, 0.5],
                      }}
                      transition={{
                        duration: 1,
                        repeat: Infinity,
                        delay: i * 0.2,
                      }}
                    />
                  ))}
                </div>
                <span>DuckBot is thinking...</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Settings Modal */}
      <AnimatePresence>
        {isSettingsOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={() => setIsSettingsOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="bg-slate-800 rounded-lg shadow-xl p-6 w-full max-w-md text-white border border-slate-700"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="text-2xl font-bold mb-6">Avatar Settings</h2>
              
              <div className="space-y-6">
                <div>
                  <label htmlFor="model-file" className="block mb-2 font-semibold">Load Custom Model</label>
                  <input 
                    id="model-file" 
                    type="file" 
                    accept=".glb,.gltf,.vrm,.fbx" 
                    onChange={handleFileChange} 
                    className="w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
                  />
                  <p className="text-xs text-gray-400 mt-2">Supported: GLB, GLTF, VRM, FBX</p>
                </div>

                <div>
                  <label htmlFor="voice-select" className="block mb-2 font-semibold">Voice Selection</label>
                  <select
                    id="voice-select"
                    value={tempSettings.speechVoiceURI || ''}
                    onChange={(e) => setTempSettings({ ...tempSettings, speechVoiceURI: e.target.value })}
                    className="w-full p-2 bg-slate-700 rounded border border-slate-600 focus:outline-none focus:ring-2 focus:ring-green-500"
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

                <div className="p-4 bg-gradient-to-r from-green-900 to-green-800 rounded-md border border-green-600">
                  <h3 className="text-lg font-bold text-green-200 mb-2">🦆 DuckBot Integration</h3>
                  <p className="text-sm text-green-100 mb-2">Connected to DuckBot Enhanced with:</p>
                  <ul className="text-xs text-green-200 space-y-1">
                    <li>• Intelligent AI routing (LM Studio → OpenRouter → Qwen)</li>
                    <li>• Windows device voices (hardware accelerated)</li>
                    <li>• 3D facial animation with morph targets</li>
                    <li>• Speech recognition and voice commands</li>
                  </ul>
                </div>
              </div>
              
              <div className="flex justify-end gap-4 mt-8">
                <button 
                  onClick={() => { setIsSettingsOpen(false); setTempSettings(settings); }} 
                  className="px-4 py-2 bg-slate-600 hover:bg-slate-500 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button 
                  onClick={handleSaveSettings} 
                  className="px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg transition-colors font-semibold"
                >
                  Save
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Avatar3D;