import React, { forwardRef, useImperativeHandle, useRef, useEffect } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VRMLoader } from 'three/addons/loaders/VRMLoader.js';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';
import type { MorphTargetDictionary, SceneHandle } from '../types';

interface ThreeSceneProps {
    modelUrl: string;
    onModelLoad: (morphTargetDictionary: MorphTargetDictionary) => void;
    onLoadProgress: (progress: number) => void;
}

export const ThreeScene = forwardRef<SceneHandle, ThreeSceneProps>(({ modelUrl, onModelLoad, onLoadProgress }, ref) => {
    const mountRef = useRef<HTMLDivElement>(null);
    const modelRef = useRef<THREE.Group>();
    const morphTargetDictionaryRef = useRef<MorphTargetDictionary>({});
    const cleanupRef = useRef<() => void>(() => {});

    useImperativeHandle(ref, () => ({
        setMorphTargetInfluence: (name, value) => {
            const model = modelRef.current;
            const dictionary = morphTargetDictionaryRef.current;
            if (model && dictionary && name in dictionary) {
                const morphIndex = dictionary[name];
                model.traverse((child) => {
                    if (child instanceof THREE.SkinnedMesh && child.morphTargetInfluences) {
                        if (morphIndex < child.morphTargetInfluences.length) {
                            child.morphTargetInfluences[morphIndex] = value;
                        }
                    }
                });
            }
        },
        resetMorphTargets: () => {
            const model = modelRef.current;
            if (model) {
                model.traverse((child) => {
                    if (child instanceof THREE.SkinnedMesh && child.morphTargetInfluences) {
                        for (let i = 0; i < child.morphTargetInfluences.length; i++) {
                            child.morphTargetInfluences[i] = 0;
                        }
                    }
                });
            }
        }
    }));

    useEffect(() => {
        if (!mountRef.current) return;
        
        const currentMount = mountRef.current;

        // Cleanup previous instance
        cleanupRef.current();
        while (currentMount.firstChild) {
            currentMount.removeChild(currentMount.firstChild);
        }

        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x2d3748);
        scene.fog = new THREE.Fog(0x2d3748, 4, 15);

        const camera = new THREE.PerspectiveCamera(50, currentMount.clientWidth / currentMount.clientHeight, 0.1, 1000);
        camera.position.set(0, 1.6, 2.8);

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(currentMount.clientWidth, currentMount.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        currentMount.appendChild(renderer.domElement);

        const controls = new OrbitControls(camera, renderer.domElement);
        controls.target.set(0, 1.0, 0);
        controls.enablePan = true;
        controls.enableZoom = true;
        controls.minDistance = 1.5;
        controls.maxDistance = 8;
        controls.dampingFactor = 0.1;
        controls.enableDamping = true;

        const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
        scene.add(ambientLight);
        const keyLight = new THREE.DirectionalLight(0xffefd5, 2.0);
        keyLight.position.set(1, 1, 2);
        scene.add(keyLight);

        let loader: GLTFLoader | VRMLoader | FBXLoader;
        const fileExtension = modelUrl.split('.').pop()?.toLowerCase();

        if (fileExtension === 'vrm') {
            loader = new VRMLoader();
        } else if (fileExtension === 'fbx') {
            loader = new FBXLoader();
        } else {
            loader = new GLTFLoader();
        }

        loader.load(modelUrl, (loadedModel) => {
            const model = (loadedModel as any).scene || loadedModel;
            modelRef.current = model;
            scene.add(model);

            const box = new THREE.Box3().setFromObject(model);
            const center = box.getCenter(new THREE.Vector3());
            model.position.sub(center);

            const dictionary: MorphTargetDictionary = {};
            model.traverse((child: any) => {
                if (child.isSkinnedMesh && child.morphTargetDictionary) {
                    for (const [name, index] of Object.entries(child.morphTargetDictionary)) {
                        dictionary[name] = index as number;
                    }
                }
            });
            morphTargetDictionaryRef.current = dictionary;
            onModelLoad(dictionary);

        }, (xhr) => {
            if (xhr.total > 0) {
                const progress = Math.round((xhr.loaded / xhr.total) * 100);
                onLoadProgress(progress);
            }
        }, (error) => {
            console.error('An error happened during model loading:', error);
            alert(`Failed to load model. Please ensure the file format is supported (GLB, GLTF, VRM, FBX). Error: ${error.message}`);
        });

        let animationFrameId: number;
        const animate = () => {
            animationFrameId = requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        };
        animate();

        const handleResize = () => {
            camera.aspect = currentMount.clientWidth / currentMount.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(currentMount.clientWidth, currentMount.clientHeight);
        };
        window.addEventListener('resize', handleResize);

        cleanupRef.current = () => {
            window.removeEventListener('resize', handleResize);
            cancelAnimationFrame(animationFrameId);
        };

    }, [modelUrl, onModelLoad, onLoadProgress]);

    return <div ref={mountRef} className="w-full h-full" />;
});
