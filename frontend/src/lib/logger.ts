/**
 * Frontend logging utility for Synapse AI
 * 
 * Provides comprehensive logging for API calls, user actions, errors, and performance metrics
 * to help debug issues throughout the frontend application.
 */

// Log levels
export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
}

// Event types for structured logging
export enum EventType {
  // API Events
  API_CALL_START = 'api_call_start',
  API_CALL_SUCCESS = 'api_call_success',
  API_CALL_ERROR = 'api_call_error',
  API_CALL_TIMEOUT = 'api_call_timeout',
  
  // User Action Events
  USER_LOGIN = 'user_login',
  USER_LOGOUT = 'user_logout',
  USER_REGISTER = 'user_register',
  USER_ACTION = 'user_action',
  FORM_SUBMIT = 'form_submit',
  BUTTON_CLICK = 'button_click',
  NAVIGATION = 'navigation',
  
  // Component Events
  COMPONENT_MOUNT = 'component_mount',
  COMPONENT_UNMOUNT = 'component_unmount',
  COMPONENT_ERROR = 'component_error',
  COMPONENT_RENDER = 'component_render',
  
  // Performance Events
  PERFORMANCE_METRIC = 'performance_metric',
  SLOW_OPERATION = 'slow_operation',
  MEMORY_WARNING = 'memory_warning',
  
  // Error Events
  UNHANDLED_ERROR = 'unhandled_error',
  PROMISE_REJECTION = 'promise_rejection',
  NETWORK_ERROR = 'network_error',
  VALIDATION_ERROR = 'validation_error',
  
  // General Events
  APP_START = 'app_start',
  FEATURE_FLAG = 'feature_flag',
  DEBUG_INFO = 'debug_info',
}

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  event_type: EventType;
  message: string;
  data?: Record<string, any>;
  user_id?: string;
  session_id?: string;
  user_agent?: string;
  url?: string;
  stack_trace?: string;
}

interface APICallData {
  endpoint: string;
  method: string;
  request_data?: any;
  response_data?: any;
  status_code?: number;
  execution_time_ms?: number;
  error?: string;
  request_id?: string;
}

interface UserActionData {
  action: string;
  element?: string;
  page?: string;
  form_data?: Record<string, any>;
  previous_page?: string;
}

interface ComponentEventData {
  component_name: string;
  props?: Record<string, any>;
  state?: Record<string, any>;
  error_message?: string;
  render_time_ms?: number;
}

interface PerformanceData {
  metric_name: string;
  value: number;
  unit: string;
  threshold?: number;
  additional_metrics?: Record<string, number>;
}

class Logger {
  private minLevel: LogLevel;
  private sessionId: string;
  private userId: string | null = null;
  private isEnabled: boolean;
  private logBuffer: LogEntry[] = [];
  private maxBufferSize = 1000;
  private flushInterval = 30000; // 30 seconds
  private remoteLoggingEndpoint: string | null = null;

  constructor() {
    this.minLevel = this.parseLogLevel(import.meta.env.VITE_LOG_LEVEL) || LogLevel.INFO;
    this.isEnabled = import.meta.env.VITE_ENABLE_LOGGING !== 'false';
    this.sessionId = this.generateSessionId();
    this.remoteLoggingEndpoint = import.meta.env.VITE_LOGGING_ENDPOINT;
    
    // Set up periodic flushing
    if (this.isEnabled && this.remoteLoggingEndpoint) {
      setInterval(() => this.flushLogs(), this.flushInterval);
    }
    
    // Set up error handlers
    this.setupGlobalErrorHandlers();
  }

  private parseLogLevel(level: string | undefined): LogLevel | null {
    if (!level) return null;
    
    switch (level.toUpperCase()) {
      case 'DEBUG': return LogLevel.DEBUG;
      case 'INFO': return LogLevel.INFO;
      case 'WARN': return LogLevel.WARN;
      case 'ERROR': return LogLevel.ERROR;
      default: return null;
    }
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private setupGlobalErrorHandlers() {
    if (!this.isEnabled) return;

    // Unhandled errors
    window.addEventListener('error', (event) => {
      this.error('Unhandled error occurred', EventType.UNHANDLED_ERROR, {
        message: event.message,
        filename: event.filename,
        line: event.lineno,
        column: event.colno,
        error: event.error?.toString(),
        stack_trace: event.error?.stack,
      });
    });

    // Unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.error('Unhandled promise rejection', EventType.PROMISE_REJECTION, {
        reason: event.reason?.toString(),
        stack_trace: event.reason?.stack,
      });
    });
  }

  setUserId(userId: string | null) {
    this.userId = userId;
  }

  private createLogEntry(
    level: LogLevel,
    message: string,
    event_type: EventType,
    data?: Record<string, any>
  ): LogEntry {
    return {
      timestamp: new Date().toISOString(),
      level,
      event_type,
      message,
      data,
      user_id: this.userId || undefined,
      session_id: this.sessionId,
      user_agent: navigator.userAgent,
      url: window.location.href,
      stack_trace: data?.stack_trace,
    };
  }

  private log(level: LogLevel, message: string, event_type: EventType, data?: Record<string, any>) {
    if (!this.isEnabled || level < this.minLevel) return;

    const logEntry = this.createLogEntry(level, message, event_type, data);
    
    // Console logging
    const consoleMethod = this.getConsoleMethod(level);
    const formattedMessage = `[${LogLevel[level]}] [${event_type}] ${message}`;
    
    if (data) {
      consoleMethod(formattedMessage, data);
    } else {
      consoleMethod(formattedMessage);
    }

    // Buffer for remote logging
    this.logBuffer.push(logEntry);
    
    // Maintain buffer size
    if (this.logBuffer.length > this.maxBufferSize) {
      this.logBuffer = this.logBuffer.slice(-this.maxBufferSize);
    }

    // Immediate flush for errors
    if (level >= LogLevel.ERROR && this.remoteLoggingEndpoint) {
      this.flushLogs();
    }
  }

  private getConsoleMethod(level: LogLevel): (...args: any[]) => void {
    switch (level) {
      case LogLevel.DEBUG: return console.debug;
      case LogLevel.INFO: return console.info;
      case LogLevel.WARN: return console.warn;
      case LogLevel.ERROR: return console.error;
      default: return console.log;
    }
  }

  private async flushLogs() {
    if (!this.remoteLoggingEndpoint || this.logBuffer.length === 0) return;

    const logsToSend = [...this.logBuffer];
    this.logBuffer = [];

    try {
      await fetch(this.remoteLoggingEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ logs: logsToSend }),
      });
    } catch (error) {
      // Restore logs if sending failed
      this.logBuffer.unshift(...logsToSend);
      console.error('Failed to send logs to remote endpoint:', error);
    }
  }

  // Public logging methods
  debug(message: string, event_type: EventType = EventType.DEBUG_INFO, data?: Record<string, any>) {
    this.log(LogLevel.DEBUG, message, event_type, data);
  }

  info(message: string, event_type: EventType = EventType.DEBUG_INFO, data?: Record<string, any>) {
    this.log(LogLevel.INFO, message, event_type, data);
  }

  warn(message: string, event_type: EventType = EventType.DEBUG_INFO, data?: Record<string, any>) {
    this.log(LogLevel.WARN, message, event_type, data);
  }

  error(message: string, event_type: EventType = EventType.UNHANDLED_ERROR, data?: Record<string, any>) {
    this.log(LogLevel.ERROR, message, event_type, data);
  }

  // Specialized logging methods
  logApiCall(data: APICallData, success: boolean, execution_time: number) {
    const event_type = success ? EventType.API_CALL_SUCCESS : EventType.API_CALL_ERROR;
    const level = success ? LogLevel.INFO : LogLevel.ERROR;
    
    this.log(level, `API ${data.method} ${data.endpoint}`, event_type, {
      ...data,
      execution_time_ms: execution_time,
    });
  }

  logUserAction(action: string, data?: UserActionData) {
    this.info(`User action: ${action}`, EventType.USER_ACTION, {
      action,
      page: window.location.pathname,
      ...data,
    });
  }

  logComponentEvent(component_name: string, event_type: EventType, data?: ComponentEventData) {
    const level = event_type === EventType.COMPONENT_ERROR ? LogLevel.ERROR : LogLevel.DEBUG;
    
    this.log(level, `Component ${event_type}: ${component_name}`, event_type, {
      component_name,
      ...data,
    });
  }

  logPerformance(metric_name: string, value: number, unit: string, data?: PerformanceData) {
    const level = data?.threshold && value > data.threshold ? LogLevel.WARN : LogLevel.INFO;
    const event_type = level === LogLevel.WARN ? EventType.SLOW_OPERATION : EventType.PERFORMANCE_METRIC;
    
    this.log(level, `Performance: ${metric_name} = ${value}${unit}`, event_type, {
      metric_name,
      value,
      unit,
      ...data,
    });
  }

  logFormSubmission(form_name: string, form_data?: Record<string, any>, validation_errors?: string[]) {
    const level = validation_errors && validation_errors.length > 0 ? LogLevel.WARN : LogLevel.INFO;
    const event_type = validation_errors && validation_errors.length > 0 ? 
      EventType.VALIDATION_ERROR : EventType.FORM_SUBMIT;
    
    // Sanitize form data (remove sensitive fields)
    const sanitized_data = form_data ? this.sanitizeFormData(form_data) : undefined;
    
    this.log(level, `Form submission: ${form_name}`, event_type, {
      form_name,
      form_data: sanitized_data,
      validation_errors,
    });
  }

  logNavigation(from_path: string, to_path: string, method: 'push' | 'replace' | 'back' | 'forward' = 'push') {
    this.info(`Navigation: ${from_path} -> ${to_path}`, EventType.NAVIGATION, {
      from_path,
      to_path,
      method,
      user_agent: navigator.userAgent,
    });
  }

  private sanitizeFormData(data: Record<string, any>): Record<string, any> {
    const sensitiveFields = ['password', 'current_password', 'new_password', 'confirm_password', 'api_key', 'token'];
    const sanitized: Record<string, any> = {};
    
    for (const [key, value] of Object.entries(data)) {
      if (sensitiveFields.includes(key.toLowerCase())) {
        sanitized[key] = '[REDACTED]';
      } else if (typeof value === 'string' && value.length > 1000) {
        // Truncate long strings
        sanitized[key] = value.substring(0, 1000) + '... [TRUNCATED]';
      } else {
        sanitized[key] = value;
      }
    }
    
    return sanitized;
  }

  // Utility methods for measuring performance
  startTimer(name: string): () => void {
    const start = performance.now();
    return () => {
      const duration = performance.now() - start;
      this.logPerformance(name, duration, 'ms', {
        metric_name: name,
        value: duration,
        unit: 'ms',
      });
      return duration;
    };
  }

  measureAsync<T>(name: string, promise: Promise<T>): Promise<T> {
    const endTimer = this.startTimer(name);
    
    return promise
      .then((result) => {
        endTimer();
        return result;
      })
      .catch((error) => {
        endTimer();
        this.error(`Async operation failed: ${name}`, EventType.UNHANDLED_ERROR, {
          operation: name,
          error: error.toString(),
          stack_trace: error.stack,
        });
        throw error;
      });
  }

  // Get current log buffer (for debugging)
  getLogBuffer(): LogEntry[] {
    return [...this.logBuffer];
  }

  // Clear log buffer
  clearBuffer() {
    this.logBuffer = [];
  }

  // Force flush logs
  async forceFush() {
    await this.flushLogs();
  }
}

// Create and export singleton instance
export const logger = new Logger();

// Export types for use in components
export type { APICallData, UserActionData, ComponentEventData, PerformanceData };

// React Hook for component logging
import { useEffect, useRef } from 'react';

export function useComponentLogger(componentName: string, props?: Record<string, any>) {
  const mountTime = useRef<number>(Date.now());
  
  useEffect(() => {
    // Log component mount
    logger.logComponentEvent(componentName, EventType.COMPONENT_MOUNT, {
      component_name: componentName,
      props: props ? logger['sanitizeFormData'](props) : undefined,
    });
    
    return () => {
      // Log component unmount and duration
      const mountDuration = Date.now() - mountTime.current;
      logger.logComponentEvent(componentName, EventType.COMPONENT_UNMOUNT, {
        component_name: componentName,
        mount_duration_ms: mountDuration,
      });
    };
  }, [componentName]);
  
  // Return logger methods bound to this component
  return {
    logAction: (action: string, data?: any) => logger.logUserAction(`${componentName}: ${action}`, data),
    logError: (error: Error, context?: any) => logger.logComponentEvent(
      componentName, 
      EventType.COMPONENT_ERROR, 
      {
        component_name: componentName,
        error_message: error.message,
        stack_trace: error.stack,
        context,
      }
    ),
    logRender: (renderTime?: number) => logger.logComponentEvent(
      componentName,
      EventType.COMPONENT_RENDER,
      {
        component_name: componentName,
        render_time_ms: renderTime,
      }
    ),
  };
}