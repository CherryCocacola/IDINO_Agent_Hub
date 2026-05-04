/**
 * Frontend Logging Utility
 * Provides structured logging for the frontend application.
 * Logs are sent to console and can optionally be sent to a backend endpoint.
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  component: string;
  message: string;
  data?: unknown;
  error?: {
    name: string;
    message: string;
    stack?: string;
  };
}

interface LoggerConfig {
  minLevel: LogLevel;
  sendToBackend: boolean;
  backendEndpoint?: string;
  bufferSize: number;
}

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

class FrontendLogger {
  private config: LoggerConfig;
  private buffer: LogEntry[] = [];
  private componentName: string;

  constructor(componentName: string, config?: Partial<LoggerConfig>) {
    this.componentName = componentName;
    this.config = {
      minLevel: (process.env.NEXT_PUBLIC_LOG_LEVEL as LogLevel) || 'info',
      sendToBackend: process.env.NEXT_PUBLIC_SEND_LOGS === 'true',
      backendEndpoint: process.env.NEXT_PUBLIC_LOG_ENDPOINT || '/api/logs',
      bufferSize: 50,
      ...config,
    };
  }

  private shouldLog(level: LogLevel): boolean {
    return LOG_LEVELS[level] >= LOG_LEVELS[this.config.minLevel];
  }

  private formatEntry(level: LogLevel, message: string, data?: unknown, error?: Error): LogEntry {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      component: this.componentName,
      message,
    };

    if (data !== undefined) {
      entry.data = data;
    }

    if (error) {
      entry.error = {
        name: error.name,
        message: error.message,
        stack: error.stack,
      };
    }

    return entry;
  }

  private logToConsole(entry: LogEntry): void {
    const prefix = `[${entry.timestamp}] [${entry.level.toUpperCase()}] [${entry.component}]`;
    const consoleMethod = entry.level === 'error' ? 'error' : entry.level === 'warn' ? 'warn' : 'log';

    if (entry.error) {
      console[consoleMethod](prefix, entry.message, entry.data || '', entry.error);
    } else if (entry.data !== undefined) {
      console[consoleMethod](prefix, entry.message, entry.data);
    } else {
      console[consoleMethod](prefix, entry.message);
    }
  }

  private addToBuffer(entry: LogEntry): void {
    this.buffer.push(entry);

    // Keep buffer at max size
    if (this.buffer.length > this.config.bufferSize) {
      this.buffer.shift();
    }

    // Auto-flush on errors
    if (entry.level === 'error' && this.config.sendToBackend) {
      this.flush();
    }
  }

  private async flush(): Promise<void> {
    if (this.buffer.length === 0 || !this.config.sendToBackend) return;

    const logsToSend = [...this.buffer];
    this.buffer = [];

    try {
      await fetch(this.config.backendEndpoint!, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logs: logsToSend }),
      });
    } catch {
      // Restore buffer on failure (but don't exceed max size)
      this.buffer = [...logsToSend.slice(-this.config.bufferSize / 2), ...this.buffer];
    }
  }

  debug(message: string, data?: unknown): void {
    if (!this.shouldLog('debug')) return;
    const entry = this.formatEntry('debug', message, data);
    this.logToConsole(entry);
    this.addToBuffer(entry);
  }

  info(message: string, data?: unknown): void {
    if (!this.shouldLog('info')) return;
    const entry = this.formatEntry('info', message, data);
    this.logToConsole(entry);
    this.addToBuffer(entry);
  }

  warn(message: string, data?: unknown): void {
    if (!this.shouldLog('warn')) return;
    const entry = this.formatEntry('warn', message, data);
    this.logToConsole(entry);
    this.addToBuffer(entry);
  }

  error(message: string, error?: Error | unknown, data?: unknown): void {
    if (!this.shouldLog('error')) return;
    const err = error instanceof Error ? error : undefined;
    const entry = this.formatEntry('error', message, data, err);
    this.logToConsole(entry);
    this.addToBuffer(entry);
  }

  /**
   * Get recent logs from buffer (useful for debugging)
   */
  getRecentLogs(): LogEntry[] {
    return [...this.buffer];
  }

  /**
   * Create a child logger with a sub-component name
   */
  child(subComponent: string): FrontendLogger {
    return new FrontendLogger(`${this.componentName}:${subComponent}`, this.config);
  }
}

// Singleton loggers for common use cases
const loggers: Map<string, FrontendLogger> = new Map();

/**
 * Get or create a logger for a component
 */
export function getLogger(componentName: string): FrontendLogger {
  if (!loggers.has(componentName)) {
    loggers.set(componentName, new FrontendLogger(componentName));
  }
  return loggers.get(componentName)!;
}

/**
 * Default application logger
 */
export const appLogger = getLogger('App');

/**
 * API logger for tracking API calls
 */
export const apiLogger = getLogger('API');

/**
 * Global error handler for uncaught errors
 */
export function setupGlobalErrorHandling(): void {
  if (typeof window === 'undefined') return;

  const errorLogger = getLogger('GlobalError');

  // Handle uncaught errors
  window.onerror = (message, source, lineno, colno, error) => {
    errorLogger.error(`Uncaught error: ${message}`, error, {
      source,
      lineno,
      colno,
    });
    return false;
  };

  // Handle unhandled promise rejections
  window.onunhandledrejection = (event) => {
    errorLogger.error('Unhandled promise rejection', event.reason);
  };
}

export { FrontendLogger };
export type { LogEntry, LogLevel };
