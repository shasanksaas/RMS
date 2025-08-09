import React from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      isOffline: false
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
    
    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Error caught by boundary:', error, errorInfo);
    }
  }

  componentDidMount() {
    // Listen for online/offline events
    window.addEventListener('online', this.handleOnline);
    window.addEventListener('offline', this.handleOffline);
  }

  componentWillUnmount() {
    window.removeEventListener('online', this.handleOnline);
    window.removeEventListener('offline', this.handleOffline);
  }

  handleOnline = () => {
    this.setState({ isOffline: false });
  };

  handleOffline = () => {
    this.setState({ isOffline: true });
  };

  handleRefresh = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  getFriendlyErrorMessage = (error) => {
    if (!error) return "Something went wrong";
    
    const message = error.message || error.toString();
    
    // Network errors
    if (message.includes('Network Error') || message.includes('fetch')) {
      return "Unable to connect to our servers. Please check your internet connection and try again.";
    }
    
    // Permission errors  
    if (message.includes('403') || message.includes('Forbidden')) {
      return "You don't have permission to access this resource. Please contact support if you think this is an error.";
    }
    
    // Not found errors
    if (message.includes('404') || message.includes('Not Found')) {
      return "The requested resource was not found. It may have been moved or deleted.";
    }
    
    // Server errors
    if (message.includes('500') || message.includes('Internal Server Error')) {
      return "Our servers are experiencing issues. Please try again in a few moments.";
    }
    
    // Invalid input errors
    if (message.includes('400') || message.includes('Bad Request')) {
      return "There was an issue with your request. Please check your input and try again.";
    }
    
    // Generic error
    return "An unexpected error occurred. Please try refreshing the page.";
  };

  render() {
    if (this.state.hasError) {
      const friendlyMessage = this.getFriendlyErrorMessage(this.state.error);
      
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <Card className="max-w-md mx-auto">
            <CardHeader className="text-center">
              <div className="flex justify-center mb-4">
                <AlertTriangle className="h-12 w-12 text-red-500" />
              </div>
              <CardTitle className="text-xl text-gray-900">Oops! Something went wrong</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-gray-600 text-center">
                {friendlyMessage}
              </p>
              
              {this.state.isOffline && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <p className="text-yellow-800 text-sm text-center">
                    You appear to be offline. Some features may not work correctly.
                  </p>
                </div>
              )}
              
              <div className="flex flex-col space-y-2">
                <Button 
                  onClick={this.handleRefresh}
                  className="flex items-center justify-center space-x-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  <span>Try Again</span>
                </Button>
                <Button 
                  variant="outline"
                  onClick={this.handleGoHome}
                  className="flex items-center justify-center space-x-2"
                >
                  <Home className="h-4 w-4" />
                  <span>Go Home</span>
                </Button>
              </div>
              
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-4">
                  <summary className="cursor-pointer text-sm text-gray-500">Technical Details</summary>
                  <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto">
                    {this.state.error.toString()}
                    {this.state.errorInfo.componentStack}
                  </pre>
                </details>
              )}
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;