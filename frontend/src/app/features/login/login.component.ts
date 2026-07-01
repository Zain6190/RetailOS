import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { ApiService } from '../../core/services/api.service';
import { AppComponent } from '../../app.component';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent {
  email = '';
  password = '';
  loading = false;
  errorMessage = '';

  constructor(
    private apiService: ApiService,
    private appComponent: AppComponent,
    private router: Router
  ) {}

  onSubmit() {
    if (!this.email || !this.password) {
      this.errorMessage = 'Please enter both email and password.';
      return;
    }

    this.loading = true;
    this.errorMessage = '';

    this.apiService.login(this.email, this.password).subscribe({
      next: (res) => {
        // Retrieve profile details to check active role
        this.apiService.getProfile().subscribe({
          next: (profile) => {
            this.loading = false;
            this.appComponent.checkLoginStatus();
            this.router.navigate(['/']);
          },
          error: (err) => {
            this.loading = false;
            this.errorMessage = 'Failed to fetch user profile details.';
          }
        });
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err.error?.detail || 'Incorrect email or password.';
      }
    });
  }

  autoFill(role: string) {
    if (role === 'admin') {
      this.email = 'admin@smartstore.ai';
      this.password = 'Admin123!';
    } else {
      this.email = 'staff@smartstore.ai';
      this.password = 'Staff123!';
    }
  }
}
