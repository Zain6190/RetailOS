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
  selector: 'app-inventory',
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
  templateUrl: './inventory.component.html',
  styleUrls: ['./inventory.component.scss']
})
export class InventoryComponent implements OnInit {
  inventory: any[] = [];
  filteredInventory: any[] = [];
  categories: any[] = [];
  
  searchQuery = '';
  statusFilter = 'all';
  loading = true;

  // New Category form
  newCategoryName = '';
  newCategoryDesc = '';

  // New Product form
  newProdName = '';
  newProdSku = '';
  newProdBarcode = '';
  newProdCategoryId: number | null = null;
  newProdPrice: number | null = null;
  newProdCost: number | null = null;
  
  // Modals visibility toggles
  isAddProductOpen = false;
  isAddCategoryOpen = false;
  isEditStockOpen = false;
  isScanModalOpen = false;

  // Edit stock state
  selectedStockItem: any = null;
  editQuantity = 0;
  editLocation = '';
  editReorderLevel = 15;

  // Scan state
  scanFile: File | null = null;
  scanPreviewUrl: string | null = null;
  scanning = false;
  scanResults: any = null;

  // Pricing Agent Modal state
  isPricingModalOpen = false;
  pricingResults: any = null;
  pricingLoading = false;

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.loadData();
  }

  loadData() {
    this.loading = true;
    this.apiService.getInventory().subscribe({
      next: (invRes) => {
        this.inventory = invRes;
        this.applyFilters();
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });

    this.apiService.getCategories().subscribe({
      next: (res) => {
        this.categories = res;
      }
    });
  }

  applyFilters() {
    this.filteredInventory = this.inventory.filter(item => {
      const prodName = item.product?.name?.toLowerCase() || '';
      const sku = item.product?.sku?.toLowerCase() || '';
      const barcode = item.product?.barcode?.toLowerCase() || '';
      const matchesSearch = prodName.includes(this.searchQuery.toLowerCase()) || 
                            sku.includes(this.searchQuery.toLowerCase()) ||
                            barcode.includes(this.searchQuery.toLowerCase());
      
      const matchesStatus = this.statusFilter === 'all' || 
                            item.status.toLowerCase() === this.statusFilter.toLowerCase();
      
      return matchesSearch && matchesStatus;
    });
  }

  // --- Add Category ---
  submitCategory() {
    if (!this.newCategoryName) return;
    this.apiService.createCategory(this.newCategoryName, this.newCategoryDesc).subscribe({
      next: (res) => {
        this.categories.push(res);
        this.newCategoryName = '';
        this.newCategoryDesc = '';
        this.isAddCategoryOpen = false;
        alert('Category added successfully!');
      }
    });
  }

  // --- Add Product ---
  submitProduct() {
    if (!this.newProdName || !this.newProdSku || !this.newProdCategoryId || !this.newProdPrice || !this.newProdCost) {
      alert('Please fill out all required fields.');
      return;
    }

    const payload = {
      name: this.newProdName,
      sku: this.newProdSku,
      barcode: this.newProdBarcode,
      category_id: this.newProdCategoryId,
      price: this.newProdPrice,
      cost: this.newProdCost
    };

    this.apiService.createProduct(payload).subscribe({
      next: () => {
        this.loadData();
        this.resetProductForm();
        this.isAddProductOpen = false;
        alert('Product created and inventory initialized successfully.');
      },
      error: (err) => {
        alert(err.error?.detail || 'Failed to create product.');
      }
    });
  }

  resetProductForm() {
    this.newProdName = '';
    this.newProdSku = '';
    this.newProdBarcode = '';
    this.newProdCategoryId = null;
    this.newProdPrice = null;
    this.newProdCost = null;
  }

  // --- Edit Stock ---
  openEditStock(item: any) {
    this.selectedStockItem = item;
    this.editQuantity = item.quantity;
    this.editLocation = item.location || '';
    this.editReorderLevel = item.reorder_level;
    this.isEditStockOpen = true;
  }

  submitStockUpdate() {
    if (!this.selectedStockItem) return;
    
    const payload = {
      quantity: this.editQuantity,
      location: this.editLocation,
      reorder_level: this.editReorderLevel
    };

    this.apiService.updateInventory(this.selectedStockItem.id, payload).subscribe({
      next: () => {
        this.loadData();
        this.isEditStockOpen = false;
        this.selectedStockItem = null;
      }
    });
  }

  // --- AI Shelf Stock Scanning ---
  onScanFileSelected(event: any) {
    const file: File = event.target.files[0];
    if (file) {
      this.scanFile = file;
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.scanPreviewUrl = e.target.result;
      };
      reader.readAsDataURL(file);
    }
  }

  runShelfScan() {
    if (!this.scanPreviewUrl) return;
    
    this.scanning = true;
    this.scanResults = null;

    this.apiService.detectShelfStock(this.scanPreviewUrl).subscribe({
      next: (res) => {
        this.scanning = false;
        this.scanResults = res;
        this.loadData(); // Reload stock updates
      },
      error: () => {
        this.scanning = false;
        alert('Failed to process AI shelf scan.');
      }
    });
  }

  closeScanModal() {
    this.isScanModalOpen = false;
    this.scanFile = null;
    this.scanPreviewUrl = null;
    this.scanResults = null;
  }

  // --- Dynamic Pricing Engine Trigger ---
  optimizePrice(item: any) {
    this.pricingLoading = true;
    this.pricingResults = null;
    this.isPricingModalOpen = true;
    
    this.apiService.evaluatePricing(item.product.id).subscribe({
      next: (res) => {
        this.pricingLoading = false;
        this.pricingResults = res;
        this.loadData(); // Refresh price adjustments
      },
      error: () => {
        this.pricingLoading = false;
        alert('Failed to evaluate dynamic pricing.');
        this.isPricingModalOpen = false;
      }
    });
  }
}
