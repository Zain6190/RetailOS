import { Component, OnInit } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatBadgeModule } from '@angular/material/badge';
import { MatMenuModule } from '@angular/material/menu';

import { ApiService } from './core/services/api.service';
import { WebsocketService } from './core/services/websocket.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatSidenavModule,
    MatToolbarModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatBadgeModule,
    MatMenuModule
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  isSidebarOpen = true;
  isLoggedIn = false;
  isDarkTheme = true;
  userName = '';
  userRole = '';
  
  notifications: Array<{ title: string; message: string; date: Date; read: boolean }> = [
    { title: 'System Initialized', message: 'SmartStore AI is operational.', date: new Date(), read: false }
  ];

  constructor(
    private apiService: ApiService,
    private wsService: WebsocketService,
    private router: Router
  ) {}

  ngOnInit() {
    this.checkLoginStatus();
    
    // Subscribe to real-time notification broadcasts
    this.wsService.getMessages().subscribe(msg => {
      this.handleIncomingNotification(msg);
    });
  }

  checkLoginStatus() {
    const token = localStorage.getItem('access_token');
    if (token) {
      this.isLoggedIn = true;
      this.userName = localStorage.getItem('user_name') || 'Administrator';
      this.userRole = localStorage.getItem('user_role') || 'Admin';
      
      const body = document.body;
      body.classList.remove('theme-manager', 'theme-staff');
      if (this.userRole === 'Administrator') {
        body.classList.add('theme-manager');
      } else {
        body.classList.add('theme-staff');
      }
    } else {
      this.isLoggedIn = false;
      document.body.classList.remove('theme-manager', 'theme-staff');
    }
  }

  handleIncomingNotification(msg: any) {
    let title = 'System Update';
    let message = msg.message || 'Notification received.';

    if (msg.type === 'STOCK_ALERT') {
      title = `Low Stock: ${msg.product_name}`;
      message = `${msg.sku} is down to ${msg.quantity} items (reorder: ${msg.reorder_level}).`;
    } else if (msg.type === 'NEW_SALE') {
      title = `Transaction Processed`;
      message = `Sale #${msg.sale_id} completed: $${msg.amount} via ${msg.payment_method}.`;
    } else if (msg.type === 'AUTONOMOUS_PO_DRAFT') {
      title = `PO Autonomously Drafted`;
      message = `PO #${msg.po_id} to ${msg.supplier} created for $${msg.amount}.`;
    } else if (msg.type === 'PRICE_ADJUSTMENT') {
      title = `Price Dynamic Shift: ${msg.product_name}`;
      message = `Adjusted from $${msg.old_price} to $${msg.new_price}.`;
    } else if (msg.type === 'SHELF_DETECTION') {
      title = `Shelf Scan Success`;
      message = `Detected ${msg.detected_count} units of ${msg.product_name} (${msg.status}).`;
    }

    this.notifications.unshift({
      title,
      message,
      date: new Date(),
      read: false
    });
  }

  get unreadCount(): number {
    return this.notifications.filter(n => !n.read).length;
  }

  markAllAsRead() {
    this.notifications.forEach(n => n.read = true);
  }

  toggleTheme() {
    this.isDarkTheme = !this.isDarkTheme;
    const body = document.body;
    if (this.isDarkTheme) {
      body.classList.remove('light-theme');
      body.classList.add('dark-theme');
    } else {
      body.classList.remove('dark-theme');
      body.classList.add('light-theme');
    }
  }

  logout() {
    this.apiService.logout();
    this.isLoggedIn = false;
    document.body.classList.remove('theme-manager', 'theme-staff');
    this.router.navigate(['/login']);
  }
}
