import React, { useRef, useEffect, forwardRef, useImperativeHandle } from 'react';
import * as THREE from 'three';
import { GLTFLoader, GLTF } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import type { MorphTargetDictionary, SceneHandle } from '../types';

interface ThreeSceneProps {
    onModelLoad: (dictionary: MorphTargetDictionary) => void;
    onLoadProgress: (progress: number) => void;
}

// Using the stable ThreeJS robot model for Clippy-like interaction
const MODEL_PATH = 'https://threejs.org/examples/models/gltf/RobotExpressive/RobotExpressive.glb';

export const ThreeScene = forwardRef<SceneHandle, ThreeSceneProps>(({ onModelLoad, onLoadProgress }, ref) => {
    const mountRef = useRef<HTMLDivElement>(null);
    const headMeshRef = useRef<THREE.Mesh | null>(null);
    const modelRef = useRef<THREE.Object3D | null>(null);
    const morphInfluencesRef = useRef<(number[] | undefined) | null>(null);

    useImperativeHandle(ref, () => ({
        setMorphTargetInfluence: (name: string, value: number) => {
            if (headMeshRef.current && headMeshRef.current.morphTargetDictionary && morphInfluencesRef.current) {
                const index = headMeshRef.current.morphTargetDictionary[name];
                if (index !== undefined) {
                    morphInfluencesRef.current[index] = value;
                }
            }
        },
        resetMorphTargets: () => {
            if (morphInfluencesRef.current) {
                for (let i = 0; i < morphInfluencesRef.current.length; i++) {
                    morphInfluencesRef.current[i] = 0;
                }
            }
        }
    }));

    useEffect(() => {
        if (!mountRef.current) return;

        const currentMount = mountRef.current;

        // Scene setup with DuckBot branding colors
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x1a202c); // Dark blue-gray background
        scene.fog = new THREE.Fog(0x1a202c, 4, 15);

        // Camera optimized for desktop assistant view - zoomed out more
        const camera = new THREE.PerspectiveCamera(40, currentMount.clientWidth / currentMount.clientHeight, 0.1, 1000);
        camera.position.set(0, 1.0, 6.5); // Zoomed out for better full robot view

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(currentMount.clientWidth, currentMount.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Limit for performance
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.2;
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        currentMount.appendChild(renderer.domElement);

        // Controls optimized for desktop companion
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.target = new THREE.Vector3(0, 0.8, 0); // Focus on center of character
        controls.enablePan = false; // Disable panning for cleaner UX
        controls.enableZoom = true;
        controls.minDistance = 4.0;
        controls.maxDistance = 10.0;
        controls.minPolarAngle = Math.PI * 0.2; // Limit vertical rotation
        controls.maxPolarAngle = Math.PI * 0.8;
        controls.dampingFactor = 0.08;
        controls.enableDamping = true;
        controls.autoRotate = true; // Enable auto-rotation for idle animation
        controls.autoRotateSpeed = 0.1; // Even slower rotation for less distraction
        
        // Enhanced lighting setup for better character visibility
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
        scene.add(ambientLight);

        // Key light - main illumination
        const keyLight = new THREE.DirectionalLight(0xffffff, 1.2);
        keyLight.position.set(3, 4, 2);
        keyLight.castShadow = true;
        keyLight.shadow.mapSize.width = 1024;
        keyLight.shadow.mapSize.height = 1024;
        scene.add(keyLight);

        // Fill light - soften shadows
        const fillLight = new THREE.DirectionalLight(0xccddff, 0.6);
        fillLight.position.set(-3, 2, 2);
        scene.add(fillLight);

        // Rim light - add depth with DuckBot accent color
        const rimLight = new THREE.DirectionalLight(0x4fd1c7, 0.5);
        rimLight.position.set(0, 3, -4);
        scene.add(rimLight);

        // Hemisphere light for realistic ambient
        const hemiLight = new THREE.HemisphereLight(0xffffbb, 0x080820, 0.4);
        scene.add(hemiLight);

        // Ground plane for shadows
        const groundGeometry = new THREE.PlaneGeometry(10, 10);
        const groundMaterial = new THREE.ShadowMaterial({ opacity: 0.2 });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = -0.1;
        ground.receiveShadow = true;
        scene.add(ground);

        // Model Loading with enhanced error handling
        const loader = new GLTFLoader();
        let modelLoaded = false;

        const loadModel = () => {
            loader.load(MODEL_PATH, 
                (gltf: GLTF) => {
                    if (modelLoaded) return; // Prevent double loading
                    modelLoaded = true;

                    const model = gltf.scene;
                    model.scale.set(0.8, 0.8, 0.8); // Scale down for better fit
                    model.position.set(0, 0, 0);
                    model.castShadow = true;
                    modelRef.current = model; // Store reference to the full model
                    
                    // Apply DuckBot-like materials/colors if needed
                    model.traverse((child: THREE.Object3D) => {
                        if (child instanceof THREE.Mesh) {
                            child.castShadow = true;
                            child.receiveShadow = true;
                            
                            // Enhance materials for better visual quality
                            if (child.material instanceof THREE.MeshStandardMaterial) {
                                child.material.metalness = 0.3;
                                child.material.roughness = 0.7;
                            }
                        }
                    });
                    
                    scene.add(model);

                    // Find morph target mesh for lip-sync animation
                    let morphTargetMesh: THREE.Mesh | null = null;
                    model.traverse((node: THREE.Object3D) => {
                        if (!morphTargetMesh && node instanceof THREE.Mesh && node.morphTargetInfluences) {
                            console.log("DuckBot Clippy: Found morph target mesh:", node.name, node.morphTargetDictionary);
                            morphTargetMesh = node;
                            headMeshRef.current = node;
                            morphInfluencesRef.current = node.morphTargetInfluences;
                            onModelLoad(node.morphTargetDictionary as MorphTargetDictionary);
                        }
                    });
                    
                    if (!morphTargetMesh) {
                        console.warn("DuckBot Clippy: No morph targets found - speech animation will be limited");
                        // Create a fallback for basic animation
                        onModelLoad({});
                    }

                    // Start subtle idle animations
                    startIdleAnimations();
                }, 
                (xhr: { loaded: number; total: number }) => {
                    if (xhr.total > 0) {
                        const progress = Math.round((xhr.loaded / xhr.total) * 100);
                        onLoadProgress(progress);
                    }
                }, 
                (error: ErrorEvent) => {
                    console.error('DuckBot Clippy: Model loading error:', error);
                    // Attempt retry after a delay
                    setTimeout(() => {
                        if (!modelLoaded) {
                            console.log('DuckBot Clippy: Retrying model load...');
                            loadModel();
                        }
                    }, 2000);
                }
            );
        };

        // Start loading the model
        loadModel();

        // Enhanced idle animations for natural Clippy-like behavior - ONLY animate the whole robot
        let idleAnimationId: number;
        let animationTime = 0;
        const startIdleAnimations = () => {
            animationTime = 0;
            const idleLoop = () => {
                idleAnimationId = requestAnimationFrame(idleLoop);
                animationTime += 0.006; // Even slower for more natural movement

                // ONLY animate the entire model as a whole - no individual part movement
                if (modelRef.current) {
                    // Gentle breathing animation for the whole robot
                    const breathe = Math.sin(animationTime * 1.5) * 0.01;
                    modelRef.current.position.y = breathe;

                    // Very subtle full body rotation
                    const sway = Math.sin(animationTime * 0.5) * 0.02;
                    modelRef.current.rotation.y = sway;

                    // Occasional slight bounce
                    const bounce = Math.sin(animationTime * 2.5) > 0.96 ? 0.008 : 0;
                    modelRef.current.position.y += bounce;
                }
            };
            idleLoop();
        };

        // Main animation loop
        let animationFrameId: number;
        const animate = () => {
            animationFrameId = requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        };
        animate();

        // Resize handler
        const handleResize = () => {
            if (!currentMount) return;
            
            camera.aspect = currentMount.clientWidth / currentMount.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(currentMount.clientWidth, currentMount.clientHeight);
        };
        window.addEventListener('resize', handleResize);

        // Handle visibility for performance
        const handleVisibilityChange = () => {
            if (document.hidden) {
                // Pause animations when window is hidden
                cancelAnimationFrame(animationFrameId);
                cancelAnimationFrame(idleAnimationId);
            } else {
                // Resume animations
                animate();
                if (modelLoaded) startIdleAnimations();
            }
        };
        document.addEventListener('visibilitychange', handleVisibilityChange);

        // Cleanup
        return () => {
            window.removeEventListener('resize', handleResize);
            document.removeEventListener('visibilitychange', handleVisibilityChange);
            cancelAnimationFrame(animationFrameId);
            cancelAnimationFrame(idleAnimationId);
            
            // Dispose of Three.js resources
            scene.traverse((child) => {
                if (child instanceof THREE.Mesh) {
                    if (child.geometry) child.geometry.dispose();
                    if (child.material) {
                        if (Array.isArray(child.material)) {
                            child.material.forEach(material => material.dispose());
                        } else {
                            child.material.dispose();
                        }
                    }
                }
            });
            
            renderer.dispose();
            
            if (currentMount && renderer.domElement && currentMount.contains(renderer.domElement)) {
                currentMount.removeChild(renderer.domElement);
            }
        };
    }, [onModelLoad, onLoadProgress]);

    return (
        <div 
            ref={mountRef} 
            className="w-full h-full bg-gradient-to-b from-gray-800 to-gray-900"
            style={{ cursor: 'grab' }}
        />
    );
});