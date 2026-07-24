import { Component, OnInit, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
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
    FormsModule,
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

  // Active Role
  userRole = '';

  // Financial metrics (Manager only)
  revenue = 0;
  expenses = 0;
  profit = 0;
  margin = 0;
  growth = 0;
  lowStockCount = 0;

  // Animated backing fields for KPI numbers rolling counters
  animatedRevenue = 0;
  animatedExpenses = 0;
  animatedProfit = 0;
  animatedMargin = 0;
  animatedGrowth = 0;
  animatedLowStockCount = 0;
  animatedMySalesTotal = 0;
  animatedMySalesCount = 0;
  animatedTasksCount = 0;

  sales: any[] = [];
  agentLogs: string[] = [];
  agentRunning = false;
  loadingMetrics = true;

  // Staff Management (Manager only)
  staffMembers: any[] = [];
  loadingStaff = false;

  // Staff Portal metrics (Staff only)
  tasks: any[] = [];
  loadingTasks = false;
  
  // Stock Lookup (Staff only)
  stockProducts: any[] = [];
  filteredProducts: any[] = [];
  searchQuery = '';
  loadingStock = false;

  // Staff stats today
  mySalesCount = 0;
  mySalesTotal = 0;

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.userRole = localStorage.getItem('user_role') || 'Admin';
    if (this.userRole === 'Administrator') {
      this.loadMetrics();
      this.loadSales();
      this.loadStaffOverview();
    } else {
      this.loadStaffDashboardData();
    }
  }

  ngAfterViewInit() {
    // Only build chart if Administrator
    if (this.userRole === 'Administrator') {
      setTimeout(() => this.buildChart(), 600);
    }
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

        // Animate financial values
        this.animateNumber('animatedRevenue', 0, this.revenue, 1200, true);
        this.animateNumber('animatedExpenses', 0, this.expenses, 1200, true);
        this.animateNumber('animatedProfit', 0, this.profit, 1200, true);
        this.animateNumber('animatedMargin', 0, this.margin, 800, false);
        this.animateNumber('animatedGrowth', 0, this.growth, 800, false);
      },
      error: () => {
        this.loadingMetrics = false;
      }
    });

    this.apiService.getLowStock().subscribe({
      next: (res) => {
        this.lowStockCount = res.length;
        this.animateNumber('animatedLowStockCount', 0, this.lowStockCount, 600, false);
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

  loadStaffOverview() {
    this.loadingStaff = true;
    this.apiService.getStaffOverview().subscribe({
      next: (res) => {
        this.staffMembers = res;
        this.loadingStaff = false;
      },
      error: () => {
        this.loadingStaff = false;
      }
    });
  }

  loadStaffDashboardData() {
    this.loadingMetrics = true;
    
    // Load Low Stock count (Staff can lookup stock)
    this.apiService.getLowStock().subscribe({
      next: (res) => {
        this.lowStockCount = res.length;
        this.animateNumber('animatedLowStockCount', 0, this.lowStockCount, 600, false);
      }
    });

    // Load Staff's assigned tasks
    this.loadingTasks = true;
    this.apiService.getMyTasks().subscribe({
      next: (res) => {
        this.tasks = res;
        this.loadingTasks = false;
        this.animateNumber('animatedTasksCount', 0, this.tasks.length, 600, false);
      },
      error: () => {
        this.loadingTasks = false;
      }
    });

    // Load Staff's sales processed today
    this.apiService.getSales().subscribe({
      next: (res) => {
        const todayStr = new Date().toDateString();
        // Since getSales filters by user, this contains only current user's sales.
        // We filter for today's sales
        this.sales = res.filter((s: any) => new Date(s.date_created).toDateString() === todayStr);
        this.mySalesCount = this.sales.length;
        this.mySalesTotal = this.sales.reduce((acc, curr) => acc + curr.total_amount, 0);
        this.loadingMetrics = false;
        
        this.animateNumber('animatedMySalesTotal', 0, this.mySalesTotal, 1200, true);
        this.animateNumber('animatedMySalesCount', 0, this.mySalesCount, 600, false);
      },
      error: () => {
        this.loadingMetrics = false;
      }
    });

    // Load products for quick Stock Lookup
    this.loadingStock = true;
    this.apiService.getProducts().subscribe({
      next: (res) => {
        this.stockProducts = res;
        this.filteredProducts = res;
        this.loadingStock = false;
      },
      error: () => {
        this.loadingStock = false;
      }
    });
  }

  onSearchChange() {
    if (!this.searchQuery) {
      this.filteredProducts = this.stockProducts;
    } else {
      const q = this.searchQuery.toLowerCase();
      this.filteredProducts = this.stockProducts.filter(p => 
        p.name.toLowerCase().includes(q) || 
        p.sku.toLowerCase().includes(q) || 
        (p.barcode && p.barcode.includes(q))
      );
    }
  }

  toggleTaskStatus(task: any) {
    const newStatus = task.status === 'Completed' ? 'Pending' : 'Completed';
    this.apiService.updateTaskStatus(task.id, newStatus).subscribe({
      next: (updatedTask) => {
        task.status = updatedTask.status;
        // Re-load stats
        if (this.userRole === 'Administrator') {
          this.loadStaffOverview();
        } else {
          // Re-update my tasks stats
          this.apiService.getMyTasks().subscribe(res => {
            this.tasks = res;
          });
        }
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

  hexToRgba(hex: string, alpha: number): string {
    hex = hex.replace('#', '').trim();
    if (hex.length === 3) {
      hex = hex.split('').map(char => char + char).join('');
    }
    const r = parseInt(hex.substring(0, 2), 16) || 0;
    const g = parseInt(hex.substring(2, 4), 16) || 0;
    const b = parseInt(hex.substring(4, 6), 16) || 0;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  buildChart() {
    if (!this.salesChartCanvas) return;
    
    const ctx = this.salesChartCanvas.nativeElement.getContext('2d');
    if (!ctx) return;

    const computedStyle = getComputedStyle(document.body);
    const primaryColor = computedStyle.getPropertyValue('--primary-color').trim() || '#D4A657';
    const accentColor2 = computedStyle.getPropertyValue('--accent-color-2').trim() || '#3E6B8A';

    // Glowing Gradients
    const revenueGradient = ctx.createLinearGradient(0, 0, 0, 300);
    revenueGradient.addColorStop(0, this.hexToRgba(primaryColor, 0.4));
    revenueGradient.addColorStop(1, this.hexToRgba(primaryColor, 0.0));

    const forecastGradient = ctx.createLinearGradient(0, 0, 0, 300);
    forecastGradient.addColorStop(0, this.hexToRgba(accentColor2, 0.4));
    forecastGradient.addColorStop(1, this.hexToRgba(accentColor2, 0.0));

    this.chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: ['June 26', 'June 27', 'June 28', 'June 29', 'June 30', 'July 01', 'July 02 (Proj)', 'July 03 (Proj)'],
        datasets: [
          {
            label: 'Historical Revenue ($)',
            data: [1200, 1450, 1100, 1350, 1600, 1550, null, null],
            borderColor: primaryColor,
            borderWidth: 3,
            backgroundColor: revenueGradient,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: primaryColor
          },
          {
            label: 'AI Demand Forecast ($)',
            data: [null, null, null, null, null, 1550, 1720, 1880],
            borderColor: accentColor2,
            borderWidth: 3,
            borderDash: [5, 5],
            backgroundColor: forecastGradient,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: accentColor2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: '#E8ECEF',
              font: { family: 'Space Grotesk', size: 12 }
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.03)' },
            ticks: { color: '#94a3b8', font: { family: 'JetBrains Mono' } }
          },
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.03)' },
            ticks: { color: '#94a3b8', font: { family: 'JetBrains Mono' } }
          }
        }
      }
    });
  }

  animateNumber(prop: string, start: number, end: number, duration: number, isFloat: boolean) {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      (this as any)[prop] = end;
      return;
    }
    const range = end - start;
    if (range === 0) {
      (this as any)[prop] = end;
      return;
    }
    const startTime = performance.now();
    const update = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Cubic ease-out
      const ease = 1 - Math.pow(1 - progress, 3);
      const val = start + range * ease;
      (this as any)[prop] = isFloat ? Math.round(val * 100) / 100 : Math.round(val);
      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        (this as any)[prop] = end;
      }
    };
    requestAnimationFrame(update);
  }
}
