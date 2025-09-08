import React, { useRef, useEffect } from 'react';

export const NeuralBackground = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let animationId;
    let nodes = [];
    let connections = [];

    // Initialize canvas size
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    // Create neural nodes
    const createNodes = (count = 30) => {
      nodes = [];
      for (let i = 0; i < count; i++) {
        nodes.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          vx: (Math.random() - 0.5) * 0.5,
          vy: (Math.random() - 0.5) * 0.5,
          size: Math.random() * 3 + 1,
          opacity: Math.random() * 0.5 + 0.3,
          pulsePhase: Math.random() * Math.PI * 2,
          pulseSpeed: Math.random() * 0.02 + 0.01
        });
      }
    };

    // Update connections between nodes
    const updateConnections = () => {
      connections = [];
      const maxDistance = 150;

      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < maxDistance) {
            connections.push({
              from: nodes[i],
              to: nodes[j],
              distance,
              opacity: (1 - distance / maxDistance) * 0.3
            });
          }
        }
      }
    };

    // Animation loop
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Update node positions
      nodes.forEach(node => {
        node.x += node.vx;
        node.y += node.vy;

        // Bounce off edges
        if (node.x < 0 || node.x > canvas.width) node.vx *= -1;
        if (node.y < 0 || node.y > canvas.height) node.vy *= -1;

        // Keep nodes within bounds
        node.x = Math.max(0, Math.min(canvas.width, node.x));
        node.y = Math.max(0, Math.min(canvas.height, node.y));

        // Update pulse
        node.pulsePhase += node.pulseSpeed;
        node.currentOpacity = node.opacity + Math.sin(node.pulsePhase) * 0.2;
      });

      // Update connections
      updateConnections();

      // Draw connections
      connections.forEach(connection => {
        ctx.strokeStyle = `rgba(59, 130, 246, ${connection.opacity})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(connection.from.x, connection.from.y);
        ctx.lineTo(connection.to.x, connection.to.y);
        ctx.stroke();

        // Add flowing effect
        const flowPosition = (Date.now() / 2000) % 1;
        const flowX = connection.from.x + (connection.to.x - connection.from.x) * flowPosition;
        const flowY = connection.from.y + (connection.to.y - connection.from.y) * flowPosition;
        
        ctx.fillStyle = `rgba(59, 130, 246, ${connection.opacity * 0.8})`;
        ctx.beginPath();
        ctx.arc(flowX, flowY, 1, 0, Math.PI * 2);
        ctx.fill();
      });

      // Draw nodes
      nodes.forEach(node => {
        // Outer glow
        const glowSize = node.size * 3;
        const glowGradient = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, glowSize);
        glowGradient.addColorStop(0, `rgba(59, 130, 246, ${node.currentOpacity * 0.3})`);
        glowGradient.addColorStop(1, 'rgba(59, 130, 246, 0)');
        
        ctx.fillStyle = glowGradient;
        ctx.beginPath();
        ctx.arc(node.x, node.y, glowSize, 0, Math.PI * 2);
        ctx.fill();

        // Core node
        ctx.fillStyle = `rgba(59, 130, 246, ${node.currentOpacity})`;
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2);
        ctx.fill();

        // Inner bright spot
        ctx.fillStyle = `rgba(255, 255, 255, ${node.currentOpacity * 0.8})`;
        ctx.beginPath();
        ctx.arc(node.x - node.size * 0.3, node.y - node.size * 0.3, node.size * 0.3, 0, Math.PI * 2);
        ctx.fill();
      });

      // Add scanning line effect
      const scanY = (Math.sin(Date.now() / 3000) + 1) * canvas.height / 2;
      const scanGradient = ctx.createLinearGradient(0, scanY - 50, 0, scanY + 50);
      scanGradient.addColorStop(0, 'rgba(6, 182, 212, 0)');
      scanGradient.addColorStop(0.5, 'rgba(6, 182, 212, 0.1)');
      scanGradient.addColorStop(1, 'rgba(6, 182, 212, 0)');
      
      ctx.fillStyle = scanGradient;
      ctx.fillRect(0, scanY - 50, canvas.width, 100);

      // Add data stream effects
      const streamCount = 5;
      for (let i = 0; i < streamCount; i++) {
        const streamX = (canvas.width / streamCount) * i + ((Date.now() / 1000) % (canvas.width / streamCount));
        const streamOpacity = 0.1 + Math.sin(Date.now() / 1000 + i) * 0.05;
        
        ctx.strokeStyle = `rgba(6, 182, 212, ${streamOpacity})`;
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 10]);
        ctx.beginPath();
        ctx.moveTo(streamX, 0);
        ctx.lineTo(streamX, canvas.height);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      animationId = requestAnimationFrame(animate);
    };

    // Initialize
    resizeCanvas();
    createNodes();
    animate();

    // Handle resize
    const handleResize = () => {
      resizeCanvas();
      createNodes();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none"
      style={{ zIndex: -1 }}
    />
  );
};