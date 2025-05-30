// AEON Weapon AI System - 3D Model Viewer
// Three.js-based OBJ model viewer for generated weapons

class WeaponModelViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.currentModel = null;
        this.currentWeapon = null;
        this.animationId = null;
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error('Model viewer container not found');
            return;
        }
        
        // Create scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xf0f0f0);
        
        // Create camera
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
        this.camera.position.set(2, 2, 2);
        
        // Create renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(width, height);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        
        // Clear container and add renderer
        this.container.innerHTML = '';
        this.container.appendChild(this.renderer.domElement);
        
        // Add lights
        this.setupLights();
        
        // Add orbit controls
        this.setupControls();
        
        // Add grid helper
        const gridHelper = new THREE.GridHelper(10, 10, 0x888888, 0xcccccc);
        this.scene.add(gridHelper);
        
        // Start render loop
        this.animate();
        
        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());
        
        console.log('🎮 3D Model Viewer initialized');
    }
    
    setupLights() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        this.scene.add(ambientLight);
        
        // Directional light (main)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(5, 5, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        this.scene.add(directionalLight);
        
        // Point light (fill)
        const pointLight = new THREE.PointLight(0xffffff, 0.3);
        pointLight.position.set(-5, 3, -5);
        this.scene.add(pointLight);
        
        // Hemisphere light (sky)
        const hemisphereLight = new THREE.HemisphereLight(0x87ceeb, 0x654321, 0.3);
        this.scene.add(hemisphereLight);
    }
    
    setupControls() {
        // Basic orbit controls implementation
        this.controls = {
            mouseDown: false,
            mouseX: 0,
            mouseY: 0,
            rotationSpeed: 0.005,
            zoomSpeed: 0.1
        };
        
        const canvas = this.renderer.domElement;
        
        canvas.addEventListener('mousedown', (e) => {
            this.controls.mouseDown = true;
            this.controls.mouseX = e.clientX;
            this.controls.mouseY = e.clientY;
        });
        
        canvas.addEventListener('mouseup', () => {
            this.controls.mouseDown = false;
        });
        
        canvas.addEventListener('mousemove', (e) => {
            if (this.controls.mouseDown) {
                const deltaX = e.clientX - this.controls.mouseX;
                const deltaY = e.clientY - this.controls.mouseY;
                
                // Rotate camera around the scene
                const spherical = new THREE.Spherical();
                spherical.setFromVector3(this.camera.position);
                spherical.theta -= deltaX * this.controls.rotationSpeed;
                spherical.phi += deltaY * this.controls.rotationSpeed;
                spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi));
                
                this.camera.position.setFromSpherical(spherical);
                this.camera.lookAt(0, 0, 0);
                
                this.controls.mouseX = e.clientX;
                this.controls.mouseY = e.clientY;
            }
        });
        
        canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            const distance = this.camera.position.length();
            const newDistance = distance + (e.deltaY * this.controls.zoomSpeed);
            const clampedDistance = Math.max(1, Math.min(20, newDistance));
            
            this.camera.position.normalize().multiplyScalar(clampedDistance);
        });
    }
    
    async loadModel(weaponPath, weaponData = null) {
        try {
            console.log('📥 Loading weapon model:', weaponPath);
            
            // Remove existing model
            if (this.currentModel) {
                this.scene.remove(this.currentModel);
                this.currentModel = null;
            }
            
            // Show loading state
            this.showLoadingState(true);
            
            // Load OBJ file
            const objText = await this.fetchOBJFile(weaponPath);
            const geometry = this.parseOBJ(objText);
            
            // Create material based on weapon personality
            const material = this.createWeaponMaterial(weaponData);
            
            // Create mesh
            this.currentModel = new THREE.Mesh(geometry, material);
            this.currentModel.castShadow = true;
            this.currentModel.receiveShadow = true;
            
            // Center and scale the model
            this.fitModelToView();
            
            // Add to scene
            this.scene.add(this.currentModel);
            
            // Store weapon data
            this.currentWeapon = weaponData;
            
            // Hide loading state
            this.showLoadingState(false);
            
            console.log('✅ Model loaded successfully');
            
        } catch (error) {
            console.error('❌ Failed to load model:', error);
            this.showError('Failed to load 3D model: ' + error.message);
        }
    }
    
    async fetchOBJFile(path) {
        const response = await fetch(path);
        if (!response.ok) {
            throw new Error(`Failed to fetch OBJ file: ${response.statusText}`);
        }
        return await response.text();
    }
    
    parseOBJ(objText) {
        const vertices = [];
        const normals = [];
        const uvs = [];
        const faces = [];
        
        const lines = objText.split('\n');
        
        for (const line of lines) {
            const parts = line.trim().split(/\s+/);
            
            if (parts[0] === 'v') {
                // Vertex
                vertices.push(
                    parseFloat(parts[1]),
                    parseFloat(parts[2]),
                    parseFloat(parts[3])
                );
            } else if (parts[0] === 'vn') {
                // Normal
                normals.push(
                    parseFloat(parts[1]),
                    parseFloat(parts[2]),
                    parseFloat(parts[3])
                );
            } else if (parts[0] === 'vt') {
                // Texture coordinate
                uvs.push(
                    parseFloat(parts[1]),
                    parseFloat(parts[2])
                );
            } else if (parts[0] === 'f') {
                // Face
                const faceVertices = [];
                for (let i = 1; i < parts.length; i++) {
                    const indices = parts[i].split('/');
                    faceVertices.push(parseInt(indices[0]) - 1); // OBJ indices are 1-based
                }
                
                // Triangulate if necessary
                if (faceVertices.length === 3) {
                    faces.push(...faceVertices);
                } else if (faceVertices.length === 4) {
                    // Quad to triangles
                    faces.push(faceVertices[0], faceVertices[1], faceVertices[2]);
                    faces.push(faceVertices[0], faceVertices[2], faceVertices[3]);
                }
            }
        }
        
        // Create geometry
        const geometry = new THREE.BufferGeometry();
        
        // Set vertices
        const vertexArray = new Float32Array(faces.length * 3);
        for (let i = 0; i < faces.length; i++) {
            const vertexIndex = faces[i] * 3;
            vertexArray[i * 3] = vertices[vertexIndex];
            vertexArray[i * 3 + 1] = vertices[vertexIndex + 1];
            vertexArray[i * 3 + 2] = vertices[vertexIndex + 2];
        }
        
        geometry.setAttribute('position', new THREE.BufferAttribute(vertexArray, 3));
        
        // Compute normals if not provided
        if (normals.length === 0) {
            geometry.computeVertexNormals();
        }
        
        return geometry;
    }
    
    createWeaponMaterial(weaponData) {
        const personality = weaponData?.personality || 'default';
        
        // Personality-based colors
        const personalityColors = {
            'aggressive_warrior': 0xff4444,    // Red
            'strategic_mage': 0x4444ff,       // Blue
            'defensive_guardian': 0xffaa44,   // Gold
            'agile_assassin': 0x8844ff,       // Purple
            'elemental_mage': 0x44ff88,       // Green
            'default': 0x888888               // Gray
        };
        
        const color = personalityColors[personality] || personalityColors.default;
        
        return new THREE.MeshPhongMaterial({
            color: color,
            shininess: 100,
            specular: 0x222222,
            side: THREE.DoubleSide
        });
    }
    
    fitModelToView() {
        if (!this.currentModel) return;
        
        // Calculate bounding box
        const box = new THREE.Box3().setFromObject(this.currentModel);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        
        // Center the model
        this.currentModel.position.sub(center);
        
        // Scale to fit in view
        const maxDimension = Math.max(size.x, size.y, size.z);
        if (maxDimension > 2) {
            const scale = 2 / maxDimension;
            this.currentModel.scale.setScalar(scale);
        }
        
        // Adjust camera position
        const distance = Math.max(3, maxDimension * 1.5);
        this.camera.position.normalize().multiplyScalar(distance);
        this.camera.lookAt(0, 0, 0);
    }
    
    showLoadingState(show) {
        if (show) {
            this.container.style.opacity = '0.6';
            this.container.style.pointerEvents = 'none';
        } else {
            this.container.style.opacity = '1';
            this.container.style.pointerEvents = 'auto';
        }
    }
    
    showError(message) {
        this.container.innerHTML = `
            <div class="d-flex align-items-center justify-content-center h-100">
                <div class="text-center">
                    <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                    <p class="text-danger">${message}</p>
                    <button class="btn btn-outline-primary" onclick="resetModel()">
                        <i class="fas fa-redo"></i> Try Again
                    </button>
                </div>
            </div>
        `;
    }
    
    reset() {
        // Remove current model
        if (this.currentModel) {
            this.scene.remove(this.currentModel);
            this.currentModel = null;
        }
        
        // Reset camera position
        this.camera.position.set(2, 2, 2);
        this.camera.lookAt(0, 0, 0);
        
        // Clear weapon data
        this.currentWeapon = null;
        
        console.log('🔄 Model viewer reset');
    }
    
    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        
        // Auto-rotate model if no user interaction
        if (this.currentModel && !this.controls.mouseDown) {
            this.currentModel.rotation.y += 0.005;
        }
        
        this.renderer.render(this.scene, this.camera);
    }
    
    onWindowResize() {
        if (!this.container) return;
        
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        
        this.renderer.setSize(width, height);
    }
    
    dispose() {
        // Clean up resources
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        if (this.currentModel) {
            this.scene.remove(this.currentModel);
        }
        
        if (this.renderer) {
            this.renderer.dispose();
        }
        
        window.removeEventListener('resize', this.onWindowResize);
        
        console.log('🗑️ Model viewer disposed');
    }
}

// Global model viewer instance
let modelViewer = null;

// Initialize model viewer when modal is shown
document.addEventListener('DOMContentLoaded', function() {
    const weaponModal = document.getElementById('weaponModal');
    if (weaponModal) {
        weaponModal.addEventListener('shown.bs.modal', function() {
            if (!modelViewer) {
                modelViewer = new WeaponModelViewer('model-viewer');
            }
        });
        
        weaponModal.addEventListener('hidden.bs.modal', function() {
            if (modelViewer) {
                modelViewer.reset();
            }
        });
    }
});

// Global functions for model viewer control
function loadModel() {
    if (!modelViewer || !currentWeapon) {
        showError('Model viewer not initialized or no weapon selected');
        return;
    }
    
    const modelPath = currentWeapon.web_path || `/download/weapon/${currentWeapon.filename}`;
    modelViewer.loadModel(modelPath, currentWeapon);
}

function resetModel() {
    if (modelViewer) {
        modelViewer.reset();
    }
}

// Export for global use
window.WeaponModelViewer = WeaponModelViewer;
window.loadModel = loadModel;
window.resetModel = resetModel;

console.log('🎨 3D Model Viewer loaded');