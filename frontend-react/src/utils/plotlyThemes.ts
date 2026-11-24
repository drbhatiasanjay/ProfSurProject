/**
 * Plotly Financial Theme Configuration
 * Ported with 100% fidelity from `helpers.py` (plotly_layout_dark & plotly_layout_light).
 */
import Plotly from 'plotly.js-dist-min';

export interface PlotlyLayoutOptions {
  title?: string;
  height?: number;
  yearRange?: [number, number];
  theme?: 'dark' | 'light';
  showLegend?: boolean;
}

export function getPlotlyThemeLayout(options: PlotlyLayoutOptions = {}): Record<string, any> {
  const {
    title = '',
    height = 400,
    yearRange,
    theme = 'dark',
    showLegend = true,
  } = options;

  const isDark = theme === 'dark';
  const topMargin = title ? 65 : 30;

  if (isDark) {
    const xaxisCfg: Record<string, any> = {
      gridcolor: 'rgba(255, 255, 255, 0.08)',
      zerolinecolor: 'rgba(255, 255, 255, 0.08)',
      tickcolor: '#94A3B8',
      tickfont: { color: '#94A3B8', size: 11, family: 'Inter, system-ui, sans-serif' },
      title: { font: { color: '#F8FAFC', size: 12, family: 'Inter, system-ui, sans-serif' } },
    };
    if (yearRange && yearRange.length === 2) {
      xaxisCfg.range = [yearRange[0], yearRange[1]];
    }

    return {
      title: title
        ? {
            text: title,
            font: { family: 'Plus Jakarta Sans, Inter, sans-serif', size: 15, color: '#F8FAFC' },
            x: 0,
            xanchor: 'left',
            pad: { l: 4 },
          }
        : undefined,
      font: { family: 'Inter, system-ui, sans-serif', size: 12, color: '#F8FAFC' },
      plot_bgcolor: 'rgba(0,0,0,0)',
      paper_bgcolor: 'rgba(0,0,0,0)',
      margin: { l: 45, r: 20, t: topMargin, b: 60 },
      height,
      showlegend: showLegend,
      legend: {
        orientation: 'h',
        yanchor: 'top',
        y: -0.15,
        xanchor: 'center',
        x: 0.5,
        font: { color: '#F8FAFC', size: 11 },
      },
      modebar: {
        orientation: 'h',
        bgcolor: 'rgba(13, 21, 39, 0.85)',
        activecolor: '#6366F1',
        color: '#94A3B8',
      },
      xaxis: xaxisCfg,
      yaxis: {
        gridcolor: 'rgba(255, 255, 255, 0.08)',
        zerolinecolor: 'rgba(255, 255, 255, 0.08)',
        tickcolor: '#94A3B8',
        tickfont: { color: '#94A3B8', size: 11, family: 'Inter, system-ui, sans-serif' },
        title: { font: { color: '#F8FAFC', size: 12, family: 'Inter, system-ui, sans-serif' } },
      },
      hoverlabel: {
        bgcolor: '#141824',
        bordercolor: 'rgba(255, 255, 255, 0.2)',
        font: { family: 'Inter, system-ui, sans-serif', size: 12, color: '#F8FAFC' },
      },
      hovermode: 'x unified',
    };
  } else {
    // Light Mode Layout
    const xaxisCfg: Record<string, any> = {
      gridcolor: 'rgba(226, 232, 240, 0.8)',
      zerolinecolor: 'rgba(226, 232, 240, 0.8)',
      tickcolor: '#64748B',
      tickfont: { color: '#334155', size: 11, family: 'Inter, system-ui, sans-serif' },
      title: { font: { color: '#0F172A', size: 12, family: 'Inter, system-ui, sans-serif' } },
    };
    if (yearRange && yearRange.length === 2) {
      xaxisCfg.range = [yearRange[0], yearRange[1]];
    }

    return {
      title: title
        ? {
            text: title,
            font: { family: 'Plus Jakarta Sans, Inter, sans-serif', size: 15, color: '#0F172A' },
            x: 0,
            xanchor: 'left',
            pad: { l: 4 },
          }
        : undefined,
      font: { family: 'Inter, system-ui, sans-serif', size: 12, color: '#334155' },
      plot_bgcolor: 'rgba(0,0,0,0)',
      paper_bgcolor: 'rgba(0,0,0,0)',
      margin: { l: 45, r: 20, t: topMargin, b: 60 },
      height,
      showlegend: showLegend,
      legend: {
        orientation: 'h',
        yanchor: 'top',
        y: -0.15,
        xanchor: 'center',
        x: 0.5,
        font: { color: '#334155', size: 11 },
      },
      modebar: {
        orientation: 'h',
        bgcolor: 'rgba(255, 255, 255, 0.85)',
        activecolor: '#4F46E5',
        color: '#64748B',
      },
      xaxis: xaxisCfg,
      yaxis: {
        gridcolor: 'rgba(226, 232, 240, 0.8)',
        zerolinecolor: 'rgba(226, 232, 240, 0.8)',
        tickcolor: '#64748B',
        tickfont: { color: '#334155', size: 11, family: 'Inter, system-ui, sans-serif' },
        title: { font: { color: '#0F172A', size: 12, family: 'Inter, system-ui, sans-serif' } },
      },
      hoverlabel: {
        bgcolor: '#FFFFFF',
        bordercolor: 'rgba(0, 0, 0, 0.15)',
        font: { family: 'Inter, system-ui, sans-serif', size: 12, color: '#0F172A' },
      },
      hovermode: 'x unified',
    };
  }
}

/**
 * Standard Plotly configuration object matching PLOTLY_CONFIG from helpers.py.
 * Enables the exact 8 modebar buttons visible in Screenshot 2:
 * Camera, Box Select, Pan, Zoom In, Zoom Out, Autoscale, Reset Axes, Fullscreen.
 */
export const STANDARD_PLOTLY_CONFIG: Partial<Plotly.Config> = {
  responsive: true,
  displaylogo: false,
  modeBarButtonsToRemove: ['lasso2d', 'select2d'],
  toImageButtonOptions: {
    format: 'png',
    filename: 'financial_chart_export',
    height: 700,
    width: 1200,
    scale: 2,
  },
};
