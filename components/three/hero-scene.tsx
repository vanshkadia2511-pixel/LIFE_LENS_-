'use client'

import { Suspense, useMemo, useRef } from 'react'
import { Canvas, useFrame, useLoader } from '@react-three/fiber'
import * as THREE from 'three'

const fresnelVertex = /* glsl */ `
  varying vec3 vNormal;
  varying vec3 vView;
  void main() {
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    vNormal = normalize(normalMatrix * normal);
    vView = normalize(-mv.xyz);
    gl_Position = projectionMatrix * mv;
  }
`

const fresnelFragment = /* glsl */ `
  uniform vec3 uColor;
  uniform float uPower;
  uniform float uIntensity;
  varying vec3 vNormal;
  varying vec3 vView;
  void main() {
    float f = pow(1.0 - abs(dot(normalize(vNormal), normalize(vView))), uPower);
    gl_FragColor = vec4(uColor * f * uIntensity, f * uIntensity);
  }
`

function useFresnel(color: string, power = 2.2, intensity = 1.4) {
  return useMemo(
    () =>
      new THREE.ShaderMaterial({
        uniforms: {
          uColor: { value: new THREE.Color(color) },
          uPower: { value: power },
          uIntensity: { value: intensity },
        },
        vertexShader: fresnelVertex,
        fragmentShader: fresnelFragment,
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        side: THREE.DoubleSide,
      }),
    [color, power, intensity],
  )
}

function useGlowTexture() {
  return useMemo(() => {
    const size = 128
    const canvas = document.createElement('canvas')
    canvas.width = canvas.height = size
    const ctx = canvas.getContext('2d')!
    const g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2)
    g.addColorStop(0, 'rgba(255,255,255,1)')
    g.addColorStop(0.25, 'rgba(255,255,255,0.45)')
    g.addColorStop(1, 'rgba(255,255,255,0)')
    ctx.fillStyle = g
    ctx.fillRect(0, 0, size, size)
    const tex = new THREE.CanvasTexture(canvas)
    tex.colorSpace = THREE.SRGBColorSpace
    return tex
  }, [])
}

const HALF_HEIGHT = 1.55
const NECK = 0.1

function glassRadius(y: number) {
  const t = Math.abs(y) / HALF_HEIGHT
  return NECK + 0.98 * Math.pow(Math.sin((t * Math.PI) / 2), 1.35) - 0.12 * Math.pow(t, 6)
}

function Hourglass() {
  const rim = useFresnel('#6fc3ff', 2.4, 1.6)
  const geometry = useMemo(() => {
    const pts: THREE.Vector2[] = []
    for (let i = 0; i <= 80; i++) {
      const y = -HALF_HEIGHT + (i / 80) * HALF_HEIGHT * 2
      pts.push(new THREE.Vector2(glassRadius(y), y))
    }
    return new THREE.LatheGeometry(pts, 96)
  }, [])

  return (
    <group>
      <mesh geometry={geometry}>
        <meshPhysicalMaterial
          color="#8ccfff"
          transparent
          opacity={0.14}
          roughness={0.05}
          metalness={0.1}
          clearcoat={1}
          side={THREE.DoubleSide}
          depthWrite={false}
        />
      </mesh>
      <mesh geometry={geometry} material={rim} />
      <Cap y={HALF_HEIGHT + 0.06} />
      <Cap y={-HALF_HEIGHT - 0.06} />
    </group>
  )
}

function Cap({ y }: { y: number }) {
  return (
    <group position={[0, y, 0]}>
      <mesh>
        <cylinderGeometry args={[1.08, 1.08, 0.12, 64]} />
        <meshStandardMaterial color="#0d1a44" metalness={0.9} roughness={0.25} />
      </mesh>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.09, 0.018, 12, 120]} />
        <meshBasicMaterial color="#5fd4ff" toneMapped={false} />
      </mesh>
    </group>
  )
}

function Globe() {
  const ref = useRef<THREE.Mesh>(null)
  const texture = useLoader(THREE.TextureLoader, '/textures/earth-night.png')
  texture.colorSpace = THREE.SRGBColorSpace
  const atmosphere = useFresnel('#3aa0ff', 2.8, 2.2)
  useFrame((_, dt) => {
    if (ref.current) ref.current.rotation.y += dt * 0.12
  })
  return (
    <group position={[0, 0.62, 0]}>
      <mesh ref={ref}>
        <sphereGeometry args={[0.72, 64, 64]} />
        <meshStandardMaterial
          map={texture}
          emissiveMap={texture}
          emissive="#ffffff"
          emissiveIntensity={0.85}
          roughness={0.6}
          metalness={0.1}
        />
      </mesh>
      <mesh scale={1.09} material={atmosphere}>
        <sphereGeometry args={[0.72, 48, 48]} />
      </mesh>
    </group>
  )
}

function Sand() {
  const streamRef = useRef<THREE.Points>(null)
  const count = 140
  const { positions, speeds } = useMemo(() => {
    const positions = new Float32Array(count * 3)
    const speeds = new Float32Array(count)
    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 0.05
      positions[i * 3 + 1] = -Math.random() * 1.1
      positions[i * 3 + 2] = (Math.random() - 0.5) * 0.05
      speeds[i] = 0.5 + Math.random() * 0.6
    }
    return { positions, speeds }
  }, [])

  useFrame((_, dt) => {
    const pts = streamRef.current
    if (!pts) return
    const attr = pts.geometry.getAttribute('position') as THREE.BufferAttribute
    for (let i = 0; i < count; i++) {
      let y = attr.getY(i) - speeds[i] * dt
      if (y < -1.1) y = 0
      attr.setY(i, y)
    }
    attr.needsUpdate = true
  })

  const pileGeometry = useMemo(() => {
    const pts: THREE.Vector2[] = []
    for (let i = 0; i <= 30; i++) {
      const t = i / 30
      const r = 0.92 * t
      pts.push(new THREE.Vector2(r, -HALF_HEIGHT + 0.42 * (1 - Math.pow(t, 0.8))))
    }
    pts.push(new THREE.Vector2(0.92, -HALF_HEIGHT))
    return new THREE.LatheGeometry(pts.reverse(), 64)
  }, [])

  return (
    <group>
      <points ref={streamRef}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        </bufferGeometry>
        <pointsMaterial color="#ffc463" size={0.03} transparent opacity={0.95} blending={THREE.AdditiveBlending} depthWrite={false} />
      </points>
      <mesh geometry={pileGeometry}>
        <meshStandardMaterial color="#c9852a" emissive="#ff9d2e" emissiveIntensity={0.9} roughness={0.9} side={THREE.DoubleSide} />
      </mesh>
    </group>
  )
}

function OrbitRing({
  radius,
  tilt,
  speed,
  color,
}: {
  radius: number
  tilt: [number, number, number]
  speed: number
  color: string
}) {
  const ref = useRef<THREE.Group>(null)
  useFrame((_, dt) => {
    if (ref.current) ref.current.rotation.z += dt * speed
  })
  return (
    <group rotation={tilt}>
      <group ref={ref}>
        <mesh>
          <torusGeometry args={[radius, 0.008, 8, 200]} />
          <meshBasicMaterial color={color} transparent opacity={0.85} toneMapped={false} />
        </mesh>
        {[0, 2.1, 4.2].map((a) => (
          <mesh key={a} position={[Math.cos(a) * radius, Math.sin(a) * radius, 0]}>
            <sphereGeometry args={[0.035, 16, 16]} />
            <meshBasicMaterial color="#ffffff" toneMapped={false} />
          </mesh>
        ))}
      </group>
    </group>
  )
}

function Platform() {
  const glow = useGlowTexture()
  return (
    <group position={[0, -HALF_HEIGHT - 0.2, 0]}>
      <mesh>
        <cylinderGeometry args={[1.7, 1.9, 0.18, 96]} />
        <meshStandardMaterial color="#0a1638" metalness={0.85} roughness={0.3} />
      </mesh>
      {[1.75, 1.95, 2.35].map((r, i) => (
        <mesh key={r} rotation={[Math.PI / 2, 0, 0]} position={[0, -0.04 - i * 0.04, 0]}>
          <torusGeometry args={[r, 0.012, 8, 160]} />
          <meshBasicMaterial color={i === 1 ? '#8b5cf6' : '#3fb6ff'} toneMapped={false} />
        </mesh>
      ))}
      <sprite scale={[6, 1.6, 1]} position={[0, 0, 0]}>
        <spriteMaterial map={glow} color="#2f7dff" transparent opacity={0.55} blending={THREE.AdditiveBlending} depthWrite={false} />
      </sprite>
    </group>
  )
}

function Shield() {
  const ref = useRef<THREE.Group>(null)
  const { shield, check } = useMemo(() => {
    const s = new THREE.Shape()
    s.moveTo(0, 0.62)
    s.bezierCurveTo(0.2, 0.5, 0.38, 0.48, 0.5, 0.48)
    s.bezierCurveTo(0.5, 0.05, 0.42, -0.35, 0, -0.62)
    s.bezierCurveTo(-0.42, -0.35, -0.5, 0.05, -0.5, 0.48)
    s.bezierCurveTo(-0.38, 0.48, -0.2, 0.5, 0, 0.62)
    const shield = new THREE.ExtrudeGeometry(s, { depth: 0.12, bevelEnabled: true, bevelThickness: 0.04, bevelSize: 0.03, bevelSegments: 4 })
    shield.center()
    const c = new THREE.Shape()
    c.moveTo(-0.22, 0.02)
    c.lineTo(-0.06, -0.14)
    c.lineTo(0.24, 0.18)
    c.lineTo(0.18, 0.24)
    c.lineTo(-0.06, -0.02)
    c.lineTo(-0.16, 0.08)
    c.closePath()
    const check = new THREE.ExtrudeGeometry(c, { depth: 0.05, bevelEnabled: false })
    check.center()
    return { shield, check }
  }, [])
  const rim = useFresnel('#7fd8ff', 1.6, 1.4)

  useFrame(({ clock }) => {
    if (!ref.current) return
    const t = clock.getElapsedTime()
    ref.current.position.y = -0.75 + Math.sin(t * 1.2) * 0.06
    ref.current.rotation.y = -0.45 + Math.sin(t * 0.6) * 0.15
  })

  return (
    <group ref={ref} position={[1.55, -0.75, 0.9]} scale={0.85}>
      <mesh geometry={shield}>
        <meshPhysicalMaterial color="#1d4fd8" metalness={0.6} roughness={0.15} clearcoat={1} emissive="#0b2a8a" emissiveIntensity={0.6} />
      </mesh>
      <mesh geometry={shield} material={rim} scale={1.02} />
      <mesh geometry={check} position={[0, 0, 0.12]}>
        <meshBasicMaterial color="#e6f6ff" toneMapped={false} />
      </mesh>
    </group>
  )
}

function Particles() {
  const ref = useRef<THREE.Points>(null)
  const positions = useMemo(() => {
    const count = 700
    const arr = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      const r = 2.2 + Math.random() * 4
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      arr[i * 3] = r * Math.sin(phi) * Math.cos(theta)
      arr[i * 3 + 1] = r * Math.cos(phi) * 0.7
      arr[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta) - 1.5
    }
    return arr
  }, [])
  useFrame((_, dt) => {
    if (ref.current) ref.current.rotation.y += dt * 0.02
  })
  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial color="#7fb8ff" size={0.022} transparent opacity={0.8} sizeAttenuation blending={THREE.AdditiveBlending} depthWrite={false} />
    </points>
  )
}

function CoreGlow() {
  const glow = useGlowTexture()
  return (
    <sprite position={[0, 0.5, -0.4]} scale={[4.2, 4.2, 1]}>
      <spriteMaterial map={glow} color="#2b6bff" transparent opacity={0.45} blending={THREE.AdditiveBlending} depthWrite={false} />
    </sprite>
  )
}

function Rig({ children }: { children: React.ReactNode }) {
  const ref = useRef<THREE.Group>(null)
  useFrame(({ pointer, clock }, dt) => {
    const g = ref.current
    if (!g) return
    const t = clock.getElapsedTime()
    g.rotation.y = THREE.MathUtils.damp(g.rotation.y, pointer.x * 0.35, 3, dt)
    g.rotation.x = THREE.MathUtils.damp(g.rotation.x, -pointer.y * 0.15, 3, dt)
    g.position.y = Math.sin(t * 0.8) * 0.05
  })
  return <group ref={ref}>{children}</group>
}

export default function HeroScene() {
  return (
    <Canvas
      dpr={[1, 1.75]}
      camera={{ position: [0, 0.1, 6.2], fov: 42 }}
      gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      aria-hidden="true"
    >
      <ambientLight intensity={0.35} />
      <pointLight position={[3, 3, 4]} intensity={30} color="#7aa8ff" />
      <pointLight position={[-4, -1, 2]} intensity={20} color="#8b5cf6" />
      <directionalLight position={[0, 5, 5]} intensity={0.8} />
      <Suspense fallback={null}>
        <Rig>
          <CoreGlow />
          <Hourglass />
          <Globe />
          <Sand />
          <OrbitRing radius={1.75} tilt={[1.25, 0.2, 0]} speed={0.25} color="#5fc8ff" />
          <OrbitRing radius={2.05} tilt={[1.35, -0.35, 0.3]} speed={-0.18} color="#8b5cf6" />
          <OrbitRing radius={1.45} tilt={[1.1, 0.5, -0.2]} speed={0.35} color="#38bdf8" />
          <Platform />
          <Shield />
        </Rig>
        <Particles />
      </Suspense>
    </Canvas>
  )
}
