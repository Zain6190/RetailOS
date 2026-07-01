import { Routes } from '@angular/router';
import { LoginComponent } from './features/login/login.component';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { InventoryComponent } from './features/inventory/inventory.component';
import { AssistantComponent } from './features/agents/assistant.component';
import { SuppliersComponent } from './features/suppliers/suppliers.component';
import { inject } from '@angular/core';
import { Router } from '@angular/router';

// Inline simple Auth Guard
const authGuard = () => {
  const router = inject(Router);
  const token = localStorage.getItem('access_token');
  if (token) return true;
  router.navigate(['/login']);
  return false;
};

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { 
    path: '', 
    canActivate: [authGuard],
    children: [
      { path: '', component: DashboardComponent },
      { path: 'inventory', component: InventoryComponent },
      { path: 'assistant', component: AssistantComponent },
      { path: 'suppliers', component: SuppliersComponent }
    ]
  },
  { path: '**', redirectTo: '' }
];
