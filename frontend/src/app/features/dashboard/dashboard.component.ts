import { Component, OnInit, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Chart, registerables } from 'chart.js';

import { ApiService } from '../../core/services/api.service';

Chart.register(...registerables);

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatDividerModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit, AfterViewInit {
  @ViewChild('salesChart') salesChartCanvas!: ElementRef<HTMLCanvasElement>;
  chart!: Chart;

  // Financial metrics
  revenue = 0;
  expenses = 0;
  profit = 0;
  margin = 0;
  growth = 0;
  lowStockCount = 0;

  sales: any[] = [];
  agentLogs: string[] = [];
  agentRunning = false;
  loadingMetrics = true;

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.loadMetrics();
    this.loadSales();
  }

  ngAfterViewInit() {
    // Wait for metrics to load to build chart or load with mock defaults
    setTimeout(() => this.buildChart(), 600);
  }

  loadMetrics() {
    this.apiService.getFinancialsForecast().subscribe({
      next: (res) => {
        this.revenue = res.projected_revenue;
        this.expenses = res.projected_expenses;
        this.profit = res.projected_profit;
        this.margin = res.profit_margin;
        this.growth = res.growth_rate;
        this.loadingMetrics = false;
      },
      error: () => {
        this.loadingMetrics = false;
      }
    });

    this.apiService.getLowStock().subscribe({
      next: (res) => {
        this.lowStockCount = res.length;
      }
    });
  }

  loadSales() {
    this.apiService.getSales().subscribe({
      next: (res) => {
        this.sales = res.slice(0, 5); // Take top 5 recent sales
      }
    });
  }

  triggerAgent() {
    this.agentRunning = true;
    this.agentLogs = ['Initializing Autonomous Agent Workflow...', 'Triggering LangGraph execution...'];
    
    this.apiService.triggerReorderAgent().subscribe({
      next: (res) => {
        this.agentRunning = false;
        this.agentLogs = res.logs;
        this.loadMetrics(); // Reload stock count and metrics
      },
      error: () => {
        this.agentRunning = false;
        this.agentLogs = ['ERROR: Failed to establish contact with LangGraph workflow node.'];
      }
    });
  }

  buildChart() {
    if (!this.salesChartCanvas) return;
    
    const ctx = this.salesChartCanvas.nativeElement.getContext('2d');
    if (!ctx) return;

    // Glowing Gradients
    const revenueGradient = ctx.createLinearGradient(0, 0, 0, 300);
    revenueGradient.addColorStop(0, 'rgba(99, 102, 241, 0.4)');
    revenueGradient.addColorStop(1, 'rgba(99, 102, 241, 0.0)');

    const forecastGradient = ctx.createLinearGradient(0, 0, 0, 300);
    forecastGradient.addColorStop(0, 'rgba(6, 182, 212, 0.4)');
    forecastGradient.addColorStop(1, 'rgba(6, 182, 212, 0.0)');

    this.chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: ['June 26', 'June 27', 'June 28', 'June 29', 'June 30', 'July 01', 'July 02 (Proj)', 'July 03 (Proj)'],
        datasets: [
          {
            label: 'Historical Revenue ($)',
            data: [1200, 1450, 1100, 1350, 1600, 1550, null, null],
            borderColor: '#6366f1',
            borderWidth: 3,
            backgroundColor: revenueGradient,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: '#6366f1'
          },
          {
            label: 'AI Demand Forecast ($)',
            data: [null, null, null, null, null, 1550, 1720, 1880],
            borderColor: '#06b6d4',
            borderWidth: 3,
            borderDash: [5, 5],
            backgroundColor: forecastGradient,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: '#06b6d4'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: '#94a3b8',
              font: { family: 'Inter', size: 12 }
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.03)' },
            ticks: { color: '#94a3b8' }
          },
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.03)' },
            ticks: { color: '#94a3b8' }
          }
        }
      }
    });
  }
}
