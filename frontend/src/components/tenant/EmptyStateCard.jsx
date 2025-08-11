import React from 'react';
import { Button } from '../ui/button';

const EmptyStateCard = ({ 
  title, 
  description, 
  icon: IconComponent,
  actionLabel,
  actionUrl,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
  features = [],
  connected = false
}) => {
  const handlePrimaryAction = () => {
    if (onAction) {
      onAction();
    } else if (actionUrl) {
      window.location.href = actionUrl;
    }
  };

  return (
    <div className="text-center py-12 px-6 bg-white rounded-lg border-2 border-dashed border-gray-200">
      {IconComponent && (
        <div className="mx-auto w-16 h-16 mb-6 flex items-center justify-center">
          <IconComponent className="h-12 w-12 text-gray-400" />
        </div>
      )}
      
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        {title}
      </h3>
      
      <p className="text-gray-600 mb-6 max-w-md mx-auto">
        {description}
      </p>

      {features.length > 0 && (
        <div className="mb-6">
          <p className="text-sm font-medium text-gray-700 mb-3">
            {connected ? 'Available features:' : 'Available with current setup:'}
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {features.map((feature, index) => (
              <span
                key={index}
                className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
              >
                {feature}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        {actionLabel && (
          <Button onClick={handlePrimaryAction} size="lg">
            {actionLabel}
          </Button>
        )}
        
        {secondaryActionLabel && onSecondaryAction && (
          <Button 
            variant="outline" 
            onClick={onSecondaryAction}
            size="lg"
          >
            {secondaryActionLabel}
          </Button>
        )}
      </div>

      {!connected && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-xs text-gray-500 mb-2">
            💡 Connect your Shopify store to unlock:
          </p>
          <div className="flex flex-wrap justify-center gap-2 text-xs">
            <span className="text-gray-600">• Automatic order import</span>
            <span className="text-gray-600">• Customer data sync</span>
            <span className="text-gray-600">• Advanced analytics</span>
            <span className="text-gray-600">• Automated workflows</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default EmptyStateCard;