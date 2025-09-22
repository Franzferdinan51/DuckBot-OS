// Three.js examples type declarations
declare module 'three/examples/jsm/loaders/GLTFLoader.js' {
    import { Group } from 'three';

    export interface GLTF {
        scene: Group;
        animations?: any[];
        cameras?: any[];
        asset?: any;
    }

    export class GLTFLoader {
        load(
            url: string,
            onLoad: (gltf: GLTF) => void,
            onProgress?: (event: ProgressEvent) => void,
            onError?: (event: ErrorEvent) => void
        ): void;
    }
}

declare module 'three/examples/jsm/controls/OrbitControls.js' {
    import { Camera, Object3D } from 'three';

    export class OrbitControls {
        constructor(camera: Camera, domElement: HTMLElement);
        target: THREE.Vector3;
        enablePan: boolean;
        enableZoom: boolean;
        minDistance: number;
        maxDistance: number;
        minPolarAngle: number;
        maxPolarAngle: number;
        dampingFactor: number;
        enableDamping: boolean;
        autoRotate: boolean;
        autoRotateSpeed: number;
        update(): void;
    }
}