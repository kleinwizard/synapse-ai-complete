import React, { Component, ErrorInfo, ReactNode } from 'react';
import { logger, EventType } from '../lib/logger';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorId: string | null;
}

export class ErrorBoundary extends Component<Props, State> {
  private errorCount = 0;

  constructor(props: Props) {
    super(props);

    this.state = {
      hasError: false,
      error: null,
      errorId: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    return {
      hasError: true,
      error,
      errorId,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.errorCount++;
    const errorId = this.state.errorId || `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Get additional context
    const errorContext = {
      error_id: errorId,
      error_message: error.message,
      error_name: error.name,
      error_stack: error.stack,
      component_stack: errorInfo.componentStack,
      error_boundary_count: this.errorCount,
      url: window.location.href,
      user_agent: navigator.userAgent,
      timestamp: new Date().toISOString(),
      
      // React-specific info
      react_version: React.version,
      component_stack_formatted: this.formatComponentStack(errorInfo.componentStack),
      
      // Performance info
      memory_usage: this.getMemoryUsage(),
      
      // User context
      has_auth_token: !!localStorage.getItem('token'),
      user_id: localStorage.getItem('userId'),
    };

    // Log the error with comprehensive details
    logger.error(`React component error caught by ErrorBoundary`, EventType.COMPONENT_ERROR, errorContext);

    // Log additional context about the error
    if (error.cause) {
      logger.error(`Error cause: ${error.cause}`, EventType.COMPONENT_ERROR, {
        error_id: errorId,
        cause: error.cause,
      });
    }

    // Check for error patterns that might indicate specific issues
    this.analyzeErrorPatterns(error, errorContext);

    // Call custom error handler if provided
    if (this.props.onError) {
      try {
        this.props.onError(error, errorInfo);
      } catch (handlerError) {
        logger.error('Error in custom error handler', EventType.COMPONENT_ERROR, {
          original_error_id: errorId,
          handler_error: handlerError instanceof Error ? handlerError.message : String(handlerError),
        });
      }
    }

    // Log recovery attempts
    logger.info('ErrorBoundary activated - displaying fallback UI', EventType.COMPONENT_ERROR, {
      error_id: errorId,
      fallback_provided: !!this.props.fallback,
    });
  }

  private formatComponentStack(componentStack: string): string[] {
    return componentStack
      .split('\n')
      .filter(line => line.trim())
      .map(line => line.trim());
  }

  private getMemoryUsage(): any {
    if ('memory' in performance) {
      return {
        used_js_heap_size: (performance as any).memory.usedJSHeapSize,
        total_js_heap_size: (performance as any).memory.totalJSHeapSize,
        js_heap_size_limit: (performance as any).memory.jsHeapSizeLimit,
      };
    }
    return null;
  }

  private analyzeErrorPatterns(error: Error, context: any) {
    const errorMessage = error.message.toLowerCase();
    const errorStack = error.stack?.toLowerCase() || '';

    // Network-related errors
    if (errorMessage.includes('network') || errorMessage.includes('fetch') || errorMessage.includes('cors')) {
      logger.warn('Network-related error detected in React component', EventType.NETWORK_ERROR, {
        ...context,
        error_category: 'network',
        possible_causes: ['API server down', 'Network connectivity', 'CORS configuration'],
      });
    }

    // Chunk loading errors (common with code splitting)
    if (errorMessage.includes('loading chunk') || errorMessage.includes('loading css chunk')) {
      logger.warn('Chunk loading error detected', EventType.COMPONENT_ERROR, {
        ...context,
        error_category: 'chunk_loading',
        possible_causes: ['Deployment in progress', 'CDN issues', 'Browser cache'],
        suggested_action: 'refresh_page',
      });
    }

    // Memory-related errors
    if (errorMessage.includes('out of memory') || errorStack.includes('maximum call stack')) {
      logger.error('Memory-related error detected', EventType.MEMORY_WARNING, {
        ...context,
        error_category: 'memory',
        memory_info: this.getMemoryUsage(),
      });
    }

    // Permission/authentication errors
    if (errorMessage.includes('unauthorized') || errorMessage.includes('forbidden')) {
      logger.warn('Authentication/authorization error in component', EventType.COMPONENT_ERROR, {
        ...context,
        error_category: 'auth',
        has_token: !!localStorage.getItem('token'),
      });
    }

    // State management errors
    if (errorStack.includes('usestate') || errorStack.includes('usereducer') || errorStack.includes('setstate')) {
      logger.warn('State management error detected', EventType.COMPONENT_ERROR, {
        ...context,
        error_category: 'state_management',
        possible_causes: ['Invalid state update', 'Component unmounted', 'Race condition'],
      });
    }

    // Render loop errors
    if (this.errorCount > 3) {
      logger.error('Multiple errors in ErrorBoundary - possible render loop', EventType.COMPONENT_ERROR, {
        ...context,
        error_category: 'render_loop',
        error_count: this.errorCount,
        warning: 'Multiple consecutive errors detected',
      });
    }
  }

  componentDidUpdate(prevProps: Props, prevState: State) {
    // If we recovered from an error
    if (prevState.hasError && !this.state.hasError) {
      logger.info('ErrorBoundary recovered from error', EventType.COMPONENT_ERROR, {
        error_id: prevState.errorId,
        recovery_successful: true,
      });
    }
  }

  handleRetry = () => {
    const errorId = this.state.errorId;
    
    logger.info('User initiated error recovery', EventType.USER_ACTION, {
      action: 'error_retry',
      error_id: errorId,
      retry_attempt: true,
    });

    this.setState({
      hasError: false,
      error: null,
      errorId: null,
    });
  };

  handleReload = () => {
    const errorId = this.state.errorId;
    
    logger.info('User initiated page reload', EventType.USER_ACTION, {
      action: 'page_reload',
      error_id: errorId,
      reason: 'error_recovery',
    });

    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
          <div className="sm:mx-auto sm:w-full sm:max-w-md">
            <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
              <div className="text-center">
                <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                  <svg
                    className="h-6 w-6 text-red-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth="2"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                    />
                  </svg>
                </div>
                
                <h2 className="mt-4 text-lg font-medium text-gray-900">
                  Something went wrong
                </h2>
                
                <p className="mt-2 text-sm text-gray-600">
                  We encountered an unexpected error. This has been logged and we're working on a fix.
                </p>

                {process.env.NODE_ENV === 'development' && this.state.error && (
                  <div className="mt-4 p-4 bg-gray-100 rounded-lg text-left">
                    <p className="text-xs font-mono text-gray-800 mb-2">
                      <strong>Error:</strong> {this.state.error.message}
                    </p>
                    {this.state.errorId && (
                      <p className="text-xs font-mono text-gray-600">
                        <strong>ID:</strong> {this.state.errorId}
                      </p>
                    )}
                  </div>
                )}

                <div className="mt-6 space-y-3">
                  <button
                    onClick={this.handleRetry}
                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    Try Again
                  </button>
                  
                  <button
                    onClick={this.handleReload}
                    className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    Reload Page
                  </button>
                </div>

                <p className="mt-4 text-xs text-gray-500">
                  If this problem persists, please contact support.
                </p>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// HOC for wrapping components with error boundary
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode,
  onError?: (error: Error, errorInfo: ErrorInfo) => void
) {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary fallback={fallback} onError={onError}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
}

// Hook for manually reporting errors within components
export function useErrorHandler() {
  return (error: Error, context?: Record<string, any>) => {
    const errorId = `manual_error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    logger.error('Manual error report', EventType.COMPONENT_ERROR, {
      error_id: errorId,
      error_message: error.message,
      error_stack: error.stack,
      context,
      manual_report: true,
      component_name: context?.componentName || 'unknown',
    });
    
    // Also throw to trigger error boundary if needed
    if (context?.rethrow) {
      throw error;
    }
  };
}