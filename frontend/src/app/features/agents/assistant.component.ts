import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-assistant',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatDividerModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './assistant.component.html',
  styleUrls: ['./assistant.component.scss']
})
export class AssistantComponent implements OnInit {
  messages: Array<{ role: string; message: string; date: Date }> = [
    { role: 'assistant', message: 'Hello! I am the SmartStore AI Copilot. Ask me anything about store manuals, return policies, role permissions, or inventory reorder thresholds.', date: new Date() }
  ];
  
  userMessage = '';
  sessionId = '';
  chatLoading = false;

  // Recommendations state
  recommendedProducts: any[] = [];
  recommendationReasoning = '';
  loadingRecs = true;

  // Preset prompts
  quickPrompts = [
    'What is the store return policy?',
    'What is our supplier reorder policy?',
    'What are the permissions for employees?'
  ];

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.sessionId = 'session_' + new Date().getTime();
    this.loadRecommendations();
  }

  loadRecommendations() {
    this.loadingRecs = true;
    this.apiService.getRecommendations().subscribe({
      next: (res) => {
        this.recommendedProducts = res.recommended_products;
        this.recommendationReasoning = res.reasoning;
        this.loadingRecs = false;
      },
      error: () => {
        this.loadingRecs = false;
      }
    });
  }

  sendMessage() {
    if (!this.userMessage.trim()) return;

    const messageText = this.userMessage;
    this.messages.push({
      role: 'user',
      message: messageText,
      date: new Date()
    });

    this.userMessage = '';
    this.chatLoading = true;

    this.apiService.chatAssistant(messageText, this.sessionId).subscribe({
      next: (res) => {
        this.chatLoading = false;
        this.messages.push({
          role: 'assistant',
          message: res.message,
          date: new Date()
        });
      },
      error: () => {
        this.chatLoading = false;
        this.messages.push({
          role: 'assistant',
          message: 'ERROR: Unable to communicate with store RAG service. Please check your API integrations.',
          date: new Date()
        });
      }
    });
  }

  sendPresetPrompt(prompt: string) {
    this.userMessage = prompt;
    this.sendMessage();
  }
}
