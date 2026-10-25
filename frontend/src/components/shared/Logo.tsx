import React from 'react'
import clsx from 'clsx'

export type LogoVariant = 'horizontal' | 'symbol'
export type LogoTheme = 'auto' | 'dark' | 'light' | 'white' | 'monochrome'
export type LogoSize = 'sm' | 'md' | 'lg' | 'xl'

export interface LogoProps extends React.SVGProps<SVGSVGElement> {
  variant?: LogoVariant
  logoTheme?: LogoTheme
  size?: LogoSize
  className?: string
  alt?: string
  showWordmark?: boolean
}

const SIZE_MAP: Record<LogoSize, { height: number; symbolWidth: number; horizontalWidth: number }> = {
  sm: { height: 24, symbolWidth: 24, horizontalWidth: 110 },
  md: { height: 32, symbolWidth: 32, horizontalWidth: 145 },
  lg: { height: 40, symbolWidth: 40, horizontalWidth: 180 },
  xl: { height: 48, symbolWidth: 48, horizontalWidth: 215 },
}

/**
 * Reusable official PATCHORA Logo Component
 * Combines cybersecurity shield, digital circuit traces, angled wrench repair tool,
 * and high-contrast wordmark according to the official brand specifications.
 */
export const Logo: React.FC<LogoProps> = ({
  variant = 'horizontal',
  logoTheme = 'auto',
  size = 'md',
  className,
  alt = 'PATCHORA logo',
  showWordmark,
  ...svgProps
}) => {
  const isHorizontal = variant === 'horizontal' || showWordmark === true
  const sizeConfig = SIZE_MAP[size] || SIZE_MAP.md

  // Unique ID prefix to avoid SVG gradient collisions if multiple logos render
  const idPrefix = React.useId().replace(/:/g, '')

  // Wordmark patch color based on theme
  let patchColorClass = 'fill-slate-900 dark:fill-white'
  if (logoTheme === 'dark') patchColorClass = 'fill-white'
  else if (logoTheme === 'light') patchColorClass = 'fill-[#071A3D]'
  else if (logoTheme === 'white') patchColorClass = 'fill-white'
  else if (logoTheme === 'monochrome') patchColorClass = 'fill-[#071A3D]'

  const oraColorClass =
    logoTheme === 'white'
      ? 'fill-white'
      : logoTheme === 'monochrome'
      ? 'fill-[#071A3D]'
      : `fill-[url(#${idPrefix}-oraGrad)]`

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox={isHorizontal ? '0 0 250 64' : '0 0 64 64'}
      height={sizeConfig.height}
      width={isHorizontal ? sizeConfig.horizontalWidth : sizeConfig.symbolWidth}
      className={clsx('inline-block select-none flex-shrink-0 transition-opacity', className)}
      role="img"
      aria-label={alt}
      {...svgProps}
    >
      <defs>
        {/* Cyan Upper-Left Facet Gradient */}
        <linearGradient id={`${idPrefix}-cyanFacet`} x1="20%" y1="10%" x2="90%" y2="90%">
          <stop offset="0%" stopColor="#00F0FF" />
          <stop offset="45%" stopColor="#00C8F0" />
          <stop offset="100%" stopColor="#0088CC" />
        </linearGradient>

        {/* Deep Navy Lower-Right Facet Gradient */}
        <linearGradient id={`${idPrefix}-navyFacet`} x1="10%" y1="10%" x2="90%" y2="100%">
          <stop offset="0%" stopColor="#071A3D" />
          <stop offset="50%" stopColor="#051433" />
          <stop offset="100%" stopColor="#020B1E" />
        </linearGradient>

        {/* Wordmark ORA Cyan Gradient */}
        <linearGradient id={`${idPrefix}-oraGrad`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#00F0FF" />
          <stop offset="100%" stopColor="#00A3E0" />
        </linearGradient>

        {/* Wrench Subtle Shadow Filter */}
        <filter id={`${idPrefix}-wrenchShadow`} x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="1" dy="2" stdDeviation="1.5" floodColor="#02091A" floodOpacity="0.5" />
        </filter>
      </defs>

      {/* ── 1. Shield Symbol (Circuit Traces + Angled Repair Wrench) ────────── */}
      <g transform="translate(4, 3) scale(0.23)">
        {/* Cyan Upper-Left Facet */}
        <path
          d="M 125,24 
             C 95,30 55,36 32,45 
             C 30,85 32,130 55,168 
             C 74,198 100,222 125,236 
             L 125,24 Z"
          fill={logoTheme === 'monochrome' ? '#071A3D' : logoTheme === 'white' ? '#FFFFFF' : `url(#${idPrefix}-cyanFacet)`}
        />

        {/* Deep Navy Lower-Right Facet */}
        <path
          d="M 125,24 
             C 155,30 195,36 218,45 
             C 220,85 218,130 195,168 
             C 176,198 150,222 125,236 
             L 125,24 Z"
          fill={logoTheme === 'monochrome' ? '#071A3D' : logoTheme === 'white' ? '#FFFFFF' : `url(#${idPrefix}-navyFacet)`}
        />

        {/* Circuit Traces */}
        <g
          stroke={logoTheme === 'white' ? '#000000' : '#FFFFFF'}
          strokeWidth="4.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        >
          <path d="M 72,76 L 96,96" />
          <path d="M 52,112 L 78,112 L 100,132" />
          <path d="M 64,152 L 86,152 L 98,140" />
        </g>

        {/* Circuit Nodes */}
        <circle cx="72" cy="76" r="6.5" fill="#00C8F0" stroke="#FFFFFF" strokeWidth="4" />
        <circle cx="52" cy="112" r="6.5" fill="#00C8F0" stroke="#FFFFFF" strokeWidth="4" />
        <circle cx="64" cy="152" r="6.5" fill="#00C8F0" stroke="#FFFFFF" strokeWidth="4" />

        {/* Wrench Repair Tool (Angled at 45 degrees with handle cutout) */}
        <g
          filter={`url(#${idPrefix}-wrenchShadow)`}
          transform="translate(125, 125) rotate(-45) translate(-125, -125)"
        >
          <path
            d="
              M 112,185 
              C 106,175 106,160 114,150 
              L 115,100 
              C 104,95 98,82 101,68 
              C 103,58 111,50 120,48 
              L 120,70 
              C 120,73 122,75 125,75 
              C 128,75 130,73 130,70 
              L 130,48 
              C 139,50 147,58 149,68 
              C 152,82 146,95 135,100 
              L 136,150 
              C 144,160 144,175 138,185 
              C 131,195 119,195 112,185 Z"
            fill={logoTheme === 'monochrome' ? '#071A3D' : '#FFFFFF'}
          />
          {/* Circular cutout in handle */}
          <circle cx="125" cy="176" r="7" fill={logoTheme === 'monochrome' ? '#FFFFFF' : '#051433'} />
        </g>
      </g>

      {/* ── 2. PATCHORA Wordmark (Rendered for horizontal variant) ─────────── */}
      {isHorizontal && (
        <g transform="translate(70, 43)">
          <text
            fontFamily="system-ui, -apple-system, 'Segoe UI', Roboto, 'Inter', sans-serif"
            fontWeight="900"
            fontSize="30"
            letterSpacing="0.8px"
          >
            <tspan className={patchColorClass}>PATCH</tspan>
            <tspan className={oraColorClass}>ORA</tspan>
          </text>
        </g>
      )}
    </svg>
  )
}

export default Logo
