import React from 'react';

const Avatar = ({ children, className = "" }) => {
  return (
    <div className={`relative inline-block ${className}`}>
      <div className="rounded-full bg-gray-100 flex items-center justify-center text-sm font-medium text-gray-600 w-full h-full">
        {children}
      </div>
    </div>
  );
};

const AvatarFallback = ({ children }) => {
  return <>{children}</>;
};

export { Avatar, AvatarFallback };