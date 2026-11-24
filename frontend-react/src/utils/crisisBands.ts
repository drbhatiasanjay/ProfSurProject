/**
 * Macroeconomic Crisis Event Bands
 * Ported with 100% fidelity from `helpers.py::event_bands`.
 * Represents:
 * 1. Global Financial Crisis (GFC): 2007.5 - 2009.5
 * 2. Insolvency and Bankruptcy Code (IBC): 2015.5 - 2020.5
 * 3. COVID-19 Shock: 2019.5 - 2021.5
 */

export interface CrisisEvent {
  x0: number;
  x1: number;
  label: string;
  color: string;
}

export const CRISIS_EVENTS: CrisisEvent[] = [
  { x0: 2007.5, x1: 2009.5, label: 'GFC', color: 'rgba(239, 68, 68, 0.08)' },
  { x0: 2015.5, x1: 2020.5, label: 'IBC', color: 'rgba(99, 102, 241, 0.08)' },
  { x0: 2019.5, x1: 2021.5, label: 'COVID', color: 'rgba(249, 115, 22, 0.08)' },
];

/**
 * Generates Plotly layout shape rectangles & text annotations for event bands.
 */
export function getCrisisEventBands(enabled: boolean = true) {
  if (!enabled) return { shapes: [], annotations: [] };

  const shapes = CRISIS_EVENTS.map((event) => ({
    type: 'rect' as const,
    xref: 'x' as const,
    yref: 'paper' as const,
    x0: event.x0,
    x1: event.x1,
    y0: 0,
    y1: 1,
    fillcolor: event.color,
    line: { width: 0 },
  }));

  const annotations = CRISIS_EVENTS.map((event) => ({
    xref: 'x' as const,
    yref: 'paper' as const,
    x: (event.x0 + event.x1) / 2,
    y: 0.98,
    text: event.label,
    showarrow: false,
    font: {
      size: 10,
      color: '#9CA3AF',
      family: 'Inter, system-ui, sans-serif',
    },
    xanchor: 'center' as const,
    yanchor: 'top' as const,
  }));

  return { shapes, annotations };
}
