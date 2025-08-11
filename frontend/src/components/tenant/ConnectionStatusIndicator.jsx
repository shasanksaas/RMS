import React from 'react';
import { CheckCircle, XCircle, AlertCircle, Loader } from 'lucide-react';

const ConnectionStatusIndicator = ({ 
  connected = false, 
  status = 'disconnected',
  showLabel = true,
  size = 'sm'
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          icon: CheckCircle,
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          label: 'Connected',
          description: 'Shopify store connected'
        };
      case 'connecting':
        return {
          icon: Loader,
          color: 'text-blue-600',
          bgColor: 'bg-blue-100',
          label: 'Connecting',
          description: 'Connecting to Shopify...',
          animate: true
        };
      case 'error':
        return {
          icon: AlertCircle,
          color: 'text-red-600',
          bgColor: 'bg-red-100',
          label: 'Error',
          description: 'Connection failed'
        };
      case 'disconnected':
      default:
        return {
          icon: XCircle,
          color: 'text-gray-400',
          bgColor: 'bg-gray-100',
          label: 'Not Connected',
          description: 'Shopify store not connected'
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;
  
  const iconSize = size === 'lg' ? 'h-6 w-6' : size === 'md' ? 'h-5 w-5' : 'h-4 w-4';
  const textSize = size === 'lg' ? 'text-base' : size === 'md' ? 'text-sm' : 'text-xs';

  return (
    <div className="flex items-center space-x-2">
      <div className={`p-1 rounded-full ${config.bgColor}`}>
        <Icon 
          className={`${iconSize} ${config.color} ${config.animate ? 'animate-spin' : ''}`}
        />
      </div>
      {showLabel && (
        <div className="flex flex-col">
          <span className={`font-medium ${config.color} ${textSize}`}>
            {config.label}
          </span>
          {size !== 'sm' && (
            <span className="text-xs text-gray-500">{config.description}</span>
          )}
        </div>
      )}
    </div>
  );
};

export default ConnectionStatusIndicator;