import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://localhost:8000/api/v1';

  constructor(private http: HttpClient) {}

  // Get auth headers automatically
  private getHeaders(): HttpHeaders {
    let headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });
    const token = localStorage.getItem('access_token');
    if (token) {
      headers = headers.set('Authorization', `Bearer ${token}`);
    }
    return headers;
  }

  // --- Authentication ---
  login(username: string, password: string): Observable<any> {
    const body = new URLSearchParams();
    body.set('username', username);
    body.set('password', password);
    
    const headers = new HttpHeaders({
      'Content-Type': 'application/x-www-form-urlencoded'
    });

    return this.http.post<any>(`${this.baseUrl}/auth/login`, body.toString(), { headers }).pipe(
      tap(res => {
        if (res.access_token) {
          localStorage.setItem('access_token', res.access_token);
        }
      })
    );
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_name');
  }

  getProfile(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/auth/me`, { headers: this.getHeaders() }).pipe(
      tap(res => {
        if (res.role && res.role.name) {
          localStorage.setItem('user_role', res.role.name);
          localStorage.setItem('user_name', res.full_name);
        }
      })
    );
  }

  getRoles(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/auth/roles`, { headers: this.getHeaders() });
  }

  // --- Categories & Products ---
  getCategories(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/inventory/categories`, { headers: this.getHeaders() });
  }

  createCategory(name: string, description?: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/inventory/categories`, { name, description }, { headers: this.getHeaders() });
  }

  getProducts(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/inventory/products`, { headers: this.getHeaders() });
  }

  createProduct(product: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/inventory/products`, product, { headers: this.getHeaders() });
  }

  updateProduct(id: number, product: any): Observable<any> {
    return this.http.put<any>(`${this.baseUrl}/inventory/products/${id}`, product, { headers: this.getHeaders() });
  }

  deleteProduct(id: number): Observable<any> {
    return this.http.delete<any>(`${this.baseUrl}/inventory/products/${id}`, { headers: this.getHeaders() });
  }

  // --- Inventory & AI Scanning ---
  getInventory(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/inventory/inventory`, { headers: this.getHeaders() });
  }

  getLowStock(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/inventory/inventory/low-stock`, { headers: this.getHeaders() });
  }

  updateInventory(id: number, body: any): Observable<any> {
    return this.http.put<any>(`${this.baseUrl}/inventory/inventory/${id}`, body, { headers: this.getHeaders() });
  }

  detectShelfStock(imageData: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/inventory/inventory/detect`, { image_data: imageData }, { headers: this.getHeaders() });
  }

  // --- Customers & Sales Transactions ---
  getCustomers(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/sales/customers`, { headers: this.getHeaders() });
  }

  createCustomer(customer: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/sales/customers`, customer, { headers: this.getHeaders() });
  }

  getSales(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/sales/sales`, { headers: this.getHeaders() });
  }

  processSale(sale: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/sales/sales`, sale, { headers: this.getHeaders() });
  }

  getOrders(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/sales/orders`, { headers: this.getHeaders() });
  }

  updateOrder(id: number, body: any): Observable<any> {
    return this.http.put<any>(`${this.baseUrl}/sales/orders/${id}`, body, { headers: this.getHeaders() });
  }

  // --- Suppliers & Purchase Orders ---
  getSuppliers(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/sales/suppliers`, { headers: this.getHeaders() });
  }

  createSupplier(supplier: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/sales/suppliers`, supplier, { headers: this.getHeaders() });
  }

  getPurchaseOrders(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/sales/purchase-orders`, { headers: this.getHeaders() });
  }

  createPurchaseOrder(po: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/sales/purchase-orders`, po, { headers: this.getHeaders() });
  }

  updatePurchaseOrderStatus(id: number, status: string): Observable<any> {
    return this.http.put<any>(`${this.baseUrl}/sales/purchase-orders/${id}/status?status=${status}`, {}, { headers: this.getHeaders() });
  }

  // --- RAG Chat & AI Operations ---
  chatAssistant(message: string, sessionId: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/agents/chat`, { message, session_id: sessionId }, { headers: this.getHeaders() });
  }

  getRecommendations(customerId?: number): Observable<any> {
    const url = customerId ? `${this.baseUrl}/agents/recommendations?customer_id=${customerId}` : `${this.baseUrl}/agents/recommendations`;
    return this.http.get<any>(url, { headers: this.getHeaders() });
  }

  triggerReorderAgent(): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/agents/reorder/trigger`, {}, { headers: this.getHeaders() });
  }

  evaluatePricing(productId: number): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/agents/pricing/evaluate/${productId}`, {}, { headers: this.getHeaders() });
  }

  // --- Forecasts & Reports ---
  getProductForecast(productId: number, days = 7): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/reports/forecast/demand/${productId}?days=${days}`, { headers: this.getHeaders() });
  }

  getFinancialsForecast(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/reports/forecast/financials`, { headers: this.getHeaders() });
  }

  getReportsHistory(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/reports/history`, { headers: this.getHeaders() });
  }

  exportReportCsvUrl(reportType: string): string {
    const token = localStorage.getItem('access_token');
    return `${this.baseUrl}/reports/export?report_type=${reportType}&format=csv&token=${token || ''}`;
  }
}
