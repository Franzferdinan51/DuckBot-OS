import React, { Component, ReactNode } from 'react';
import { Loader, AlertCircle } from 'lucide-react';

interface Props {
  children: ReactNode;
  loading?: ReactNode;
  error?: ReactNode;
  onError?: (error: Error) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  isLoading: boolean;
}

class AsyncErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      isLoading: false
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      isLoading: false
    };
  }

  componentDidCatch(error: Error) {
    this.setState({ error });
    this.props.onError?.(error);
    console.error('AsyncErrorBoundary caught an error:', error);
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      isLoading: false
    });
  };

  setLoading = (loading: boolean) => {
    this.setState({ isLoading: loading });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.error) {
        return this.props.error;
      }

      return (
        <div className="p-6 bg-gray-800 rounded-lg">
          <div className="flex items-center gap-3 text-red-400 mb-4">
            <AlertCircle className="w-5 h-5" />
            <span className="font-medium">Operation Failed</span>
          </div>
          <p className="text-gray-300 text-sm mb-4">
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <button
            onClick={this.handleRetry}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors"
          >
            Try Again
          </button>
        </div>
      );
    }

    if (this.state.isLoading) {
      if (this.props.loading) {
        return this.props.loading;
      }

      return (
        <div className="flex items-center justify-center p-6">
          <Loader className="w-6 h-6 text-blue-400 animate-spin" />
          <span className="ml-2 text-gray-300">Loading...</span>
        </div>
      );
    }

    // Pass setLoading function to children
    return React.Children.map(this.props.children, child => {
      if (React.isValidElement(child)) {
        return React.cloneElement(child, {
          setLoading: this.setLoading
        } as any);
      }
      return child;
    });
  }
}

export default AsyncErrorBoundary;