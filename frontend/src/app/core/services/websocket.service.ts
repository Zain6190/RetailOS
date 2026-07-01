import { Injectable } from '@angular/core';
import { Subject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class WebsocketService {
  private socket!: WebSocket;
  private messageSubject = new Subject<any>();

  constructor() {
    this.connect();
  }

  private connect(): void {
    try {
      this.socket = new WebSocket('ws://localhost:8000/ws');

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.messageSubject.next(data);
        } catch (e) {
          this.messageSubject.next({ type: 'RawText', message: event.data });
        }
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket connection error:', error);
      };

      this.socket.onclose = () => {
        console.warn('WebSocket connection closed. Retrying in 5 seconds...');
        setTimeout(() => this.connect(), 5000);
      };
    } catch (error) {
      console.error('Failed to establish WebSocket:', error);
      setTimeout(() => this.connect(), 5000);
    }
  }

  getMessages(): Observable<any> {
    return this.messageSubject.asObservable();
  }

  sendMessage(message: string): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(message);
    } else {
      console.error('WebSocket is not open. Cannot send message:', message);
    }
  }
}
