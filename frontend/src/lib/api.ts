import { logger, EventType } from './logger';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface ApiRequestOptions extends RequestInit {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
}

export const apiRequest = async (endpoint: string, options: ApiRequestOptions = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = localStorage.getItem('token');
  const startTime = performance.now();
  const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  // Extract custom options
  const { timeout = 30000, retries = 0, retryDelay = 1000, ...fetchOptions } = options;
  
  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
    'X-Request-ID': requestId,
  };
  
  if (token) {
    defaultHeaders.Authorization = `Bearer ${token}`;
  }
  
  const config: RequestInit = {
    ...fetchOptions,
    headers: {
      ...defaultHeaders,
      ...fetchOptions.headers,
    },
  };
  
  // Sanitize request data for logging (remove sensitive information)
  const sanitizeRequestData = (data: any) => {
    if (!data) return data;
    
    const sanitized = JSON.parse(JSON.stringify(data));
    const sensitiveFields = ['password', 'current_password', 'new_password', 'api_key', 'token'];
    
    const removeSensitiveData = (obj: any) => {
      if (typeof obj !== 'object' || obj === null) return obj;
      
      for (const key in obj) {
        if (sensitiveFields.some(field => key.toLowerCase().includes(field))) {
          obj[key] = '[REDACTED]';
        } else if (typeof obj[key] === 'object') {
          removeSensitiveData(obj[key]);
        }
      }
      return obj;
    };
    
    return removeSensitiveData(sanitized);
  };
  
  // Parse request body for logging
  let requestData = null;
  if (config.body) {
    try {
      if (typeof config.body === 'string') {
        requestData = JSON.parse(config.body);
      } else {
        requestData = config.body;
      }
      requestData = sanitizeRequestData(requestData);
    } catch (e) {
      requestData = { body_type: typeof config.body, body_length: config.body.toString().length };
    }
  }
  
  const method = (config.method || 'GET').toUpperCase();
  
  logger.info(`API call started: ${method} ${endpoint}`, EventType.API_CALL_START, {
    endpoint,
    method,
    request_id: requestId,
    request_data: requestData,
    has_auth_token: !!token,
    timeout,
    retries,
    url,
  });
  
  const makeRequest = async (attemptNumber: number = 0): Promise<any> => {
    try {
      // Create abort controller for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);
      
      const requestConfig = {
        ...config,
        signal: controller.signal,
      };
      
      logger.debug(`Making request attempt ${attemptNumber + 1}`, EventType.API_CALL_START, {
        endpoint,
        method,
        request_id: requestId,
        attempt: attemptNumber + 1,
        max_attempts: retries + 1,
      });
      
      const response = await fetch(url, requestConfig);
      clearTimeout(timeoutId);
      
      const executionTime = performance.now() - startTime;
      
      // Get response headers for logging
      const responseHeaders: Record<string, string> = {};
      response.headers.forEach((value, key) => {
        responseHeaders[key] = value;
      });
      
      let responseData = null;
      let responseText = '';
      
      try {
        responseText = await response.text();
        if (responseText) {
          responseData = JSON.parse(responseText);
        }
      } catch (e) {
        responseData = { raw_response: responseText.substring(0, 1000) };
      }
      
      if (!response.ok) {
        const errorMessage = responseData?.detail || `HTTP ${response.status}: ${response.statusText}`;
        
        logger.error(`API call failed: ${method} ${endpoint}`, EventType.API_CALL_ERROR, {
          endpoint,
          method,
          request_id: requestId,
          status_code: response.status,
          status_text: response.statusText,
          response_data: responseData,
          response_headers: responseHeaders,
          execution_time_ms: executionTime,
          attempt: attemptNumber + 1,
          error: errorMessage,
          url,
        });
        
        // Check if we should retry
        if (attemptNumber < retries && (response.status >= 500 || response.status === 429)) {
          logger.warn(`Retrying API call in ${retryDelay}ms`, EventType.API_CALL_START, {
            endpoint,
            method,
            request_id: requestId,
            attempt: attemptNumber + 1,
            next_attempt_in_ms: retryDelay,
            reason: `HTTP ${response.status}`,
          });
          
          await new Promise(resolve => setTimeout(resolve, retryDelay));
          return makeRequest(attemptNumber + 1);
        }
        
        const error = new Error(errorMessage);
        (error as any).status = response.status;
        (error as any).response = responseData;
        throw error;
      }
      
      logger.info(`API call successful: ${method} ${endpoint}`, EventType.API_CALL_SUCCESS, {
        endpoint,
        method,
        request_id: requestId,
        status_code: response.status,
        response_data: responseData ? sanitizeRequestData(responseData) : null,
        response_headers: responseHeaders,
        execution_time_ms: executionTime,
        response_size_bytes: responseText.length,
        attempt: attemptNumber + 1,
        url,
      });
      
      // Log slow API calls
      if (executionTime > 5000) { // More than 5 seconds
        logger.warn(`Slow API call detected: ${executionTime.toFixed(2)}ms`, EventType.SLOW_OPERATION, {
          endpoint,
          method,
          request_id: requestId,
          execution_time_ms: executionTime,
          threshold_ms: 5000,
        });
      }
      
      return responseData;
      
    } catch (error) {
      const executionTime = performance.now() - startTime;
      
      // Handle timeout
      if (error instanceof Error && error.name === 'AbortError') {
        logger.error(`API call timeout: ${method} ${endpoint}`, EventType.API_CALL_TIMEOUT, {
          endpoint,
          method,
          request_id: requestId,
          timeout_ms: timeout,
          execution_time_ms: executionTime,
          attempt: attemptNumber + 1,
          url,
        });
        
        const timeoutError = new Error(`Request timeout after ${timeout}ms`);
        (timeoutError as any).code = 'TIMEOUT';
        throw timeoutError;
      }
      
      // Handle network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        logger.error(`Network error: ${method} ${endpoint}`, EventType.NETWORK_ERROR, {
          endpoint,
          method,
          request_id: requestId,
          error: error.message,
          execution_time_ms: executionTime,
          attempt: attemptNumber + 1,
          url,
        });
        
        // Retry on network errors
        if (attemptNumber < retries) {
          logger.info(`Retrying after network error in ${retryDelay}ms`, EventType.API_CALL_START, {
            endpoint,
            method,
            request_id: requestId,
            attempt: attemptNumber + 1,
            retry_reason: 'network_error',
          });
          
          await new Promise(resolve => setTimeout(resolve, retryDelay));
          return makeRequest(attemptNumber + 1);
        }
      }
      
      logger.error(`API call error: ${method} ${endpoint}`, EventType.API_CALL_ERROR, {
        endpoint,
        method,
        request_id: requestId,
        error: error instanceof Error ? error.message : String(error),
        error_type: error instanceof Error ? error.constructor.name : typeof error,
        stack_trace: error instanceof Error ? error.stack : undefined,
        execution_time_ms: executionTime,
        attempt: attemptNumber + 1,
        url,
      });
      
      throw error;
    }
  };
  
  return makeRequest();
};

// Enhanced API functions with specific logging
export const authRequest = async (endpoint: string, credentials: any) => {
  logger.info(`Authentication request: ${endpoint}`, EventType.USER_LOGIN, {
    endpoint,
    has_email: !!credentials.email,
    has_password: !!credentials.password,
  });
  
  return apiRequest(endpoint, {
    method: 'POST',
    body: JSON.stringify(credentials),
    timeout: 10000, // Shorter timeout for auth
    retries: 1,
  });
};

export const optimizeRequest = async (data: any) => {
  logger.info('Starting prompt optimization', EventType.API_CALL_START, {
    prompt_length: data.prompt?.length || 0,
    has_parameters: !!data.parameters,
    domain_knowledge: !!data.domain_knowledge,
    role: data.role,
    tone: data.tone,
  });
  
  return apiRequest('/optimize', {
    method: 'POST',
    body: JSON.stringify(data),
    timeout: 60000, // Longer timeout for optimize
    retries: 2,
  });
};

export const executeRequest = async (data: any) => {
  logger.info('Starting prompt execution', EventType.API_CALL_START, {
    task_id: data.task_id,
    action: data.action,
    power_level: data.power_level,
    task_type: data.task_type,
    prompt_length: data.prompt?.length || 0,
  });
  
  return apiRequest('/execute', {
    method: 'POST',
    body: JSON.stringify(data),
    timeout: 120000, // Very long timeout for execute
    retries: 1,
  });
};
