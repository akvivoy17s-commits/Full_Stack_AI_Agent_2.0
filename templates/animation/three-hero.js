/* Optional opt-in Three.js hero. Add data-three-hero or data-3d="three-hero" to a hero container. */
(() => {
  'use strict';
  const hosts = [...document.querySelectorAll('[data-three-hero],[data-3d="three-hero"]')];
  if (!hosts.length) return;
  const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
  const THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js';

  hosts.forEach((host) => {
    if (host.dataset.threeReady === 'true') return;
    host.dataset.threeReady = 'true';
    host.classList.add('three-hero-fallback');
    let renderer;
    let frame = 0;
    let disposed = false;
    let visible = true;
    let scene;
    let camera;
    let group;
    let resizeObserver;
    let visibilityObserver;

    const cleanup = () => {
      disposed = true;
      cancelAnimationFrame(frame);
      visibilityObserver?.disconnect();
      resizeObserver?.disconnect();
      if (renderer) {
        renderer.domElement.remove();
        renderer.dispose();
      }
      scene?.traverse((node) => {
        if (node.geometry) node.geometry.dispose();
        if (node.material) (Array.isArray(node.material) ? node.material : [node.material]).forEach((m) => m.dispose?.());
      });
    };
    window.addEventListener('pagehide', cleanup, { once: true });

    import(THREE_URL).then((THREE) => {
      if (disposed || !host.isConnected) return;
      const width = Math.max(host.clientWidth, 1);
      const height = Math.max(host.clientHeight, 1);
      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 100);
      camera.position.set(0, 0, 6.2);
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
      renderer.setSize(width, height);
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.domElement.setAttribute('aria-hidden', 'true');
      renderer.domElement.tabIndex = -1;
      host.prepend(renderer.domElement);

      scene.add(new THREE.AmbientLight(0xffffff, 1.7));
      const key = new THREE.PointLight(host.getAttribute('data-three-color') || '#8b5cf6', 32, 24);
      key.position.set(3, 3, 5);
      scene.add(key);
      const fill = new THREE.PointLight('#38bdf8', 16, 18);
      fill.position.set(-4, -2, 1);
      scene.add(fill);

      group = new THREE.Group();
      scene.add(group);
      const coreColor = host.getAttribute('data-three-color') || '#8b5cf6';
      const core = new THREE.Mesh(
        new THREE.IcosahedronGeometry(1.15, 1),
        new THREE.MeshStandardMaterial({ color: coreColor, metalness: 0.56, roughness: 0.26, transparent: true, opacity: 0.84, wireframe: true })
      );
      group.add(core);
      const shell = new THREE.Mesh(
        new THREE.TorusGeometry(1.62, 0.018, 8, 100),
        new THREE.MeshStandardMaterial({ color: '#67e8f9', metalness: 0.6, roughness: 0.2, transparent: true, opacity: 0.86 })
      );
      shell.rotation.set(0.65, 0.25, 0.3);
      group.add(shell);
      const orbit = new THREE.Mesh(
        new THREE.TorusGeometry(2.02, 0.012, 6, 100),
        new THREE.MeshStandardMaterial({ color: '#c4b5fd', metalness: 0.5, roughness: 0.25, transparent: true, opacity: 0.72 })
      );
      orbit.rotation.set(1.05, -0.5, 0.8);
      group.add(orbit);
      const count = Math.min(80, Math.max(24, Math.floor(width * height / 18000)));
      const positions = new Float32Array(count * 3);
      for (let i = 0; i < count; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 7;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 5;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 4;
      }
      const particleGeometry = new THREE.BufferGeometry();
      particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      const particles = new THREE.Points(particleGeometry, new THREE.PointsMaterial({ color: '#c4b5fd', size: 0.024, transparent: true, opacity: 0.72 }));
      scene.add(particles);

      const resize = () => {
        if (!renderer || !camera) return;
        const w = Math.max(host.clientWidth, 1);
        const h = Math.max(host.clientHeight, 1);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h, false);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
      };
      resizeObserver = 'ResizeObserver' in window ? new ResizeObserver(resize) : null;
      resizeObserver?.observe(host);
      if (!resizeObserver) window.addEventListener('resize', resize, { passive: true });
      visibilityObserver = 'IntersectionObserver' in window ? new IntersectionObserver(([entry]) => {
        visible = Boolean(entry?.isIntersecting);
        if (visible && !reduceMotion) animate();
        else { cancelAnimationFrame(frame); renderer.render(scene, camera); }
      }, { rootMargin: '120px' }) : null;
      visibilityObserver?.observe(host);

      const animate = () => {
        if (disposed || !renderer || !scene || !camera || !visible) return;
        group.rotation.y += 0.0028;
        group.rotation.x += 0.0009;
        particles.rotation.y -= 0.00045;
        renderer.render(scene, camera);
        frame = requestAnimationFrame(animate);
      };
      renderer.render(scene, camera);
      if (!reduceMotion && (!visibilityObserver || visible)) animate();
    }).catch(() => {
      // CSS fallback keeps the hero polished when WebGL/CDN access is unavailable.
      host.classList.add('three-hero-fallback');
    });
  });
})();
