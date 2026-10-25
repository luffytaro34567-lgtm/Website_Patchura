# PATCHORA — Official Brand & Logo Design Guidelines

**Document Version:** 1.0.0  
**Status:** Approved & Implemented  
**Date:** October 24, 2026  
**Primary Visual Asset:** `frontend/public/patchora-logo-reference.png`  
**Canonical Reusable Component:** `frontend/src/components/shared/Logo.tsx`  

---

## 1. Brand Identity Overview

**Brand Name:** PATCHORA  
**Industry / Category:** AI-Assisted Cybersecurity, Vulnerability Assessment, and Automated Remediation Platform  
**Brand Personality:** Secure, Intelligent, Precise, Modern, Reliable, Developer-Focused  
**Core Design Concept:** The synthesis of three foundational cybersecurity pillars:
1. **The Shield Silhouette:** Communicates trust, proactive defense, and digital infrastructure protection.
2. **The Digital Circuit Traces:** Signifies intelligent vulnerability detection, AST parsing, and automated scanning algorithms.
3. **The Angled Repair Tool (Wrench):** Represents actionable remediation, automated patch generation, and DevSecOps fixing capabilities.

The PATCHORA identity is crafted to deliver a modern, authoritative enterprise cybersecurity presence, strictly distinguished from gaming or cliché hacker aesthetics.

---

## 2. Official Color Palette

| Color Name | Hex Code | RGB | HSL | Primary Application |
| :--- | :--- | :--- | :--- | :--- |
| **Electric Cyan** | `#00C8F0` | `rgb(0, 200, 240)` | `190°, 100%, 47%` | Accent highlights, circuit nodes, `ORA` wordmark, primary focus rings |
| **Deep Navy** | `#071A3D` | `rgb(7, 26, 61)` | `219°, 79%, 13%` | Shield lower facet, light-mode `PATCH` wordmark, high-contrast borders |
| **Midnight Black** | `#05070D` | `rgb(5, 7, 13)` | `225°, 44%, 4%` | Dark application canvas, deep terminal backgrounds |
| **Pure White** | `#FFFFFF` | `rgb(255, 255, 255)` | `0°, 0%, 100%` | Dark-mode `PATCH` wordmark, wrench tool face, circuit lines |
| **Slate Gray** | `#94A3B8` | `rgb(148, 163, 184)` | `215°, 25%, 65%` | Subtle borders, secondary UI indicators, muted labels |

---

## 3. Logo Anatomy & Symbol Geometry

The PATCHORA logo consists of a geometric shield symbol and a bold, uppercase wordmark:

```
        ┌─────────────┐
        │ ╲ Circuit   │
        │   ●─ Traces │   PATCHORA
        │     ╲ Wrench│   [PATCH: White/Navy] [ORA: Cyan]
        │       ╲Tool │
        └─────────────┘
```

1. **The Shield Facets:**
   - **Upper-Left Facet:** Rendered with a linear gradient from Electric Cyan (`#00F0FF`) down to Cyan-Blue (`#0088CC`), symbolizing proactive assessment.
   - **Lower-Right Facet:** Rendered with a deep navy gradient (`#071A3D` to `#020B1E`), providing deep contrast and grounding the mark.
   - **Bevel Highlight:** A subtle 1.5px top highlight line (`#66E5FF` at 40% opacity) accentuates the geometric top arch.
2. **The Circuit Traces:**
   - 3 clean white circuit traces (`#FFFFFF`, stroke width 4.5px, rounded caps and joins) emerge from circular terminal nodes (`#00C8F0` center with white outer rim) on the cyan facet and connect into the central remediation tool.
3. **The Wrench Motif:**
   - Positioned at a precise 45-degree angle pointing towards the upper-right.
   - Solid pure white body (`#FFFFFF`) with a subtle drop shadow (`#02091A` at 50% opacity) providing layered depth across both shield facets.
   - Features a clean circular cutout in the handle base exposing the deep background.
4. **The Wordmark Typography:**
   - Brand name is strictly formatted as **`PATCHORA`** (never hyphenated, spaced, or lowercase).
   - Heavyweight, geometric sans-serif (`font-weight: 900`, `letter-spacing: 0.8px`).
   - In dark mode / dark backgrounds: `PATCH` is Pure White (`#FFFFFF`), `ORA` is Electric Cyan (`#00C8F0`).
   - In light mode / light backgrounds: `PATCH` is Deep Navy (`#071A3D`), `ORA` is Electric Cyan (`#00C8F0`).

---

## 4. Asset Inventory & Canonical Locations

All logo files are maintained in both `frontend/public/` (for static serving and metadata) and `frontend/src/assets/` (for bundler imports):

### A. Scalable Vector Assets (SVG)
- **`patchora-symbol.svg`**: Standalone shield symbol with circuit traces and wrench (viewBox `0 0 250 250`).
- **`patchora-logo-dark.svg`**: Primary horizontal logo for dark backgrounds (White `PATCH`, Cyan `ORA`).
- **`patchora-logo-light.svg`**: Primary horizontal logo for light backgrounds (Navy `PATCH`, Cyan `ORA`).
- **`patchora-logo-white.svg`**: High-contrast monochrome pure white version.
- **`patchora-logo-monochrome.svg`**: High-contrast monochrome deep navy version.
- **`favicon.svg`**: High-visibility 32x32 optimized vector favicon with enhanced line weights for browser tabs.

### B. High-Resolution Raster Assets (PNG)
- **`patchora-logo-reference.png`**: Original 1024×682 transparent master reference asset.
- **`patchora-logo-1200.png`**: 1200×400 high-resolution transparent horizontal banner.
- **`patchora-logo-horizontal.png`**: 763×252 cropped transparent horizontal logo.
- **`patchora-logo-dark.png`**: 763×252 transparent PNG optimized for dark interfaces.
- **`patchora-logo-light.png`**: 763×252 transparent PNG optimized for light interfaces.
- **`patchora-symbol-512.png`**: 512×512 square transparent app icon / PWA splash icon.
- **`patchora-symbol-192.png`**: 192×192 square transparent mobile icon / Apple touch icon.
- **`patchora-symbol-48.png`**: 48×48 square transparent desktop shortcut icon.
- **`patchora-symbol-32.png`**: 32×32 square transparent browser favicon.
- **`patchora-symbol-16.png`**: 16×16 square transparent compact favicon.

### C. Browser Tab Icon (ICO)
- **`favicon.ico`**: Windows and legacy browser multi-resolution icon bundle.

---

## 5. React Component Usage (`<Logo />`)

The application utilizes a single canonical component: [`frontend/src/components/shared/Logo.tsx`](file:///c:/Website_Patchura/frontend/src/components/shared/Logo.tsx).

### Component Properties

```typescript
export interface LogoProps extends React.SVGProps<SVGSVGElement> {
  variant?: 'horizontal' | 'symbol' // 'horizontal' (default) or 'symbol'
  logoTheme?: 'auto' | 'dark' | 'light' | 'white' | 'monochrome' // 'auto' (default)
  size?: 'sm' | 'md' | 'lg' | 'xl' // 'sm' (24px), 'md' (32px), 'lg' (40px), 'xl' (48px)
  className?: string
  alt?: string // Accessible description (default: "PATCHORA logo")
}
```

### Examples

```tsx
// 1. Standard Desktop Navigation Header
<Logo variant="horizontal" size="md" />

// 2. Compact Mobile Header
<Logo variant="symbol" size="sm" />

// 3. Authentication Screen Centerpiece
<Logo variant="symbol" size="xl" />

// 4. Monochrome Inverted Footer
<Logo variant="horizontal" logoTheme="white" size="md" />
```

---

## 6. Clear Space & Size Constraints

1. **Clear Space:** Maintain clear space around the logo equal to at least 10% of the symbol width. Never encroach on this margin with text, buttons, or border lines.
2. **Minimum Sizes:**
   - **Horizontal Wordmark:** Minimum display height of 24 CSS pixels.
   - **Symbol Only:** Minimum display height of 16 CSS pixels (favicon) or 20 CSS pixels (UI icon).
3. **Aspect Ratio:** Always preserve the 1:1 aspect ratio of the shield symbol and the 4:1 aspect ratio of the horizontal mark. Never stretch, squish, or distort the vector geometries.

---

## 7. Prohibited Modifications

- ❌ Never alter the spelling or capitalization (e.g., do not use `Patchora`, `PatchOra`, or `PATCH-ORA`).
- ❌ Never detach or substitute the wrench motif with standard gears, checkmarks, or third-party stock icons.
- ❌ Never invert the color split (the upper-left facet must always remain Electric Cyan).
- ❌ Never apply unapproved drop shadows, intense neon glows, or 3D extrusions.
- ❌ Never embed low-resolution raster screenshots where clean vector SVG components are supported.
