/*
 * Adaptive Three.js hero runtime for generated websites.
 * Opt in by marking a visual container with data-three-hero.
 * Modes: orb, product, abstract, space. Decorative canvas only; meaningful content stays in HTML.
 */
const THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js';

export function initThreeHero(root = document) {
  const hosts = [...root.querySelectorAll('[data-three-hero],[data-3d="three-hero"]')];
  const disposers = [];
  const reduceQuery = window.matchMedia?.('(prefers-reduced-motion: reduce)');
  const finePointer = window.matchMedia?.('(hover: hover) and (pointer: fine)').matches ?? false;

  hosts.forEach((host) => {
    if (!(host instanceof HTMLElement) || host.dataset.threeReady === 'true') return;
    host.dataset.threeReady = 'true';
    host.classList.add('three-hero-fallback');
    let renderer, scene, camera, resizeObserver, visibilityObserver, frame = 0;
    let disposed = false, visible = true, pointerX = 0, pointerY = 0;
    const reduced = Boolean(reduceQuery?.matches);
    const mode = ['orb', 'product', 'abstract', 'space'].includes(host.dataset.threeMode) ? host.dataset.threeMode : 'orb';
    const color = host.dataset.threeColor || getComputedStyle(host).getPropertyValue('--primary').trim() || '#7c5cff';
    const geometries = [], materials = [];

    const cleanup = () => {
      if (disposed) return;
      disposed = true;
      cancelAnimationFrame(frame);
      visibilityObserver?.disconnect();
      resizeObserver?.disconnect();
      host.removeEventListener('pointermove', onPointerMove);
      host.removeEventListener('pointerleave', onPointerLeave);
      window.removeEventListener('resize', resize);
      if (renderer) {
        renderer.domElement.removeEventListener('webglcontextlost', onContextLost);
        renderer.dispose();
        renderer.domElement.remove();
      }
      geometries.forEach((geometry) => geometry.dispose());
      materials.forEach((material) => material.dispose());
      delete host.dataset.threeReady;
    };
    const onContextLost = (event) => {
      event.preventDefault?.();
      cleanup();
      host.classList.add('three-hero-fallback');
    };
    const onPointerMove = (event) => {
      const rect = host.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      pointerX = Math.max(-1, Math.min(1, ((event.clientX - rect.left) / rect.width - 0.5) * 2));
      pointerY = Math.max(-1, Math.min(1, ((event.clientY - rect.top) / rect.height - 0.5) * 2));
    };
    const onPointerLeave = () => { pointerX = 0; pointerY = 0; };
    const resize = () => {
      if (!renderer || !camera || disposed) return;
      const width = Math.max(host.clientWidth, 1), height = Math.max(host.clientHeight, 1);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, width < 600 ? 1 : 1.5));
      renderer.setSize(width, height, false);
      renderFrame();
    };
    const renderFrame = () => {
      if (!disposed && renderer && scene && camera) renderer.render(scene, camera);
    };
    const animate = () => {
      if (disposed || !renderer || !visible || reduced) return;
      const t = performance.now() * 0.00025;
      if (scene?.userData?.heroGroup) {
        const group = scene.userData.heroGroup;
        group.rotation.y += (pointerX * 0.12 - group.rotation.y) * 0.018 + 0.0012;
        group.rotation.x += (-pointerY * 0.07 - group.rotation.x) * 0.018 + 0.0004;
        group.position.y = Math.sin(t * 2) * 0.055;
      }
      if (scene?.userData?.particles) scene.userData.particles.rotation.y = t * 0.7;
      if (scene?.userData?.halo) scene.userData.halo.rotation.z = t * 0.6;
      renderFrame();
      frame = requestAnimationFrame(animate);
    };
    window.addEventListener('pagehide', cleanup, { once: true });
    disposers.push(cleanup);
    import(THREE_URL).then((THREE) => {
      if (disposed || !host.isConnected) { cleanup(); return; }
      const width = Math.max(host.clientWidth, 1), height = Math.max(host.clientHeight, 1);
      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 100);
      camera.position.set(0, 0, mode === 'product' ? 7.2 : 6.4);
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: width >= 600, powerPreference: 'low-power', stencil: false, depth: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, width < 600 ? 1 : 1.5));
      renderer.setSize(width, height, false);
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.15;
      renderer.shadowMap.enabled = width >= 600;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      renderer.domElement.setAttribute('aria-hidden', 'true');
      renderer.domElement.setAttribute('role', 'presentation');
      renderer.domElement.tabIndex = -1;
      host.prepend(renderer.domElement);
      renderer.domElement.addEventListener('webglcontextlost', onContextLost, { once: true });

      scene.add(new THREE.HemisphereLight(0xdce9ff, 0x171225, 1.8));
      const key = new THREE.DirectionalLight(0xffffff, 3.1);
      key.position.set(4, 6, 7); key.castShadow = width >= 600; scene.add(key);
      const rim = new THREE.PointLight(color, 42, 18); rim.position.set(-4, 1.5, -1); scene.add(rim);
      const fill = new THREE.PointLight('#60d8ff', 24, 20); fill.position.set(4, -2, 4); scene.add(fill);
      const group = new THREE.Group(); scene.add(group); scene.userData.heroGroup = group;

      const standard = (opts) => { const m = new THREE.MeshStandardMaterial(opts); materials.push(m); return m; };
      const physical = (opts) => { const m = new THREE.MeshPhysicalMaterial(opts); materials.push(m); return m; };
      const mesh = (geometry, material, position = [0,0,0], rotation = [0,0,0], scale = [1,1,1], parent = group) => {
        geometries.push(geometry);
        const item = new THREE.Mesh(geometry, material);
        item.position.set(...position); item.rotation.set(...rotation); item.scale.set(...scale);
        item.castShadow = width >= 600; item.receiveShadow = width >= 600; parent.add(item); return item;
      };

      if (mode === 'product') {
        // Procedural premium product stage: a glass/metal device with a lit display and studio highlights.
        mesh(new THREE.BoxGeometry(2.15, 2.75, 0.18, 4, 4, 2), physical({ color: '#171b27', metalness: 0.82, roughness: 0.22, clearcoat: 1, clearcoatRoughness: 0.14 }), [0,0,0], [0.06,-0.18,-0.08]);
        mesh(new THREE.BoxGeometry(1.91, 2.48, 0.025, 2, 2, 1), physical({ color: host.dataset.screenColor || color, metalness: 0.2, roughness: 0.2, transmission: 0.08, thickness: 0.25, clearcoat: 1 }), [0,0.03,0.104], [0.06,-0.18,-0.08]);
        mesh(new THREE.TorusGeometry(0.11, 0.022, 12, 40), standard({ color: '#c8d4e7', metalness: 0.85, roughness: 0.2 }), [0,-1.13,0.12], [0.06,-0.18,-0.08]);
        mesh(new THREE.SphereGeometry(0.055, 24, 16), standard({ color: '#dce6f5', metalness: 0.5, roughness: 0.22 }), [0.72,0.92,0.13]);
        const halo = mesh(new THREE.TorusGeometry(2.15, 0.012, 8, 160), standard({ color, metalness: 0.75, roughness: 0.25, emissive: color, emissiveIntensity: 0.25 }), [0,0, -0.55], [0.75,0.1,0.2], [1,0.72,1], scene);
        scene.userData.halo = halo;
      } else if (mode === 'space') {
        mesh(new THREE.SphereGeometry(1.18, 64, 48), physical({ color: '#17234b', metalness: 0.25, roughness: 0.34, clearcoat: 0.7, emissive: '#0c1e45', emissiveIntensity: 0.25 }));
        mesh(new THREE.TorusGeometry(1.62, 0.026, 12, 160), standard({ color: '#a7c7ff', metalness: 0.85, roughness: 0.18, emissive: '#254e9c', emissiveIntensity: 0.18 }), [0,0,0], [0.9,0.18,0.25]);
        mesh(new THREE.TorusGeometry(1.92, 0.012, 8, 160), standard({ color, metalness: 0.72, roughness: 0.22, emissive: color, emissiveIntensity: 0.25 }), [0,0,0], [1.2,-0.42,0.5]);
      } else if (mode === 'abstract') {
        mesh(new THREE.IcosahedronGeometry(1.15, 2), physical({ color, metalness: 0.72, roughness: 0.22, clearcoat: 1, clearcoatRoughness: 0.12 }));
        mesh(new THREE.IcosahedronGeometry(1.22, 1), standard({ color: '#c5f5ff', metalness: 0.5, roughness: 0.24, wireframe: true, transparent: true, opacity: 0.42 }));
        mesh(new THREE.TorusGeometry(1.62, 0.018, 12, 160), standard({ color: '#a7f3ff', metalness: 0.8, roughness: 0.18, emissive: '#1c7b96', emissiveIntensity: 0.18 }), [0,0,0], [0.65,0.25,0.3]);
      } else {
        mesh(new THREE.SphereGeometry(1.06, 64, 48), physical({ color, metalness: 0.66, roughness: 0.19, clearcoat: 1, clearcoatRoughness: 0.08, emissive: color, emissiveIntensity: 0.12 }));
        mesh(new THREE.SphereGeometry(1.12, 48, 32), standard({ color: '#c8f7ff', metalness: 0.45, roughness: 0.24, wireframe: true, transparent: true, opacity: 0.28 }));
        mesh(new THREE.TorusGeometry(1.55, 0.018, 12, 160), physical({ color: '#8deaff', metalness: 0.88, roughness: 0.16, clearcoat: 1 }), [0,0,0], [0.65,0.25,0.3]);
        mesh(new THREE.TorusGeometry(1.9, 0.012, 8, 160), standard({ color: '#c4b5fd', metalness: 0.8, roughness: 0.2, emissive: '#5b3bff', emissiveIntensity: 0.16 }), [0,0,0], [1.05,-0.5,0.8]);
      }

      const particleCount = width < 600 ? 36 : Math.min(120, Math.max(56, Math.floor(width * height / 9000)));
      const positions = new Float32Array(particleCount * 3);
      let seed = 1337;
      const rand = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
      for (let i = 0; i < particleCount; i++) {
        positions[i*3] = (rand() - 0.5) * 8.5;
        positions[i*3+1] = (rand() - 0.5) * 5.5;
        positions[i*3+2] = (rand() - 0.5) * 5;
      }
      const pg = new THREE.BufferGeometry(); pg.setAttribute('position', new THREE.BufferAttribute(positions, 3)); geometries.push(pg);
      const pm = new THREE.PointsMaterial({ color: '#d9e7ff', size: width < 600 ? 0.018 : 0.024, transparent: true, opacity: 0.68, sizeAttenuation: true }); materials.push(pm);
      const particles = new THREE.Points(pg, pm); scene.add(particles); scene.userData.particles = particles;

      host.addEventListener('pointermove', onPointerMove, { passive: true });
      host.addEventListener('pointerleave', onPointerLeave, { passive: true });
      resizeObserver = 'ResizeObserver' in window ? new ResizeObserver(resize) : null;
      resizeObserver?.observe(host);
      if (!resizeObserver) window.addEventListener('resize', resize, { passive: true });
      visibilityObserver = 'IntersectionObserver' in window ? new IntersectionObserver(([entry]) => {
        visible = Boolean(entry?.isIntersecting);
        cancelAnimationFrame(frame);
        if (visible && !reduced) animate(); else renderFrame();
      }, { rootMargin: '100px' }) : null;
      visibilityObserver?.observe(host);
      host.classList.remove('three-hero-fallback');
      renderFrame();
      if (!reduced && (!visibilityObserver || visible)) animate();
    }).catch(() => {
      host.classList.add('three-hero-fallback');
      delete host.dataset.threeReady;
    });
  });

  return () => disposers.forEach((dispose) => dispose());
}

// Static HTML pages use this module directly. React calls the same initializer after mount.
if (typeof document !== 'undefined') initThreeHero();
