import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-suppliers',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatSelectModule,
    MatDividerModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './suppliers.component.html',
  styleUrls: ['./suppliers.component.scss']
})
export class SuppliersComponent implements OnInit {
  suppliers: any[] = [];
  purchaseOrders: any[] = [];
  products: any[] = [];
  
  loading = true;

  // New Supplier form
  isAddSupplierOpen = false;
  supName = '';
  supContact = '';
  supEmail = '';
  supPhone = '';
  supAddress = '';
  supRating = 5.0;

  // New PO form
  isAddPoOpen = false;
  selectedSupplierId: number | null = null;
  poItems: Array<{ product_id: number | null; quantity: number; unit_cost: number }> = [];

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.loadData();
  }

  loadData() {
    this.loading = true;
    this.apiService.getSuppliers().subscribe({
      next: (supRes) => {
        this.suppliers = supRes;
      }
    });

    this.apiService.getProducts().subscribe({
      next: (prodRes) => {
        this.products = prodRes;
      }
    });

    this.apiService.getPurchaseOrders().subscribe({
      next: (poRes) => {
        this.purchaseOrders = poRes;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  // --- Add Supplier ---
  submitSupplier() {
    if (!this.supName) return;

    const payload = {
      name: this.supName,
      contact_person: this.supContact,
      email: this.supEmail,
      phone: this.supPhone,
      address: this.supAddress,
      rating: this.supRating
    };

    this.apiService.createSupplier(payload).subscribe({
      next: (res) => {
        this.suppliers.push(res);
        this.resetSupplierForm();
        this.isAddSupplierOpen = false;
        alert('Supplier registered successfully!');
      }
    });
  }

  resetSupplierForm() {
    this.supName = '';
    this.supContact = '';
    this.supEmail = '';
    this.supPhone = '';
    this.supAddress = '';
    this.supRating = 5.0;
  }

  // --- Add PO ---
  openAddPo() {
    this.selectedSupplierId = null;
    this.poItems = [{ product_id: null, quantity: 10, unit_cost: 5.0 }];
    this.isAddPoOpen = true;
  }

  addPoItem() {
    this.poItems.push({ product_id: null, quantity: 10, unit_cost: 5.0 });
  }

  removePoItem(index: number) {
    this.poItems.splice(index, 1);
  }

  onProductSelected(item: any) {
    const prod = this.products.find(p => p.id === item.product_id);
    if (prod) {
      item.unit_cost = prod.cost;
    }
  }

  get poTotalAmount(): number {
    return this.poItems.reduce((acc, item) => acc + (item.quantity * item.unit_cost), 0);
  }

  submitPurchaseOrder() {
    if (!this.selectedSupplierId || this.poItems.length === 0) {
      alert('Please select a supplier and add at least one item.');
      return;
    }

    const payload = {
      supplier_id: this.selectedSupplierId,
      items: this.poItems.map(item => ({
        product_id: item.product_id,
        quantity: item.quantity,
        unit_cost: item.unit_cost
      }))
    };

    this.apiService.createPurchaseOrder(payload).subscribe({
      next: () => {
        this.loadData();
        this.isAddPoOpen = false;
        alert('Purchase Order drafted successfully.');
      },
      error: (err) => {
        alert(err.error?.detail || 'Failed to draft purchase order.');
      }
    });
  }

  // --- Update PO Status ---
  updatePoStatus(poId: number, status: string) {
    this.apiService.updatePurchaseOrderStatus(poId, status).subscribe({
      next: () => {
        this.loadData();
        alert(`Purchase Order status updated to ${status}.`);
      }
    });
  }
}
