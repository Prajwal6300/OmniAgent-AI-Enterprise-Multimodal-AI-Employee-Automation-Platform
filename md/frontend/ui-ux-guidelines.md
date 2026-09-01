# Frontend — Enterprise UI/UX Guidelines & Accessibility

## Status
**Status:** ✅ IMPLEMENTED (WCAG 2.1 AA Compliance & Enterprise Theme Tokens)

---

## 1. Design System Principles

1. **Clarity Over Complexity:** Information-dense enterprise views (financial diffs, SQL outputs, multi-agent traces) must use clean typography, clear visual hierarchy, and monospace formatting for data values.
2. **Transparency & Explainability:** Every autonomous AI response must visually display its contributing agents, latency waterfall, and clickable citation chips.
3. **Safety First:** Destructive or high-risk actions must always trigger high-contrast warning colors (amber/red) and explicit confirmation modals.

---

## 2. Color Tokens & Risk Badging

| Token Name | Hex Value | Usage |
| :--- | :--- | :--- |
| **`--primary`** | `#1E40AF` (Deep Slate Blue) | Navigation, primary buttons, active tabs. |
| **`--background`** | `#0F172A` / `#FFFFFF` | Dark/Light mode base canvas. |
| **`--risk-low`** | `#10B981` (Emerald Green) | Low risk operations, straight-through processing badges. |
| **`--risk-medium`** | `#F59E0B` (Amber Orange) | Medium risk operations, review notices. |
| **`--risk-high`** | `#EF4444` (Crimson Red) | High risk operations, suspended workflow gates. |

---

## 3. Accessibility Standards (WCAG 2.1 AA)

* Full keyboard navigation across all interactive tables, chat inputs, and modals (`Tab`, `Escape`, `Enter`).
* Screen-reader accessible ARIA labels on dynamic streaming regions (`aria-live="polite"`).
* Minimum color contrast ratio $\ge 4.5:1$ across all text elements.
