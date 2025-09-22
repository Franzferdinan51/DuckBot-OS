import React, { useRef, useEffect, forwardRef, useImperativeHandle } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import type { MorphTargetDictionary, SceneHandle } from '../types';

interface ThreeSceneProps {
    onModelLoad: (dictionary: MorphTargetDictionary) => void;
    onLoadProgress: (progress: number) => void;
}

// Replaced the broken model with a permanent, stable link from the official threejs.org examples.
const MODEL_PATH = 'https://threejs.org/examples/models/gltf/RobotExpressive/RobotExpressive.glb';

export const ThreeScene = forwardRef<SceneHandle, ThreeSceneProps>(({ onModelLoad, onLoadProgress }, ref) => {
    const mountRef = useRef<HTMLDivElement>(null);
    const headMeshRef = useRef<THREE.Mesh | null>(null);
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

        // Scene, Camera, Renderer setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x2d3748);
        scene.fog = new THREE.Fog(0x2d3748, 4, 15);

        // Adjust camera for the new full-body avatar
        const camera = new THREE.PerspectiveCamera(50, currentMount.clientWidth / currentMount.clientHeight, 0.1, 1000);
        camera.position.set(0, 1.6, 2.8);

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(currentMount.clientWidth, currentMount.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        currentMount.appendChild(renderer.domElement);

        // Update controls for the new avatar
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.target.set(0, 1.0, 0); // Target the upper body/head area
        controls.enablePan = true;
        controls.enableZoom = true;
        controls.minDistance = 1.5;
        controls.maxDistance = 8;
        controls.dampingFactor = 0.1;
        controls.enableDamping = true;
        
        // Lighting setup optimized for characters
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
        scene.add(ambientLight);
        const keyLight = new THREE.DirectionalLight(0xffefd5, 2.0);
        keyLight.position.set(1, 1, 2);
        scene.add(keyLight);
        const fillLight = new THREE.DirectionalLight(0xd5e5ff, 1.0);
        fillLight.position.set(-1, 0.5, 1);
        scene.add(fillLight);
        const hemiLight = new THREE.HemisphereLight(0xffffbb, 0x080820, 0.4);
        scene.add(hemiLight);

        // Model Loading
        const loader = new GLTFLoader();
        loader.load(MODEL_PATH, 
            (gltf) => {
                const model = gltf.scene;
                scene.add(model);

                model.traverse((node) => {
                    // This logic is robust and finds the first mesh with morph targets
                    if (!headMeshRef.current && node instanceof THREE.Mesh && node.morphTargetInfluences) {
                        console.log("Found a Mesh with morph targets:", node.name, node.morphTargetDictionary);
                        headMeshRef.current = node;
                        morphInfluencesRef.current = node.morphTargetInfluences;
                        onModelLoad(node.morphTargetDictionary as MorphTargetDictionary);
                    }
                });
                
                if (!headMeshRef.current) {
                     console.error("Could not find any mesh with morph targets in the loaded model.");
                }
            }, 
            (xhr) => { // Progress callback
                if (xhr.total > 0) {
                    const progress = Math.round((xhr.loaded / xhr.total) * 100);
                    onLoadProgress(progress);
                }
            }, 
            (error) => {
                console.error('An error happened during model loading:', error);
            }
        );

        // Animation Loop
        let animationFrameId: number;
        const animate = () => {
            animationFrameId = requestAnimationFrame(animate);
            controls.update(); // Required if damping is enabled
            renderer.render(scene, camera);
        };
        animate();

        // Resize handler
        const handleResize = () => {
            camera.aspect = currentMount.clientWidth / currentMount.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(currentMount.clientWidth, currentMount.clientHeight);
        };
        window.addEventListener('resize', handleResize);

        // Cleanup
        return () => {
            window.removeEventListener('resize', handleResize);
            cancelAnimationFrame(animationFrameId);
            if (currentMount && renderer.domElement) {
               currentMount.removeChild(renderer.domElement);
            }
        };
    }, [onModelLoad, onLoadProgress]);

    return <div ref={mountRef} className="w-full h-full" />;
});