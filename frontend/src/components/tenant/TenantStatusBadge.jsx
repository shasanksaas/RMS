import React from 'react';

const TenantStatusBadge = ({ status, showDescription = false }) => {
  const getStatusConfig = (status) => {
    const configs = {
      'new': {
        label: 'New',
        bgColor: 'bg-blue-100',
        textColor: 'text-blue-800',
        borderColor: 'border-blue-200',
        description: 'Awaiting first merchant signup'
      },
      'claimed': {
        label: 'Claimed',
        bgColor: 'bg-green-100',
        textColor: 'text-green-800',
        borderColor: 'border-green-200',
        description: 'First merchant has signed up'
      },
      'active': {
        label: 'Active',
        bgColor: 'bg-green-100',
        textColor: 'text-green-800',
        borderColor: 'border-green-200',
        description: 'Tenant is active with users'
      },
      'suspended': {
        label: 'Suspended',
        bgColor: 'bg-yellow-100',
        textColor: 'text-yellow-800',
        borderColor: 'border-yellow-200',
        description: 'Temporarily suspended'
      },
      'archived': {
        label: 'Archived',
        bgColor: 'bg-gray-100',
        textColor: 'text-gray-800',
        borderColor: 'border-gray-200',
        description: 'No longer active'
      }
    };

    return configs[status] || {
      label: status,
      bgColor: 'bg-gray-100',
      textColor: 'text-gray-800',
      borderColor: 'border-gray-200',
      description: ''
    };
  };

  const config = getStatusConfig(status);

  return (
    <div className="flex items-center space-x-2">
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.bgColor} ${config.textColor} ${config.borderColor}`}
      >
        {config.label}
      </span>
      {showDescription && (
        <span className="text-xs text-gray-500">{config.description}</span>
      )}
    </div>
  );
};

export default TenantStatusBadge;